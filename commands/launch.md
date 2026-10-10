---
description: 从零开播：节目定位→命名→封面→RSS托管→分发清单，一次把"电台"搭起来。
argument-hint: "[节目定位一句话]"
---

# /lhg-podcast:launch —— 从零开播

用户输入在 `$ARGUMENTS` 中：`[节目定位一句话]`，如"给上班族的副业试错电台"。

## 流程（加载 lhg-pod-topic + lhg-pod-distribute）

### 1. 定位三件套（lhg-pod-topic 第 2 节）
- 输出：节目名（3 选 1，用户拍板）、一句话 slogan、目标听众画像（越具体越好）。
- 命名检查：小宇宙/Apple Podcasts 重名检索思路、发音无歧义、3 秒能记住。

### 2. 品牌包
- 封面：正方形 1400–3000px，标题字在小图下可读（手机列表里只有指甲盖大）。
- 片头/片尾：15 秒内音频签名（可用免费音效+人声口播，别用无版权热歌）。

### 3. RSS 与托管（lhg-pod-distribute 第 4 节）
- 输出 feed.xml（含 channel 必填：title/description/link/language/itunes:author/itunes:image）。
- 托管三选一：免费托管平台 / 自建对象存储+RSS / 已有网站加 feed（给对比表，用户选）。

### 4. 分发清单
- 首发平台清单：小宇宙、Apple Podcasts、Spotify、喜马拉雅（按目标听众排序）。
- 每平台的上架要求逐项打勾（封面、简介、分类、语言）。

### 5. 自查
跑 `/lhg-podcast:audit`（含 feed.xml 校验），blocker 清零。

## 硬规则
- 封面不是正方形或小于 1400px 不许说"品牌包完成"。
- feed.xml 缺 title/description/link 中任何一个不许进入分发清单。
- 节目名不做重名检索不许定稿。
