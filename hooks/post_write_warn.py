#!/usr/bin/env python3
"""lhg-podcast 硬门②（警告级，不拦截）：写 shownotes.md 无时间戳章节时提醒。

触发：PostToolUse / Write|Edit。只做提醒，永远 exit 0、不拦截写入。

逃生方式：LHG_PODCAST_HOOKS_OFF=1（环境变量）可关闭本提醒；
或 /plugin disable lhg-podcast 停用整个插件。
零第三方依赖。
"""

import json
import os
import re
import sys

TS_RE = re.compile(r"\b(?:\d{1,2}:)?[0-5]?\d:[0-5]\d\b")


def main() -> int:
    if os.environ.get("LHG_PODCAST_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return 0

    if os.path.basename(file_path).lower() != "shownotes.md":
        return 0  # 只关心 shownotes，其余快速放行

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return 0

    if TS_RE.search(text):
        return 0  # 已有时间戳，不提醒

    msg = (
        "shownotes 提醒（lhg-podcast）：%s 里没有检测到时间戳章节。\n"
        "时间戳章节是播客的目录：听众靠它跳转话题，播放器靠它做章节跳转。\n"
        "建议按话题切换点补 5+ 个时间戳（MM:SS 格式，从 00:00 开始）；\n"
        "确认本期不需要章节时忽略本提醒，或在 /lhg-podcast:audit 报告中记录。\n"
        "关闭本提醒：export LHG_PODCAST_HOOKS_OFF=1（当前会话有效）。"
    ) % file_path
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": msg,
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
