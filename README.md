<!-- About 简介（推送后填写到仓库 About 栏）：
播客制作专家：选题→录制→剪辑→shownotes→分发，一期节目全流程 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-podcast
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, podcast, rss, audio -->

# lhg-podcast：播客制作专家

> **一句话介绍**：一句话开工一期播客节目——选题三问过滤器、大纲钩子、录制指引（设备/环境/话术/双轨备份）、剪辑三刀流、时间戳 shownotes、封面与 RSS 分发，29 条确定性规则发布前自检。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-podcast
> /plugin install lhg-podcast@lhg-plugs
> ```

## 它是什么

`lhg-podcast` 是一个 Claude Code 插件（plugin 为主、skill 为辅），专为"想开播但不知道从哪下手"的小白设计：

- **4 个命令**（小白入口）：`podcast` 一期节目全流程（选题→大纲→录制→剪辑→shownotes→分发），`launch` 从零开播（定位/命名/封面/RSS/上架），`shownotes` 转录稿→时间戳 shownotes+章节文件，`audit` 单集交付体检
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：选题与定位、录制指引、剪辑方法论、分发与自查
- **2 个专家 agent**：播客制作人（端到端执行）、独立审计员（发布前挑毛病）
- **2 个硬门 hooks**：commit 前单集审计拦截、无时间戳的 shownotes 写作提醒（均可一键豁免）
- **29 条确定性自查规则**：时间戳格式/递增、章节缺失、封面尺寸（1400–3000 正方形）、RSS 必填字段、单集时长标注，纯 Python、零第三方依赖，5 秒出结果

工作流：`launch`（搭电台）→ `podcast`（做节目）→ `shownotes`（写目录）→ `audit`（查一遍），也可以只用其中一段。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-podcast:podcast` | 一期节目全流程：选题→大纲→录制指引→剪辑工单→shownotes→分发 | `/lhg-podcast:podcast "副业第一课" --guest 王强` |
| `/lhg-podcast:launch` | 从零开播：定位/命名/封面/RSS 托管/分发清单 | `/lhg-podcast:launch "给上班族的副业试错电台"` |
| `/lhg-podcast:shownotes` | 转录稿→时间戳 shownotes + chapters.json | `/lhg-podcast:shownotes ./ep08-transcript.txt` |
| `/lhg-podcast:audit` | 单集交付体检（脚本 + 人工评审清单） | `/lhg-podcast:audit ./ep08/` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工评审清单（人）：

1. 先跑 `scripts/audit/podcast_audit.py`（29 条规则：shownotes 6、时长 3、外链 1、章节 4、封面 5、音频 3、RSS 7），零 LLM 成本；
2. 发现分三级：**blocker**（必须修，无音频/封面不合格/无 enclosure/时间戳非法，commit 前 hook 会拦截）、**warning**（修或写豁免理由）、**nit**（顺手修）；
3. 再按 `lhg-pod-distribute` 第 5 节的人工评审清单过一遍脚本抓不到的（时间戳跳转抽查、音频抽听、封面小图可读性、手机实际订阅验证）。

blocker 清零才算可发布；为清零改规则算作弊，不许。

## 目录结构

```
lhg-podcast/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：podcast / launch / shownotes / audit
├── skills/                  # 4 个平台中立 skill（topic/record/edit/distribute）
├── agents/                  # 2 个专家 agent（producer / auditor）
├── hooks/                   # 2 个硬门（commit 前审计拦截 / shownotes 无时间戳提醒）+ 豁免说明
├── scripts/audit/           # 29 条确定性自查规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你想开播客，但卡在"第一期讲什么、用什么设备、怎么剪"时 → 用 `/lhg-podcast:podcast`，一句话开工
- 你已经有节目，只想把 shownotes/章节/RSS 这些"发出去"的活干标准时 → 用 `/lhg-podcast:shownotes` + `/lhg-podcast:audit`
- 你要发布前怕翻车（封面被平台打回、RSS 订阅不到、时间戳跳转错乱）时 → 跑 `/lhg-podcast:audit`
- 你想给播客工作室立一套"发布前必须过自检"的纪律时 → 它的 hook 硬门与审计脚本开箱即用

**什么时候不用：**

- 你只想做视频口播剪辑（字幕/卡点/混剪）→ 那是 `lhg-video-edit` 的地盘，本插件是纯音频播客专家
- 你的节目是音乐/电台剧等强后期混音类型 → 本插件的剪辑方法论按谈话类播客设计，响度标准也按人声节目给
- 你希望 AI 完全自由发挥、不接受任何硬门 → 它的 commit 拦截和 shownotes 提醒会让你烦（可关，但那就别装它）

**风险点诚实说明：**

- **音频质量靠录制**：29 条规则查的是交付物格式与完整性，查不出"这期内容无聊"；选题三问过滤器才是内容质量的门
- **封面尺寸是硬标准**：1400–3000px 正方形来自 Apple 公开规范，低于 1400 会被打回，没有"凑合"
- **响度 -16 LUFS 是行业惯例**：本插件只给目标值与流程，不替你做母带；偏离太多会被平台归一化压得忽大忽小
- **转录稿人名/书名**：不确定的标 `[待确认]`，插件不许编，审计也不查事实——事实核对是人工评审的事

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-podcast](https://github.com/lhg-plugs/lhg-podcast) | 播客制作专家：选题→录制→剪辑→shownotes→分发，一期节目全流程 | `/plugin install lhg-podcast@lhg-plugs` |
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、29 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-podcast/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
