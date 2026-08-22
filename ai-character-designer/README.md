# ai-character-designer · AI 角色打造设计师

把「审美玄学」翻译成可复制系统的角色设计 Skill。核心产物是**详细的中英双语提示词**，分别遵循 **gpt-image-2（OpenAI）/ 即梦 5.0 pro（字节 Seedream）/ flux2krea（FLUX.2 Krea）** 三种模型标准；配置接口后可直接出图（肖像 / 全身 / 三视）。

> 一句话心法：**AI 不是帮你创造角色，它是按你的规则设定角色；规则模糊，它就随机发挥、千人一面。**

---

## 它解决什么问题

- 想做一个**有辨识度、不撞脸**的 AI 角色 / 虚拟艺人 / 角色设定，却只会写「精致美丽」。
- 面向具体出图模型写提示词时，不知道各家的句式、负向、尺寸差异。
- 角色资产化：标准照锚点、全身、四视图、视频一致性——换脸漂移、蜡像假面。

方法论基于**麦橘 MERJIC「骨皮形神」16 型** + 面部美学理论 + 刺猬星球工程化流程，并有学术论文背书（解释「AI 脸 = 当代平均脸」与「结构 > 对称」）。

---

## 目录结构

```
ai-character-designer/
├── SKILL.md                              # 技能主文件（触发条件 + 执行流程）
├── README.md                             # 本文件
├── assets/
│   └── character_card_template.json      # 角色卡模板（四问落点 → 结构化字段）
├── references/
│   ├── theory.md                         # 骨皮形神 16 型、审美资产化、阵营速查
│   ├── aesthetics.md                     # 人体比例/头骨/三庭五眼/折叠度/妆容 + 出图检查清单
│   ├── engineering.md                    # 工程化流程：标准照→锁脸→全身→四视图→一致性
│   ├── prompt_standards.md               # ★核心：三模型提示词对照、特征词库、API 配置
│   └── academic.md                       # 三庭五眼/折叠度/黄金比 + 3 篇论文
└── scripts/
    └── generate.py                       # 渲染三模型中英双语提示词 + 可选直出图
```

---

## 快速开始

### 1. 定角色（骨皮形神四问）

向用户提四个问题，或读用户给的角色卡：

| 旋钮 | 落点 | 含义 |
|---|---|---|
| 骨 | 修 / 敦 | 轻盈脱俗 / 稳固敦实 |
| 皮 | 浓 / 淡 | 高对比抓眼 / 低对比耐看 |
| 形 | 聚 / 散 | 五官缜密收拢 / 松弛舒展 |
| 神 | 锐 / 柔 | 冷峻疏离 / 治愈温柔 |

四问落点 → 确定四大阵营之一（凌越者=浓+锐 / 造梦者=浓+柔 / 洞察者=淡+锐 / 抚慰者=淡+柔），再细化到 16 格。

若用户已有详细描述，直接填 [`assets/character_card_template.json`](assets/character_card_template.json)。

### 2. 生成提示词（调用脚本）

```bash
# 交互四问向导
python scripts/generate.py

# 用角色卡（默认三模型 × 三视图）
python scripts/generate.py --card character_card.json --out ./out

# 指定模型 / 视图
python scripts/generate.py --card card.json \
    --models jimeng_5_pro,flux2_krea --views portrait,fullbody
```

输出：
- `./out/prompts.md` —— 可读的中英双语提示词
- `./out/prompts.json` —— 结构化数据

### 3. 配置接口直出图（可选）

提供 `config.json` + 环境变量（结构见 [`references/prompt_standards.md`](references/prompt_standards.md) §3）：

| 模型 | 服务商 | 环境变量 |
|---|---|---|
| `gpt_image_2` | OpenAI | `OPENAI_API_KEY` |
| `jimeng_5_pro` | 火山方舟 Seedream | `ARK_API_KEY` |
| `flux2_krea` | BFL FLUX.2 Krea | `BFL_API_KEY` |

```bash
python scripts/generate.py --card card.json --generate --out ./out
```

脚本按视图调用各模型接口，存 `模型__视图.png`。未配置则跳过、只给提示词。

### 4. 资产化与一致性（视频 / 系列图）

- 先做**标准照**（白底 / 均匀光 / 正面）作锚点；再出全身、四视图。
- 后期变装写明**身份锁**（不可改：五官 / 脸型 / 身材 / 发色；可改：衣服 / 场景 / 配饰）。
- 分镜强制带角色标签 + 表情语法。

---

## 反「蜡像 / 千人一面」铁律

写进每条提示词：

- **皮肤**：保留毛孔 / 血色 / 轻微肌理，拒绝「完美皮肤 / 8K / 超现实」类触发词（即梦 / FLUX 尤其要避）。
- **结构**：必写**差异**而非「美」——脸型偏圆 / 偏方、内眼角高低、鼻翼宽窄、唇峰清晰与否、单眼皮 / 高颧骨等不完美细节。
- **模型名 / 端点会变**：`config.json` 里的 `model` / `base_url` 以你账号后台或官方文档为准。

---

## 角色卡字段（节选）

```json
{
  "name": "角色代号",
  "subject": { "age": "25", "gender": "女", "ethnicity": "东方" },
  "bone_skin_shape_spirit": { "骨": "修", "皮": "淡", "形": "散", "神": "柔" },
  "camp": "抚慰者",
  "face": { "face_shape": "...", "brows_eyes": "...", "nose": "...", "lips": "...", "skin": "...", "hair": "..." },
  "body": { "head_to_body": "7.5头身", "shoulder_width": "1.8头", "build": "...", "posture": "..." },
  "outfit": { "silhouette": "...", "material": "...", "palette": "..." },
  "expression_light": { "gaze": "...", "expression": "...", "light": "..." },
  "identity_lock": { "locked": ["面部五官", "脸型结构", "身材比例", "发型发色"], "mutable": ["衣服", "配饰", "场景元素"] }
}
```

完整模板见 [`assets/character_card_template.json`](assets/character_card_template.json)。

---

## 适用场景 / 触发词

设计一个不撞脸的 AI 角色 · 生成角色三视图提示词 · AI 人像提示词 · 捏脸 / 角色设定 / 虚拟艺人 · 骨皮形神 / 麦橘 / 即梦 / flux krea / gpt-image 提示词。

---

## License

本 Skill 用于角色设计研究与出图实践，遵循对应出图平台的 API 服务条款使用。
