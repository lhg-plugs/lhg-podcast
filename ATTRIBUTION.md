# 灵感来源与致谢（Attribution）

本插件的**方法论灵感**来自以下优秀的开源项目与公开标准，**所有实现代码、检测规则与文案均为原创**，未复制任何第三方的原文案与代码。

| 项目 / 标准 | 作者 / 组织 | 许可 | 链接 | 借鉴了什么思路 |
|---|---|---|---|---|
| Podcast 製作流水線 skill | gaskhuang | 未声明（仅借鉴高层思路） | https://github.com/gaskhuang/opencraw-master-workspace | "录制前研究+大纲、录制后转录→时间戳 shownotes+推广素材"的分阶段流水线思想 |
| podcast-episode skill | blkgelcode | 未声明（仅借鉴高层思路） | https://github.com/blkgelcode/code | "用确定性脚本校验交付物清单（verify.py）+ 角色分工"的模式；本插件审计脚本的"交付物校验"思想受其启发，**规则条目全部自研** |
| marketing-podcast-strategist skill | itzfaisal 等 | 未声明（仅借鉴高层思路） | https://github.com/itzfaisal/agency-agents | "制作标准卡（设备/环境/后期规格/封面/shownotes 模板）"的问题意识 |
| Apple Podcasts 播客封面与 RSS 规范 | Apple | 公开技术规范 | https://podcasters.apple.com | 封面 1400×1400–3000×3000 正方形、RSS 必填字段等**公开技术规格**（事实性标准，非创意表达） |
| 播客响度惯例（-16 LUFS 立体声） | 行业惯例（AES/EBU R128 衍生实践） | 公开技术惯例 | — | 播客人声后期响度目标为 -16 LUFS 的行业惯例（事实性标准） |

## 声明

1. **借鉴思路，实现与文案均为原创**：以上项目的具体文案、规则原文、代码实现均未被复制。本插件的 skill 方法论文案、审计规则、命令流程均为独立撰写。Apple 播客规范与响度标准属于公开技术事实，按其字面规格实现不构成复制。
2. **许可合规**：许可未声明的项目仅借鉴高层思路，未复制其任何表达；公开技术规范按事实性标准使用。
3. **商标与归属**：各项目名称与作者署名归其各自所有者所有。

## 本插件自身的许可

本插件原创部分采用 MIT 许可（见 `LICENSE` 文件），版权所有：刘洪光（https://github.com/lhg-skills）。
