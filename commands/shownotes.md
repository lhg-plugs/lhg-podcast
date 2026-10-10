---
description: 录音稿/转录文本→带时间戳的 shownotes + 章节文件，话题切换点自动识别。
argument-hint: "[转录稿路径] [--chapters]"
---

# /lhg-podcast:shownotes —— 文稿→shownotes

用户输入在 `$ARGUMENTS` 中：`[转录稿路径] [--chapters]`。路径缺省时请用户粘贴文本。

## 流程（加载 lhg-pod-distribute 第 2 节）

### 1. 读稿
读取转录稿全文，先通读一遍标出话题切换点（不是按段落，是按"听众想跳转"的粒度）。

### 2. 生成 shownotes.md
结构：
```markdown
# EPxx：标题

时长：MM:SS

00:00 开场
MM:SS 话题一标题
...

本期提到：
- 工具/书/文章：https://...（全写 https，裸域名会被审计标 nit）
```

### 3. 章节文件（`--chapters` 或时间戳≥3 个时）
生成 chapters.json（time/title 数组），与 shownotes 时间戳数量一致。

### 4. 自查
- 时间戳递增、从 00:00 开始、间距≤10 分钟；
- 标注时长与末时间戳偏差≤5 分钟；
- 外链全部带 https。

## 硬规则
- 时间戳格式只许 MM:SS 或 H:MM:SS（如 05:23、1:02:10），不许 5:2:3 这类写法。
- 转录稿里的人名/书名不确定时标 `[待确认]`，不许编一个。
- shownotes 写完必须跑一遍审计脚本的时间戳规则（POD-SN-*）。
