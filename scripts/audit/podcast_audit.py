#!/usr/bin/env python3
"""lhg-podcast 确定性单集审计：29 条规则，零第三方依赖。

扫描一期播客节目的交付目录（shownotes.md / chapters.json / 封面 /
feed.xml / 音频文件），输出 JSON 与人类可读报告；
有 blocker 时以非零 exit code 退出（供 hooks 与 CI 使用）。

用法：
    python3 podcast_audit.py --target <单集目录> [--format json|text] [--fail-on blocker|warning|nit]

规则文案均为本项目原创（思路受开源播客 skill 的"交付物校验"思想启发，
未复制任何第三方原文；封面尺寸与 RSS 字段依据 Apple 公开技术规范）。
"""

import argparse
import json
import os
import re
import struct
import sys

VERSION = "1.0.0"
TOOL = "lhg-podcast/podcast-audit"

SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build"}
AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac"}
COVER_NAMES = {"cover.png", "cover.jpg", "cover.jpeg", "artwork.png", "artwork.jpg"}

TS_VALID = re.compile(r"^(?:\d{1,2}:)?[0-5]?\d:[0-5]\d$")
TS_LIKE = re.compile(r"\b\d{1,3}:\d{2}(?::\d{2})?\b")


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def ts_to_seconds(ts):
    parts = [int(x) for x in ts.split(":")]
    s = 0
    for p in parts:
        s = s * 60 + p
    return s


def image_size(path):
    """零依赖解析 PNG/JPEG 尺寸，失败返回 None。"""
    try:
        with open(path, "rb") as fh:
            head = fh.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n" and len(head) >= 24:
            w, h = struct.unpack(">II", head[16:24])
            return w, h
        if head[:2] == b"\xff\xd8":
            with open(path, "rb") as fh:
                data = fh.read()
            i = 2
            while i < len(data) - 8:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):  # SOF
                    h, w = struct.unpack(">HH", data[i + 5:i + 9])
                    return w, h
                if marker in (0xD8, 0xD9) or (0xD0 <= marker <= 0xD7) or marker == 0x01:
                    i += 2
                    continue
                ln = struct.unpack(">H", data[i + 2:i + 4])[0]
                i += 2 + ln
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- 规则注册表

RULES = []
_RULE_BY_ID = {}


def rule(rule_id, severity, category, title, detail):
    def deco(fn):
        r = {"id": rule_id, "severity": severity, "category": category,
             "title": title, "detail": detail}
        _RULE_BY_ID[rule_id] = r
        r["check"] = fn
        RULES.append(r)
        return fn
    return deco


def _mk(rule_id, path, line, snippet):
    r = _RULE_BY_ID[rule_id]
    return Finding(r["id"], r["severity"], r["category"], r["title"],
                   path, line, snippet[:160], r["detail"])


def _collect(target):
    """收集单集目录关键文件。ctx 供所有规则共享。"""
    ctx = {"target": target, "shownotes": None, "shownotes_lines": [],
           "chapters": None, "cover": None, "cover_size": None,
           "audio": [], "feed": None, "feed_tree": None}
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            p = os.path.join(root, f)
            low = f.lower()
            if low == "shownotes.md" and ctx["shownotes"] is None:
                ctx["shownotes"] = p
                text = read_text(p)
                ctx["shownotes_lines"] = text.split("\n")
                ctx["shownotes_text"] = text
            elif low == "chapters.json" and ctx["chapters"] is None:
                ctx["chapters"] = p
            elif low in COVER_NAMES and ctx["cover"] is None:
                ctx["cover"] = p
            elif low == "feed.xml" and ctx["feed"] is None:
                ctx["feed"] = p
            _, ext = os.path.splitext(low)
            if ext in AUDIO_EXTS:
                ctx["audio"].append(p)
    if ctx["cover"]:
        ctx["cover_size"] = image_size(ctx["cover"])
    if ctx["feed"]:
        try:
            import xml.etree.ElementTree as ET
            ctx["feed_tree"] = ET.parse(ctx["feed"]).getroot()
        except Exception:
            ctx["feed_tree"] = None
    return ctx


def _timestamps(ctx):
    """返回 [(秒数, 行号, 原始串)]。时长行本身不算章节时间戳。"""
    out = []
    for i, ln in enumerate(ctx["shownotes_lines"]):
        if re.search(r"时长|duration|length", ln, re.I):
            continue
        for m in TS_LIKE.finditer(ln):
            out.append((m.group(0), i + 1, ln.strip()))
    return out


# ---------------- shownotes ----------------

@rule("POD-SN-001", "blocker", "shownotes", "shownotes.md 缺失",
      "没有 shownotes，播客平台的单集展示页与搜索引擎都无内容可抓，等于节目只发了一半。")
def r_sn_001(ctx):
    if ctx["shownotes"] is None:
        return [_mk("POD-SN-001", ctx["target"], 0, "(目录中无 shownotes.md)")]
    return []


@rule("POD-SN-002", "blocker", "shownotes", "时间戳格式非法",
      "存在形如 12:345 / 1:2 / 99:99 的可疑时间戳。合法格式为 MM:SS 或 H:MM:SS，"
      "非法时间戳会导致播放器章节解析失败、跳转错乱。")
def r_sn_002(ctx):
    if ctx["shownotes"] is None:
        return []
    return [_mk("POD-SN-002", ctx["shownotes"], ln, s)
            for ts, ln, s in _timestamps(ctx) if not TS_VALID.match(ts)]


@rule("POD-SN-003", "warning", "shownotes", "时间戳非递增",
      "后面的时间戳早于前面的，听众点章节会跳到错误位置。检查是否写错了分钟数。")
def r_sn_003(ctx):
    if ctx["shownotes"] is None:
        return []
    hits, prev = [], -1
    for ts, ln, s in _timestamps(ctx):
        if not TS_VALID.match(ts):
            continue
        cur = ts_to_seconds(ts)
        if cur < prev:
            hits.append(_mk("POD-SN-003", ctx["shownotes"], ln, s))
        prev = max(prev, cur)
    return hits


@rule("POD-SN-004", "warning", "shownotes", "首个时间戳不是 00:00",
      "章节列表应从 00:00 开始（开场/片头）。第一个时间戳不是 0 点，"
      "说明开场白没有章节入口。")
def r_sn_004(ctx):
    if ctx["shownotes"] is None:
        return []
    for ts, ln, s in _timestamps(ctx):
        if TS_VALID.match(ts):
            if ts_to_seconds(ts) != 0:
                return [_mk("POD-SN-004", ctx["shownotes"], ln, s)]
            return []
    return []


@rule("POD-SN-005", "warning", "shownotes", "时间戳间距超过 10 分钟",
      "相邻章节间隔超过 10 分钟，中间很可能漏标了一个话题点。听众想回找内容时会抓狂。")
def r_sn_005(ctx):
    if ctx["shownotes"] is None:
        return []
    secs = [ts_to_seconds(ts) for ts, _, _ in _timestamps(ctx) if TS_VALID.match(ts)]
    hits = []
    for a, b in zip(secs, secs[1:]):
        if b - a > 600:
            hits.append(_mk("POD-SN-005", ctx["shownotes"], 0,
                            "间隔 %d 分钟（%s → %s）" % ((b - a) // 60, a, b)))
            break
    return hits


@rule("POD-SN-006", "warning", "shownotes", "时间戳章节过稀（<3 个）",
      "整期节目时间戳少于 3 个，章节导航名存实亡。建议按话题切换点至少标 5 个。")
def r_sn_006(ctx):
    if ctx["shownotes"] is None:
        return []
    n = sum(1 for ts, _, _ in _timestamps(ctx) if TS_VALID.match(ts))
    if n < 3:
        return [_mk("POD-SN-006", ctx["shownotes"], 0, "仅 %d 个有效时间戳" % n)]
    return []


# ---------------- 时长标注 ----------------

def _duration_line(ctx):
    for i, ln in enumerate(ctx["shownotes_lines"]):
        if re.search(r"时长|duration|length", ln, re.I):
            return i + 1, ln.strip()
    return None


@rule("POD-DUR-001", "blocker", "时长", "单集时长未标注",
      "shownotes 里没有时长一行。听众点开前想知道这期要花多少时间，" 
      "平台也用它做展示，这是单集交付的必备字段。")
def r_dur_001(ctx):
    if ctx["shownotes"] is None:
        return []
    if _duration_line(ctx) is None:
        return [_mk("POD-DUR-001", ctx["shownotes"], 0, "(无时长行)")]
    return []


@rule("POD-DUR-002", "warning", "时长", "时长格式非法",
      "时长应写成 HH:MM:SS / MM:SS（如 45:30）或约 45 分钟。写成很长、一小时左右"
      "这类模糊表达等于没标。")
def r_dur_002(ctx):
    if ctx["shownotes"] is None:
        return []
    hit = _duration_line(ctx)
    if not hit:
        return []
    ln, text = hit
    if re.search(r"\d{1,2}:\d{2}(?::\d{2})?|\d+\s*分钟", text):
        return []
    return [_mk("POD-DUR-002", ctx["shownotes"], ln, text)]


@rule("POD-DUR-003", "warning", "时长", "标注时长与末时间戳偏差超过 5 分钟",
      "shownotes 标注的时长和最后一个章节时间戳对不上（差 5 分钟以上），"
      "其中一个写错了，听众会按错的预期安排时间。")
def r_dur_003(ctx):
    if ctx["shownotes"] is None:
        return []
    hit = _duration_line(ctx)
    if not hit:
        return []
    _, text = hit
    m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", text)
    if not m:
        return []
    parts = [int(x) for x in m.groups() if x is not None]
    claimed = 0
    for p in parts:
        claimed = claimed * 60 + p
    secs = [ts_to_seconds(ts) for ts, _, _ in _timestamps(ctx) if TS_VALID.match(ts)]
    if not secs:
        return []
    if abs(claimed - max(secs)) > 300:
        return [_mk("POD-DUR-003", ctx["shownotes"], hit[0], text)]
    return []


# ---------------- 外链 ----------------

@rule("POD-LINK-001", "nit", "shownotes", "外链缺少协议头",
      "写成 example.com 而不是 https://example.com 的裸域名，在部分平台渲染不成可点击链接。")
def r_link_001(ctx):
    if ctx["shownotes"] is None:
        return []
    hits = []
    for i, ln in enumerate(ctx["shownotes_lines"]):
        for m in re.finditer(r"(?<![/\w@.-])([a-z0-9-]+\.(?:com|cn|net|org|io|tv|fm|co)(?:/[^\s)]*)?)", ln, re.I):
            if "://" not in ln[max(0, m.start() - 8):m.start() + 1]:
                hits.append(_mk("POD-LINK-001", ctx["shownotes"], i + 1, ln.strip()))
                break
    return hits


# ---------------- 章节 ----------------

@rule("POD-CH-001", "warning", "章节", "时间戳丰富但无章节文件",
      "shownotes 里有 3 个以上时间戳，却没有 chapters.json（或平台章节列表），"
      "Apple Podcasts / Overcast 的章节跳转功能用不上，浪费了时间戳。")
def r_ch_001(ctx):
    if ctx["shownotes"] is None:
        return []
    n = sum(1 for ts, _, _ in _timestamps(ctx) if TS_VALID.match(ts))
    if n >= 3 and ctx["chapters"] is None:
        return [_mk("POD-CH-001", ctx["shownotes"], 0, "%d 个时间戳但无 chapters.json" % n)]
    return []


@rule("POD-CH-002", "warning", "章节", "chapters.json 与 shownotes 时间戳数量不一致",
      "两处章节数对不上，说明有一处没随剪辑更新。听众看到的章节和实际内容错位。")
def r_ch_002(ctx):
    if ctx["chapters"] is None or ctx["shownotes"] is None:
        return []
    try:
        data = json.loads(read_text(ctx["chapters"]))
        items = data if isinstance(data, list) else data.get("chapters", [])
    except Exception:
        return []
    n_sn = sum(1 for ts, _, _ in _timestamps(ctx) if TS_VALID.match(ts))
    if len(items) != n_sn:
        return [_mk("POD-CH-002", ctx["chapters"], 0,
                    "chapters.json %d 章 vs shownotes %d 个时间戳" % (len(items), n_sn))]
    return []


@rule("POD-CH-003", "warning", "章节", "chapters.json 时间戳格式非法",
      "章节文件里的时间戳不是合法 MM:SS / H:MM:SS，播放器会跳过该章节。")
def r_ch_003(ctx):
    if ctx["chapters"] is None:
        return []
    try:
        data = json.loads(read_text(ctx["chapters"]))
        items = data if isinstance(data, list) else data.get("chapters", [])
    except Exception:
        return [_mk("POD-CH-003", ctx["chapters"], 0, "JSON 解析失败")]
    hits = []
    for it in items:
        ts = str(it.get("time", it.get("timestamp", "")))
        if not TS_VALID.match(ts):
            hits.append(_mk("POD-CH-003", ctx["chapters"], 0, "非法时间戳: %s" % ts))
    return hits


@rule("POD-CH-004", "nit", "章节", "章节标题过长（>30 字）",
      "章节标题在播放器里只显示一行，超过 30 字会被截断，精简一下。")
def r_ch_004(ctx):
    if ctx["chapters"] is None:
        return []
    try:
        data = json.loads(read_text(ctx["chapters"]))
        items = data if isinstance(data, list) else data.get("chapters", [])
    except Exception:
        return []
    return [_mk("POD-CH-004", ctx["chapters"], 0, str(it.get("title", ""))[:40])
            for it in items if len(str(it.get("title", ""))) > 30]


# ---------------- 封面 ----------------

@rule("POD-COV-001", "blocker", "封面", "封面文件缺失",
      "单集目录没有 cover.png / cover.jpg。没有封面，播客平台直接拒绝上架或显示空白。")
def r_cov_001(ctx):
    if ctx["cover"] is None:
        return [_mk("POD-COV-001", ctx["target"], 0, "(无封面文件)")]
    return []


@rule("POD-COV-002", "blocker", "封面", "封面非正方形",
      "播客封面必须是正方形（Apple 规范）。非正方形会被平台强制裁剪，关键信息可能被切掉。")
def r_cov_002(ctx):
    if ctx["cover"] is None or ctx["cover_size"] is None:
        return []
    w, h = ctx["cover_size"]
    if w != h:
        return [_mk("POD-COV-002", ctx["cover"], 0, "%dx%d" % (w, h))]
    return []


@rule("POD-COV-003", "blocker", "封面", "封面边长小于 1400px",
      "Apple Podcasts 要求封面 1400×1400 至 3000×3000。小于 1400 会被平台打回。")
def r_cov_003(ctx):
    if ctx["cover"] is None or ctx["cover_size"] is None:
        return []
    w, _ = ctx["cover_size"]
    if w < 1400:
        return [_mk("POD-COV-003", ctx["cover"], 0, "%dpx" % w)]
    return []


@rule("POD-COV-004", "warning", "封面", "封面边长超过 3000px",
      "超过 3000px 的封面部分平台会拒绝或强制压缩，压到 3000 以内最稳。")
def r_cov_004(ctx):
    if ctx["cover"] is None or ctx["cover_size"] is None:
        return []
    w, _ = ctx["cover_size"]
    if w > 3000:
        return [_mk("POD-COV-004", ctx["cover"], 0, "%dpx" % w)]
    return []


@rule("POD-COV-005", "warning", "封面", "封面文件超过 2MB",
      "封面太大导致 App 内加载慢。压缩到 2MB 以内（JPG 质量 85 左右通常够）。")
def r_cov_005(ctx):
    if ctx["cover"] is None:
        return []
    try:
        size = os.path.getsize(ctx["cover"])
    except OSError:
        return []
    if size > 2 * 1024 * 1024:
        return [_mk("POD-COV-005", ctx["cover"], 0, "%.1fMB" % (size / 1048576))]
    return []


# ---------------- 音频 ----------------

@rule("POD-AU-001", "blocker", "音频", "音频文件缺失",
      "单集目录没有 mp3/m4a/wav 等音频文件。shownotes 写得再好，没有音频发不出去。")
def r_au_001(ctx):
    if not ctx["audio"]:
        return [_mk("POD-AU-001", ctx["target"], 0, "(无音频文件)")]
    return []


@rule("POD-AU-002", "warning", "音频", "音频格式非 mp3/m4a",
      "wav/flac 体积大、部分播客托管按流量计费。发布用 mp3（128k–192k）或 m4a 最通用。")
def r_au_002(ctx):
    return [_mk("POD-AU-002", p, 0, os.path.basename(p))
            for p in ctx["audio"]
            if os.path.splitext(p)[1].lower() not in (".mp3", ".m4a")]


@rule("POD-AU-003", "nit", "音频", "音频文件名含空格或非 ASCII 字符",
      "文件名里的空格/中文在某些托管与 CDN 链路上会被转义出错，建议用小写英文+连字符。")
def r_au_003(ctx):
    hits = []
    for p in ctx["audio"]:
        base = os.path.basename(p)
        if re.search(r"\s|[^\x00-\x7f]", base):
            hits.append(_mk("POD-AU-003", p, 0, base))
    return hits


# ---------------- RSS ----------------

ITUNES_NS = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"


@rule("POD-RSS-001", "blocker", "RSS", "feed.xml 缺失",
      "没有 RSS feed，Apple Podcasts / 小宇宙等平台无法订阅更新。这是播客的水电。")
def r_rss_001(ctx):
    if ctx["feed"] is None:
        return [_mk("POD-RSS-001", ctx["target"], 0, "(无 feed.xml)")]
    return []


@rule("POD-RSS-002", "blocker", "RSS", "channel 缺少 title/description/link",
      "RSS channel 缺必填字段，Apple Podcasts 会拒绝收录。三个字段一个都不能少。")
def r_rss_002(ctx):
    if ctx["feed_tree"] is None:
        return []
    ch = ctx["feed_tree"].find("channel")
    if ch is None:
        return [_mk("POD-RSS-002", ctx["feed"], 0, "无 channel 节点")]
    missing = [t for t in ("title", "description", "link")
               if ch.find(t) is None or not (ch.find(t).text or "").strip()]
    if missing:
        return [_mk("POD-RSS-002", ctx["feed"], 0, "缺: %s" % ", ".join(missing))]
    return []


@rule("POD-RSS-003", "warning", "RSS", "channel 缺 itunes:author/itunes:image/language",
      "缺作者、封面或语言声明，节目在平台展示不完整（无作者名、无封面图、语言识别错）。")
def r_rss_003(ctx):
    if ctx["feed_tree"] is None:
        return []
    ch = ctx["feed_tree"].find("channel")
    if ch is None:
        return []
    missing = []
    if ch.find(ITUNES_NS + "author") is None:
        missing.append("itunes:author")
    img = ch.find(ITUNES_NS + "image")
    if img is None or not img.get("href"):
        missing.append("itunes:image")
    if ch.find("language") is None:
        missing.append("language")
    if missing:
        return [_mk("POD-RSS-003", ctx["feed"], 0, "缺: %s" % ", ".join(missing))]
    return []


@rule("POD-RSS-004", "blocker", "RSS", "item 缺少 enclosure（音频地址）",
      "单集 item 没有 enclosure，订阅端下载不到音频——这期节目等于没发布。")
def r_rss_004(ctx):
    if ctx["feed_tree"] is None:
        return []
    hits = []
    for item in ctx["feed_tree"].find("channel").findall("item"):
        enc = item.find("enclosure")
        if enc is None or not enc.get("url"):
            title = item.findtext("title") or "(无标题)"
            hits.append(_mk("POD-RSS-004", ctx["feed"], 0, title[:40]))
    return hits


@rule("POD-RSS-005", "warning", "RSS", "item 缺少 guid/pubDate",
      "缺 guid 会导致客户端把同一期识别成多期重复；缺 pubDate 排序错乱。")
def r_rss_005(ctx):
    if ctx["feed_tree"] is None:
        return []
    hits = []
    for item in ctx["feed_tree"].find("channel").findall("item"):
        title = item.findtext("title") or "(无标题)"
        missing = [t for t in ("guid", "pubDate") if item.find(t) is None]
        if missing:
            hits.append(_mk("POD-RSS-005", ctx["feed"], 0,
                            "%s 缺: %s" % (title[:30], ",".join(missing))))
    return hits


@rule("POD-RSS-006", "warning", "RSS", "item 缺少 itunes:duration",
      "没有 itunes:duration，Apple Podcasts 不显示单集时长，影响听众点击决策。")
def r_rss_006(ctx):
    if ctx["feed_tree"] is None:
        return []
    hits = []
    for item in ctx["feed_tree"].find("channel").findall("item"):
        if item.find(ITUNES_NS + "duration") is None:
            title = item.findtext("title") or "(无标题)"
            hits.append(_mk("POD-RSS-006", ctx["feed"], 0, title[:40]))
    return hits


@rule("POD-RSS-007", "nit", "RSS", "channel description 过短（<50 字）",
      "节目简介不到 50 字，平台搜索与推荐位吃亏。写清这节目讲什么、适合谁。")
def r_rss_007(ctx):
    if ctx["feed_tree"] is None:
        return []
    ch = ctx["feed_tree"].find("channel")
    if ch is None:
        return []
    desc = (ch.findtext("description") or "").strip()
    if desc and len(desc) < 50:
        return [_mk("POD-RSS-007", ctx["feed"], 0, "%d 字" % len(desc))]
    return []


# ---------------------------------------------------------------- 主流程

SEV_ORDER = {"blocker": 0, "warning": 1, "nit": 2}


def run_audit(target):
    ctx = _collect(target)
    findings = []
    for r in RULES:
        try:
            findings.extend(r["check"](ctx))
        except Exception as e:
            findings.append(Finding(r["id"], "nit", "脚本", "规则执行异常",
                                    target, 0, str(e)[:120],
                                    "规则内部出错，已 fail-open 跳过，不影响其他规则。"))
    findings.sort(key=lambda f: (SEV_ORDER[f.severity], f.rule_id, f.file, f.line))
    sev = {"blocker": 0, "warning": 0, "nit": 0}
    for f in findings:
        sev[f.severity] += 1
    return {
        "tool": TOOL, "version": VERSION, "target": os.path.abspath(target),
        "summary": {"blocker": sev["blocker"], "warning": sev["warning"],
                    "nit": sev["nit"], "rules_run": len(RULES)},
        "findings": [f.to_dict() for f in findings],
    }


def format_text(data):
    lines = ["[%s v%s] 目标: %s" % (data["tool"], data["version"], data["target"])]
    s = data["summary"]
    lines.append("规则 %d 条 → blocker %d / warning %d / nit %d"
                 % (s["rules_run"], s["blocker"], s["warning"], s["nit"]))
    for f in data["findings"]:
        loc = "%s:%s" % (f["file"], f["line"]) if f["line"] else f["file"]
        lines.append("[%s][%s] %s\n    %s → %s"
                     % (f["severity"], f["rule_id"], f["title"], loc, f["detail"][:90]))
    if not data["findings"]:
        lines.append("干净：无发现。")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--format", choices=["json", "text"], default="json")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"], default="blocker")
    args = ap.parse_args()
    data = run_audit(args.target)
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_text(data))
    n = data["summary"][args.fail_on]
    if args.fail_on == "warning":
        n += data["summary"]["blocker"]
    elif args.fail_on == "nit":
        n += data["summary"]["blocker"] + data["summary"]["warning"]
    return 2 if n > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
