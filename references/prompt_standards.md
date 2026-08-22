# gpt-image-2 提示词标准 + API 配置（核心）

> 本 Skill 的最终产物 = **gpt-image-2 标准的中英双语提示词**（中英分开，先中文三视图、再英文）。
> 若已配置接口（`OPENAI_API_KEY`），可直接出图（肖像 / 全身 / 三视）。
> 生成器：`scripts/generate.py`。角色卡模板：`assets/character_card_template.json`。

---

## 0. 提示词装配顺序（gpt-image-2 统一骨架）

一条不撞脸的提示词按以下顺序组装（英文用段落串起，同时给中文等价段落便于核对）：

1. **主体 + 身份**：年龄段、性别、人种/族裔基调（如「东方女性」）、职业、时代。
2. **骨皮形神气质**（来自四问落点 → 见 §1 词库）。
3. **面部结构差异**（来自角色卡显式字段：脸型/眉眼/鼻/唇/皮肤/发型——**写差异不写美**）。
4. **身材与体态**（头身/肩宽/体型/体态，来自卡）。
5. **穿搭**（廓形 + 材质 + 配色，来自卡）。
6. **神态与光影**（眼神/表情克制点/光位/景深）。
7. **质量与风格标签**（见 §2）。
8. **负向约束（negative）**：gpt-image-2 无独立 negative 字段，负向写进正向句（英文 `without ...` / 中文「不要 ...」）。

---

## 1. 骨皮形神 → 具体特征词库（中英对照）

| 旋钮 | 落点 | 英文（嵌入提示词） | 中文（嵌入提示词） |
|---|---|---|---|
| 骨 | 修 | delicate ethereal bone structure, refined slim jaw, high-set cheekbones | 轻盈脱俗骨相、纤巧下颌线、颧骨走高清秀 |
| 骨 | 敦 | sturdy authoritative bone structure, broad square jaw, strong chin | 稳固敦实骨相、方颌、下巴比重有分量 |
| 皮 | 浓 | high-contrast striking features, bold vivid makeup, intense hair/lip/pupil color | 高对比浓颜、抓眼妆容、发瞳唇色浓烈 |
| 皮 | 淡 | soft low-contrast features, understated bare-skin makeup, pale luminous complexion | 低对比淡颜、裸妆感、脸裸白占比高 |
| 形 | 聚 | dense controlled feature arrangement, precise defined brows and lips | 五官缜密收拢、眉唇线条精致清晰 |
| 形 | 散 | relaxed open feature spacing, soft loose arrangement | 五官松弛舒展、间距宽松自然 |
| 神 | 锐 | cool aloof gaze, sharp piercing eyes, distant untouchable vibe | 冷峻疏离眼神、锐利有距离感 |
| 神 | 柔 | healing gentle gaze, soft warm eyes, approachable tender vibe | 治愈温柔眼神、暖意亲近 |

> 四大阵营气质组合：凌越者=浓+锐（冷艳/权威）；造梦者=浓+柔（风情/元气）；洞察者=淡+锐（高智/清冷）；抚慰者=淡+柔（温婉/治愈）。骨(修/敦)×形(聚/散) 再细化到 16 格。

## 2. gpt-image-2 提示词习惯

| 维度 | gpt-image-2（OpenAI） |
|---|---|
| 偏好语言 | 英文自然段落（中文亦可，英文更稳）；中英各出一份便于核对 |
| 负向支持 | **无独立 negative 字段**，负向写进正向句 |
| 标志性质量词 | photorealistic, cinematic lighting, highly detailed |
| 肖像尺寸 | 1024x1024 |
| 全身尺寸 | 1024x1536（竖） |
| 三视尺寸 | 1536x1024（16:9） |
| 风格提示 | 句末加「without over-smoothed waxy skin, without extra accessories, without deformity」 |

### 2.1 英文段落模板
```
A [age] [ethnicity] [woman/man], [occupation], [era] with [bone-trait EN], [skin-trait EN], [shape-trait EN], [spirit-trait EN].
Face: [face structure EN: face shape, brows/eyes, nose, lips, skin texture, hair].
Body: [body EN: head-to-body ratio, shoulder width, posture]. Wearing [outfit EN: silhouette, material, palette].
Expression & light: [expression & light EN]. [view spec EN].
Photorealistic, cinematic soft lighting, highly detailed, shallow depth of field.
Maintain consistent facial identity; without over-smoothed waxy skin, without extra accessories, without deformity.
```

### 2.2 中文段落模板（与英文同语义）
```
一位[年龄段][族裔][性别]，职业/身份：[职业]，时代背景：[时代]，[骨相中文]，[皮相中文]，[形中文]，[神中文]。
[脸型]、[眉眼]、[鼻]、[唇]、[皮肤]、[发型]。
[头身/肩宽/体型/体态]，身穿[廓形+材质+配色]。
[神态]、[光位]。[视图要求中文]。写实摄影质感、自然光、细节真实、保留皮肤肌理与血色。
保持面部特征一致；不要过度磨皮蜡像感，不要多余配饰，不要面部畸变。
```

---

## 3. API 配置（可选，配置后直出图）

生成器读取 `config.json`（优先级：当前工作目录 → Skill 目录）与环境变量 `OPENAI_API_KEY`。未配置则不调用接口，只产出提示词文本。

### config.json 结构（示例）
```json
{
  "gpt_image_2": {
    "base_url": "https://api.openai.com/v1",
    "api_key_env": "OPENAI_API_KEY",
    "model": "gpt-image-2",
    "size_portrait": "1024x1024",
    "size_fullbody": "1024x1536",
    "size_threeview": "1536x1024",
    "quality": "high"
  }
}
```

### 调用约定
- **gpt-image-2**：`POST {base_url}/images/generations`，body `{model, prompt, size, quality, n:1}`；响应 `data[0].b64_json` 或 `url` → 存盘。无独立 negative 字段（负向已并入 prompt）。

> 注意：端点路径与模型字符串会随版本更新，config 中的 `model` / `base_url` 以你账号后台或官方文档为准；上面的字符串是常见形态，缺哪个填哪个。

---

## 4. 三个视图的提示词差异

- **肖像（portrait）**：正面、平视、均匀平光、干净纯色背景、聚焦面部特征（锚点图）。尺寸 1024×1024。
- **全身（fullbody）**：正面站姿、从头到脚、平视均匀光、纯色背景；提示词强制「面部特征与角色定义完全一致」+ 引用标准照。尺寸 1024×1536。
- **三视（three-view）**：一张图含「面部超大特写 + 全身正/侧/背」；所有视图同一角色、仅角度变；白底无阴影。尺寸 1536×1024（16:9）。可用 `engineering.md` §7 的中文模板作底，叠加本卡结构描述。

---

## 5. 反「蜡像/千人一面」铁律（写进每条提示词）

- 皮肤：**保留毛孔/血色/轻微肌理**，拒绝「完美皮肤 / 8K / 超现实」类触发词。
- 结构：**必写差异**（脸型偏圆/偏方、内眼角高低、鼻翼宽窄、唇峰清晰与否、单眼皮/高颧骨等不完美细节）。
- 身份锁：后期变装时，提示词写明「不可改五官/脸型/身材/发色；仅改衣服/场景/配饰」。
