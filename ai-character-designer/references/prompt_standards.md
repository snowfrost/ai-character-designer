# 三模型提示词标准 + API 配置（核心）

> 本 Skill 的最终产物 = **详细的中英双语提示词**，分别遵循 gpt-image-2 / 即梦5.0pro / flux2krea 三种模型的提示词习惯。若已配置接口，可直接出图（肖像 / 全身 / 三视）。
> 生成器：`scripts/generate.py`。角色卡模板：`assets/character_card_template.json`。

---

## 0. 提示词装配顺序（三种模型共用骨架）

无论哪种模型，一条不撞脸的提示词都按以下顺序组装（GPT 用段落串起，即梦用中文条目，FLUX 用英文逗号标签）：

1. **主体 + 身份**：年龄段、性别、人种/族裔基调（如「东方女性」）。
2. **骨皮形神气质**（来自四问落点 → 见 §1 词库）。
3. **面部结构差异**（来自角色卡显式字段：脸型/眉眼/鼻/唇/皮肤/发型——**写差异不写美**）。
4. **身材与体态**（头身/肩宽/体型/体态，来自卡）。
5. **穿搭**（廓形 + 材质 + 配色，来自卡）。
6. **神态与光影**（眼神/表情克制点/光位/景深）。
7. **质量与风格标签**（按模型选，见 §2）。
8. **负向约束（negative）**：过度磨皮/蜡像/畸变/多余配饰（gpt-image-2 把负向写进正向句，即梦与 FLUX 用独立 negative 字段）。

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

## 2. 三模型提示词习惯对照

| 维度 | gpt-image-2（OpenAI） | 即梦5.0pro（字节 Seedream） | flux2krea（BFL FLUX.2 Krea） |
|---|---|---|---|
| 偏好语言 | 英文自然段落（中文亦可，英文更稳） | 中文结构化条目 + 描述 | 英文逗号分隔标签 |
| 负向支持 | 无独立字段，负向写进正向句 | 有 `negative_prompt` 字段 | 有 `negative_prompt` 字段 |
| 标志性质量词 | photorealistic, cinematic lighting, highly detailed | 写实摄影、电影感、自然光、细节丰富 | **RAW**, photorealistic, ultra-detailed, real skin texture |
| 肖像尺寸 | 1024x1024 | 1024x1024 | aspect_ratio "1:1" |
| 全身尺寸 | 1024x1536（竖） | 1024x1536 | "3:4" |
| 三视尺寸 | 1536x1024（16:9） | 1344x768 / 2048x1024 | "16:9" |
| 风格提示 | 句末加「without over-smoothed waxy skin, without extra accessories」 | 负向字段填「过度磨皮、蜡像感、畸变、多余配饰」 | 负向字段填「oversmoothed waxy skin, deformed, extra limbs, extra accessories」 |

### 2.1 gpt-image-2 段落模板（英文）
```
A [age] [ethnicity] woman with [bone-trait EN], [skin-trait EN], [shape-trait EN], [spirit-trait EN].
[face structure EN: face shape, brows/eyes, nose, lips, skin texture, hair].
[body EN: head-to-body ratio, shoulder width, posture]. Wearing [outfit EN: silhouette, material, palette].
[expression & light EN]. Photorealistic, cinematic soft lighting, highly detailed, shallow depth of field.
Maintain consistent facial identity; without over-smoothed waxy skin, without extra accessories, without deformity.
```
（同时给出中文等价段落，便于用户核对语义。）

### 2.2 即梦5.0pro 中文条目模板
```
一位[年龄段][族裔]女性，[骨相中文]，[皮相中文]，[形中文]，[神中文]。
脸型[...]、眉眼[...]、鼻[...]、唇[...]、皮肤[肌理中文]、发型[...]。
身材[头身/肩宽/体态]，身穿[廓形+材质+配色]。
[神态中文]、[光位中文]。写实摄影，电影感自然光，细节真实。
（negative_prompt：过度磨皮、蜡像假面、面部畸变、多余配饰、闪光灯死白）
```

### 2.3 flux2krea 英文标签模板
```
RAW, photorealistic, ultra-detailed, real skin texture, 8k,
[age] [ethnicity] woman, [bone EN tags], [skin EN tags], [shape EN tags], [spirit EN tags],
[face structure EN tags], [body EN tags], [outfit EN tags], [expression & light EN tags],
shallow depth of field, cinematic soft light
--negative-- oversmoothed waxy skin, deformed, extra limbs, extra accessories, distorted face
```

---

## 3. API 配置（可选，配置后直出图）

生成器读取 `config.json`（优先级：当前工作目录 → Skill 目录）与环境变量。未配置则不调用接口，只产出提示词文本。

### config.json 结构（示例，模型名以各家文档为准）
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
  },
  "jimeng_5_pro": {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key_env": "ARK_API_KEY",
    "model": "doubao-seedream-3-0-t2i-250715",
    "size_portrait": "1024x1024",
    "size_fullbody": "1024x1536",
    "size_threeview": "1344x768"
  },
  "flux2_krea": {
    "base_url": "https://api.bfl.ai/v1",
    "api_key_env": "BFL_API_KEY",
    "model": "flux-krea-pro",
    "size_portrait": "1:1",
    "size_fullbody": "3:4",
    "size_threeview": "16:9"
  }
}
```

### 调用约定（生成器实现要点）
- **gpt-image-2**：`POST {base_url}/images/generations`，body `{model, prompt, size, quality, n:1}`；响应 `data[0].b64_json` 或 `url` → 存盘。无独立 negative 字段（负向已并入 prompt）。
- **即梦5.0pro（火山方舟）**：`POST {base_url}/images/generations`，body `{model, prompt, negative_prompt, size, ...}`；按各家返回结构（url 或异步 task）取图。负向用独立字段。
- **flux2krea（BFL）**：`POST {base_url}/image/generations/{model}` 或 `/v1/images/generations`，body `{prompt, negative_prompt, aspect_ratio}`；BFL 常返回轮询 `id`，需轮询 `/v1/image/get/{id}` 取最终图。

> 注意：各厂家端点路径与模型字符串会随版本更新，config 中的 `model` / `base_url` 以你账号后台或官方文档为准；上面的字符串是常见形态，缺哪个填哪个。

---

## 4. 三个视图的提示词差异

- **肖像（portrait）**：正面、平视、均匀平光、干净纯色背景、聚焦面部特征（锚点图）。尺寸 1:1 / 1024²。
- **全身（fullbody）**：正面站姿、从头到脚、平视均匀光、纯色背景；提示词强制「面部特征与角色定义完全一致」+ 引用标准照。尺寸 3:4 / 1024×1536。
- **三视（three-view）**：一张图含「面部超大特写 + 全身正/侧/背」；所有视图同一角色、仅角度变；白底无阴影。尺寸 16:9。可用 `engineering.md` §7 的中文模板作底，叠加本卡结构描述。

---

## 5. 反「蜡像/千人一面」铁律（写进每条提示词）

- 皮肤：**保留毛孔/血色/轻微肌理**，拒绝「完美皮肤 / 8K / 超现实」类触发词（gpt-image 可适度，即梦/FLUX 尤其要避）。
- 结构：**必写差异**（脸型偏圆/偏方、内眼角高低、鼻翼宽窄、唇峰清晰与否、单眼皮/高颧骨等不完美细节）。
- 身份锁：后期变装时，提示词写明「不可改五官/脸型/身材/发色；仅改衣服/场景/配饰」。
