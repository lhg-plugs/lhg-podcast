---
name: lhg-pod-distribute
description: 播客分发方法论：shownotes 写作、章节文件、封面规范、RSS feed 搭建、多平台上架清单、自查流程。成片之后"发出去"的全部工作。
license: MIT
compatibility: 适用于任何支持 Markdown 指令的 AI 助手（Claude Code、豆包、Workbuddy 等）
metadata:
  version: 1.0.0
  author: 刘洪光
---

# lhg-pod-distribute：播客分发

> 目标：成片变成"各平台都能正常展示、听众愿意点开"的一期节目。
> 核心纪律：**先跑脚本（机器），再做评审（人）；blocker 不清零，不许说可发布。**

## 1. 何时使用

- 成片已出：按第 3 节顺序做 shownotes→封面→RSS→上架
- 只做 shownotes：看第 3.2 节
- 从零搭 RSS：看第 3.4 节
- 发布前：跑第 5 节自查全流程

## 2. 输入 / 输出

**输入**：成片音频、转录稿/剪辑记录、节目基本信息（名称/简介/作者）。

**输出**：shownotes.md + chapters.json + 封面图 + feed.xml（新增/更新 item）+ 上架检查单 + 自查报告。

## 3. 分步方法论

### 3.1 交付物清单（一期节目=5 件套）

| 交付物 | 规格 | 缺了会怎样 |
|---|---|---|
| 音频 | mp3/m4a，-16 LUFS | 没这个全白搭 |
| shownotes.md | 时间戳章节+时长+外链 | 平台展示页空白 |
| chapters.json | 与 shownotes 时间戳一致 | 章节跳转功能浪费 |
| 封面 | 正方形 1400–3000px | 平台打回/强制裁剪 |
| feed.xml item | title/guid/pubDate/enclosure/duration | 订阅端收不到这期 |

### 3.2 shownotes 写作

```markdown
# EPxx：标题（标题党适度，关键词前置方便搜索）

时长：MM:SS（必填）

00:00 开场：钩子一句话
08:20 话题一
16:40 话题二
...

本期提到：
- 书《xxx》：https://...
- 工具 xxx：https://...
```

写作纪律：
- 时间戳从 00:00 开始、递增、间距≤10 分钟；格式只许 MM:SS 或 H:MM:SS。
- 每个时间戳后跟"话题+钩子"，不是干巴巴的标题（如"08:20 为什么副业先别辞职"）。
- 外链全写 https；人名书名不确定的标 `[待确认]`，不许编。
- 标注时长与最后一个时间戳偏差≤5 分钟。

### 3.3 封面规范

- 正方形，边长 1400–3000px（Apple Podcasts 公开规范），文件 <2MB。
- 小图测试：缩到 120px，标题字还能认出来；认不出就放大字号、减少字数。
- 版权：不用无授权的网图/字体；AI 生成图确认商用条款。

### 3.4 RSS feed 搭建

channel 必填（缺一不可）：`title` / `description`（≥50 字，写清讲什么、适合谁）/ `link` / `language` / `itunes:author` / `itunes:image`。

每个 item 必填：`title` / `guid`（唯一且永久）/ `pubDate` / `enclosure`（音频直链，含 length 与 type）/ `itunes:duration`。

托管三选一：
1. **免费托管平台**：省心，适合新手；注意免费版的流量/存储上限与导出政策。
2. **对象存储+RSS**：音频放对象存储，自己维护 feed.xml；自由度高，要懂一点技术。
3. **已有网站加 feed**：有博客/官网的人顺手，feed 只是多个 xml。

选型建议：先跑起来用 1，节目活下来再迁 2 或 3；迁移时 guid 不许变（变了客户端会重复下载）。

### 3.5 平台上架清单

按目标听众排序，常见四家：
- [ ] 小宇宙：简介、分类、封面
- [ ] Apple Podcasts：feed 提交、分类、语言
- [ ] Spotify：Anchor/Spotify for Podcasters 认领
- [ ] 喜马拉雅：专辑分类、标签

每家上架后：手机端实际订阅一次，检查封面/标题/时长/章节展示正常。

### 3.6 发布后 24 小时

- 看首波数据：完播率最低的 3 分钟在哪（下期剪辑重点）。
- 回复前 10 条评论（冷启动期每条都回）。
- 把本期时间戳里反响最好的话题记下来 → 下期选题候选。

## 4. 反模式

- ❌ shownotes 只有一句话简介——时间戳章节是播客的"目录"，没目录的书没人买
- ❌ 封面用 800px 的图"先凑合"——平台打回那天更浪费时间
- ❌ feed.xml 里 guid 用"第 8 期"这种会变的——迁移/重发就乱套
- ❌ 从没在手机上订阅过自己的节目——展示翻车自己都不知道
- ❌ 音频文件名 `最终版2真的定了.mp3`——小写英文连字符，现在就改

## 5. 自查流程（发布前必跑）

### 第一步：跑确定性审计脚本（必做，零 LLM 成本）

```
python3 <插件目录>/scripts/audit/podcast_audit.py --target <单集目录>
```

- 29 条规则：shownotes 时间戳 6、时长标注 3、外链 1、章节 4、封面 5、音频 3、RSS 7。
- 有 blocker 时脚本以非零 exit code 退出——这是设计，不是 bug。
- `--fail-on` 控制 exit code 语义：默认 `blocker`；想要更严可设为 `warning`。

### 第二步：分级

| 级别 | 定义 | 处理 |
|---|---|---|
| blocker | 发出去会翻车：无音频、封面不合格、无 enclosure、时间戳非法 | 必须修，不修不许发布（commit 前 hook 会拦截） |
| warning | 大概率是坑：章节缺失、时长偏差、RSS 字段不全 | 本次修掉；修不掉写理由进报告 |
| nit | 洁癖项：裸域名外链、简介过短、文件名不规范 | 顺手修 |

### 第三步：人工评审（脚本覆盖不到的）

- [ ] 时间戳跳转抽查 3 个：点的和听到的对得上
- [ ] 音频抽听开头 2 分钟：底噪/喷麦/音量跳变
- [ ] 封面 120px 小图可读、无版权风险元素
- [ ] 手机实际订阅一次：封面/标题/时长/章节展示正常
- [ ] 人名书名无错别字（对照转录稿）

### 第四步：输出报告

```markdown
# 自查报告 EPxx（日期）
## 结论：可发布 / 不可发布
## blocker（n）：已修 n，剩余 n
## warning（n）：已修 n，豁免 n（理由）
## nit（n）
## 人工评审：x/y 通过
## 需人工处理
```

## 6. 自检与反馈

每次执行完本 skill，做一次轻量自检：

1. 脚本是否真的跑了？→ 没跑不算做。
2. blocker 是否清零或全部列入"需人工处理"？
3. 人工评审是否逐项打勾且有依据？

标准冒烟用例：对插件自带的 `fixtures/` 跑脚本，确认坏 fixture 的 blocker 全命中、好 fixture 零 blocker（见仓库根 `smoke_test.py`）。

反馈渠道：以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-podcast/issues，正文写清"输入 → 错误输出 → 期望输出"。规则误报/漏报请附最小复现用例。

## 出品：刘洪光

本 skill 由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 视频号：搜「刘洪光实名上网」
- 微信：lhgsmsw
