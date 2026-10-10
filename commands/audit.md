---
description: 单集交付体检：跑确定性审计脚本 + 人工评审清单，输出分级报告并自动修复 blocker。
argument-hint: "[单集目录] [--fix]"
---

# /lhg-podcast:audit —— 单集交付体检

用户输入在 `$ARGUMENTS` 中：`[单集目录] [--fix]`。目录缺省为当前目录。

## 流程（加载 lhg-pod-distribute 第 5 节全程指导）

### 1. 跑脚本
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit/podcast_audit.py --target <单集目录> --format text
```
记下 blocker / warning / nit 的数量与明细（含文件、行号、规则说明）。

### 2. 分级与修复
- blocker：逐条修。`--fix` 缺省即自动修（最小改动原则）；修一条用脚本复查一条。
- 修不掉的（如需用户重录音频、重画封面）→ 列入"需人工处理"，不许为清零改规则。
- warning：修掉或写豁免理由（+有效期）；nit：顺手修。

### 3. 人工评审（脚本覆盖不到的）
- 内容：时间戳标题与实际话题对得上（抽 3 个跳转验证）、人名书名无错别字
- 音频：抽听开头 2 分钟（底噪/喷麦/音量跳变）、-16 LUFS 响度达标
- 封面：小图可读性（缩到 120px 看标题）、无版权风险元素
- RSS：在播客客户端实际订阅一次，看封面/标题/时长展示正常

### 4. 输出报告
按 lhg-pod-distribute 第 6 节模板输出自查报告，存为 `docs/audit-EPxx.md`，结论写清"可发布 / 不可发布"。

## 硬规则
- 有 blocker 就说"可发布" → 不许。
- 为清零改脚本规则或阈值 → 这是作弊，不许。
- 音频没抽听过不许说"音频没问题"。
