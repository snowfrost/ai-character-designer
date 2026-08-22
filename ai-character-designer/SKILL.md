---
name: ai-character-designer
description: "This skill should be used when a user wants to design, build, or generate a consistent, non-generic AI character (persona / virtual talent / 虚拟艺人 / 角色设定) and needs detailed bilingual Chinese-English prompts. It implements 麦橘 MERJIC's 骨皮形神 16 型 methodology plus facial-aesthetics theory, and outputs prompts tuned for three image models: gpt-image-2 (OpenAI), 即梦5.0pro (ByteDance Seedream), and flux2krea (FLUX.2 Krea). If an API is configured, it can directly generate portrait, full-body, and three-view images. Trigger on requests like 设计一个不撞脸的 AI 角色, 生成角色三视图提示词, AI 人像提示词, 捏脸/角色设定/虚拟艺人, or any mention of 骨皮形神 / 麦橘 / 即梦 / flux krea / gpt-image prompts."
agent_created: true
---

# AI 角色打造设计师（ai-character-designer）

把「审美玄学」翻译成可复制系统的角色设计 Skill。核心产物是**详细的中英双语提示词**，
分别遵循 gpt-image-2 / 即梦5.0pro / flux2krea 三种模型标准；配置接口后可直接出图
（肖像 / 全身 / 三视）。一句话心法：**AI 不是帮你创造角色，它是按你的规则设定角色；
规则模糊，它就随机发挥、千人一面。**

## 何时使用

- 用户要设计一个有辨识度、不撞脸的 AI 角色 / 虚拟艺人 / 角色设定。
- 用户要面向具体出图模型（GPT 图像 / 即梦 / FLUX.2 Krea）写提示词。
- 用户要做角色资产化：标准照锚点、全身、四视图、视频一致性。
- 用户抱怨「AI 脸千人一面 / 蜡像假面 / 换脸漂移」需要解法。

## 方法论总览（执行前先读 references）

1. **`references/theory.md`** — 骨皮形神 16 型（四问定脸）、审美资产化、麦橘循环论、阵营速查。
2. **`references/aesthetics.md`** — ima《AI美人指南》PPT 深度拆解（人体比例/头骨/三庭五眼/眼/鼻唇/侧脸折叠度/妆容）+ 出图检查清单。
3. **`references/engineering.md`** — 刺猬星球工程化流程：标准照→锁脸→全身→四视图→拆结构写差异→身份锁→一致性三招 + 原文全身/四视图模板。
4. **`references/prompt_standards.md`** — **核心**：三模型提示词习惯对照、骨皮形神→特征词库、装配顺序、API 配置（config.json 结构）。
5. **`references/academic.md`** — 三庭五眼/折叠度/黄金比 + 3 篇论文（解释「AI 脸=当代平均脸」与「结构>对称」）。

## 执行流程

### 步骤 1：定角色（骨皮形神四问）
向用户提四个问题，或读用户给的角色卡：灵动/沉稳？抓眼/耐看？聚焦/松弛？疏远/亲近？
落点 → 骨(修/敦) 皮(浓/淡) 形(聚/散) 神(锐/柔)，并确定四大阵营之一。
若用户已有详细描述，直接填 `assets/character_card_template.json`。

### 步骤 2：补结构差异（反平均脸的关键）
按 `engineering.md` §3 / `aesthetics.md` 检查清单，把脸型/眉眼/鼻/唇/皮肤/发型写成
**具体差异**，而非「美/精致」。加不完美细节（毛孔/雀斑/单眼皮/高颧骨）破蜡像感。

### 步骤 3：生成提示词（调用脚本）
用 `scripts/generate.py` 渲染三模型中英双语提示词（肖像/全身/三视）：
```bash
# 交互四问向导
python <skill>/scripts/generate.py

# 用角色卡（默认三模型 × 三视图）
python <skill>/scripts/generate.py --card character_card.json --out ./out

# 指定模型/视图
python <skill>/scripts/generate.py --card card.json \
    --models jimeng_5_pro,flux2_krea --views portrait,fullbody
```
输出 `./out/prompts.md`（可读）与 `./out/prompts.json`（结构化）。

### 步骤 4：配置接口直出图（可选）
若用户要直接出图，让其提供 config.json + 环境变量（结构见 `prompt_standards.md` §3）：
- `gpt_image_2`：OpenAI，env `OPENAI_API_KEY`
- `jimeng_5_pro`：火山方舟 Seedream，env `ARK_API_KEY`
- `flux2_krea`：BFL FLUX.2 Krea，env `BFL_API_KEY`
然后：
```bash
python <skill>/scripts/generate.py --card card.json --generate --out ./out
```
脚本按视图调用各模型接口，存 `模型__视图.png`。未配置则跳过、只给提示词。

### 步骤 5：资产化与一致性（视频/系列图）
- 先做**标准照**（白底/均匀光/正面）作锚点；再出全身、四视图。
- 后期变装写明**身份锁**（不可改：五官/脸型/身材/发色；可改：衣服/场景/配饰）。
- 分镜强制带角色标签 + 表情语法（见 `engineering.md` §6）。

## 注意事项

- **反蜡像铁律**：每条提示词保留皮肤肌理与血色，避「完美皮肤/8K/超现实」触发词（尤其即梦/FLUX）。
- **写差异不写美**：结构越具体，AI 越不走平均值。
- **模型名/端点会变**：config 里的 `model` / `base_url` 以用户账号后台或官方文档为准，脚本已留默认值与降级提示。
- **学术背书**：用 `academic.md` 的 Bernal 2024 等论文解释「为何要拆结构写差异」，增强说服力。
