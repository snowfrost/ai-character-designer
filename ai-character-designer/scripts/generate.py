#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai-character-designer :: generate.py
把「角色定义卡」渲染成 三模型（gpt-image-2 / 即梦5.0pro / flux2krea）标准的 中英双语提示词；
若配置了接口（config.json + 环境变量），可直接出图：肖像 / 全身 / 三视。

用法：
  # 交互四问向导生成提示词
  python generate.py

  # 用角色卡生成（默认三模型 × 三视图）
  python generate.py --card character_card.json

  # 只出指定模型/视图
  python generate.py --card card.json --models jimeng_5_pro,flux2krea --views portrait,fullbody

  # 配置接口后直接出图
  python generate.py --card card.json --generate --out ./out

配置：当前目录或脚本目录下的 config.json（见 references/prompt_standards.md §3）。
"""

import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 1. 骨皮形神 → 中英特征词库（与 references/prompt_standards.md §1 一致）
# ---------------------------------------------------------------------------
BSS = {
    "骨": {
        "修": ("delicate ethereal bone structure, refined slim jaw, high-set cheekbones",
               "轻盈脱俗骨相、纤巧下颌线、颧骨走高清秀"),
        "敦": ("sturdy authoritative bone structure, broad square jaw, strong chin",
               "稳固敦实骨相、方颌、下巴比重有分量"),
    },
    "皮": {
        "浓": ("high-contrast striking features, bold vivid makeup, intense hair/lip/pupil color",
               "高对比浓颜、抓眼妆容、发瞳唇色浓烈"),
        "淡": ("soft low-contrast features, understated bare-skin makeup, pale luminous complexion",
               "低对比淡颜、裸妆感、脸裸白占比高"),
    },
    "形": {
        "聚": ("dense controlled feature arrangement, precise defined brows and lips",
               "五官缜密收拢、眉唇线条精致清晰"),
        "散": ("relaxed open feature spacing, soft loose arrangement",
               "五官松弛舒展、间距宽松自然"),
    },
    "神": {
        "锐": ("cool aloof gaze, sharp piercing eyes, distant untouchable vibe",
               "冷峻疏离眼神、锐利有距离感"),
        "柔": ("healing gentle gaze, soft warm eyes, approachable tender vibe",
               "治愈温柔眼神、暖意亲近"),
    },
}

# 中文结构字段 → 英文 词组翻译表（覆盖常见描述，未命中保留中文）
TRANS = {
    "鹅蛋脸": "oval face", "圆脸": "round face", "方圆脸": "square-round face",
    "瓜子脸": "heart-shaped face", "方脸": "square face", "长脸": "long face",
    "偏圆": "slightly round", "偏方": "slightly square", "清秀": "delicate",
    "上三下二": "parallelogram eye shape (top-heavy 3:2)", "单眼皮": "monolid",
    "双眼皮": "double eyelid", "内眼角略低": "slightly low inner corners",
    "内眼角高": "slightly high inner corners", "眶周折叠度": "orbital folding depth",
    "高颧骨": "high cheekbones", "鼻梁自然骨感": "naturally structured nose bridge",
    "鼻梁高": "high nose bridge", "鼻翼偏窄": "narrow nostrils", "鼻翼宽": "wide nostrils",
    "鼻基底饱满": "full nasal base", "海鸥线": "seagull-line nose tip",
    "双C线": "double-C lines", "唇薄": "thin lips", "厚唇": "full lips",
    "唇峰清晰": "defined cupid's bow", "唇峰柔和": "soft cupid's bow",
    "颏唇沟": "mentolabial fold", "冷白": "cool fair skin", "哑光": "matte texture",
    "保留毛孔": "visible pores", "小麦": "wheatish skin tone", "雀斑": "freckles",
    "血色": "natural blush", "乌黑": "jet-black", "及肩": "shoulder-length",
    "及腰": "waist-length", "直发": "straight hair", "卷发": "curly hair",
    "软发": "soft flyaway hairs", "蓬松": "voluminous", "通透": "luminous",
    "头身": "head-to-body ratio", "肩宽": "shoulder width", "匀称": "balanced",
    "纤": "slim", "挺拔": "upright posture", "松弛": "relaxed", "微侧": "slightly turned",
    "真丝": "silk", "亚麻": "linen", "羊毛": "wool", "蕾丝": "lace", "皮革": "leather",
    "柔光": "soft sheen", "垂坠": "draping", "修身": "fitted", "落肩": "drop-shoulder",
    "宽松": "loose", "侧窗光": "soft side window light", "浅景深": "shallow depth of field",
    "低对比": "low contrast", "平光": "flat even lighting", "逆光": "backlight",
    "米白": "off-white", "浅驼": "light camel",
}


def to_en(zh: str) -> str:
    """把中文描述尽量转成英文；未命中词保留中文（可接受）。"""
    if not zh:
        return ""
    out = zh
    # 长词优先
    for k in sorted(TRANS, key=len, reverse=True):
        if k in out:
            out = out.replace(k, TRANS[k])
    return out


# ---------------------------------------------------------------------------
# 2. 角色卡 → 组件字符串
# ---------------------------------------------------------------------------
def load_card(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def default_card():
    return {
        "name": "未命名角色",
        "subject": {"age": "25", "gender": "女", "ethnicity": "东方"},
        "bone_skin_shape_spirit": {"骨": "修", "皮": "淡", "形": "散", "神": "柔"},
        "camp": "抚慰者",
        "face": {"face_shape": "鹅蛋脸", "brows_eyes": "眼型上三下二", "nose": "鼻梁自然骨感、鼻翼偏窄",
                 "lips": "唇薄、唇峰清晰", "skin": "冷白哑光、保留毛孔", "hair": "乌黑及肩直发"},
        "body": {"head_to_body": "7.5头身", "shoulder_width": "1.8头", "build": "匀称偏纤", "posture": "松弛微侧"},
        "outfit": {"silhouette": "修身落肩", "material": "真丝", "palette": "米白+浅驼"},
        "expression_light": {"gaze": "温柔平静", "expression": "克制微微笑意", "light": "侧窗光、浅景深、低对比"},
        "identity_lock": {"locked": ["面部五官", "脸型结构", "身材比例", "发型发色"],
                          "mutable": ["衣服", "配饰", "场景元素"]},
    }


def interactive_card():
    print("== 骨皮形神 四问向导 ==")
    bone = input("骨（视觉重心）修/敦：") or "修"
    skin = input("皮（视觉强度）浓/淡：") or "淡"
    shape = input("形（视觉密度）聚/散：") or "散"
    spirit = input("神（视觉触感）锐/柔：") or "柔"
    name = input("角色名/代号：") or "未命名角色"
    age = input("年龄段（如 25）：") or "25"
    gender = input("性别（女/男）：") or "女"
    face_shape = input("脸型（如 鹅蛋脸偏圆）：") or "鹅蛋脸"
    card = default_card()
    card.update({
        "name": name,
        "subject": {"age": age, "gender": gender, "ethnicity": "东方"},
        "bone_skin_shape_spirit": {"骨": bone, "皮": skin, "形": shape, "神": spirit},
        "face": {"face_shape": face_shape, "brows_eyes": "眼型上三下二",
                 "nose": "鼻梁自然骨感、鼻翼偏窄", "lips": "唇薄、唇峰清晰",
                 "skin": "冷白哑光、保留毛孔", "hair": "乌黑及肩直发"},
    })
    return card


def components(card):
    bss = card.get("bone_skin_shape_spirit", {})
    bone_en, bone_zh = BSS["骨"].get(bss.get("骨", "修"), BSS["骨"]["修"])
    skin_en, skin_zh = BSS["皮"].get(bss.get("皮", "淡"), BSS["皮"]["淡"])
    shape_en, shape_zh = BSS["形"].get(bss.get("形", "散"), BSS["形"]["散"])
    spirit_en, spirit_zh = BSS["神"].get(bss.get("神", "柔"), BSS["神"]["柔"])

    sub = card.get("subject", {})
    eth_zh = sub.get("ethnicity", "东方")
    eth_en = {"东方": "East Asian", "欧美": "European", "混血": "mixed-race"}.get(eth_zh, eth_zh)
    sub_zh = f"一位{sub.get('age','')}岁{eth_zh}{sub.get('gender','女')}性"
    sub_en = f"a {sub.get('age','')}-year-old {eth_en} {('woman' if sub.get('gender','女')=='女' else 'man')}"

    face = card.get("face", {})
    face_zh = "，".join([v for v in face.values() if v])
    face_en = "; ".join([to_en(v) for v in face.values() if v])

    body = card.get("body", {})
    body_zh = "，".join([v for v in body.values() if v])
    body_en = "; ".join([to_en(v) for v in body.values() if v])

    out = card.get("outfit", {})
    out_zh = "身穿" + "、".join([f"{v}" for v in out.values() if v])
    out_en = "wearing " + ", ".join([to_en(v) for v in out.values() if v])

    el = card.get("expression_light", {})
    el_zh = "、".join([v for v in el.values() if v])
    el_en = "; ".join([to_en(v) for v in el.values() if v])

    return {
        "sub_zh": sub_zh, "sub_en": sub_en,
        "bone_zh": bone_zh, "bone_en": bone_en,
        "skin_zh": skin_zh, "skin_en": skin_en,
        "shape_zh": shape_zh, "shape_en": shape_en,
        "spirit_zh": spirit_zh, "spirit_en": spirit_en,
        "face_zh": face_zh, "face_en": face_en,
        "body_zh": body_zh, "body_en": body_en,
        "out_zh": out_zh, "out_en": out_en,
        "el_zh": el_zh, "el_en": el_en,
    }


# ---------------------------------------------------------------------------
# 3. 三模型提示词渲染
# ---------------------------------------------------------------------------
NEG_JIMENG = "过度磨皮、蜡像假面、面部畸变、多余配饰、闪光灯死白、畸形肢体"
NEG_FLUX = "oversmoothed waxy skin, deformed, extra limbs, extra accessories, distorted face, plastic doll look"
NEG_GPT_INLINE = "without over-smoothed waxy skin, without extra accessories, without deformity, without plastic-doll look"

VIEW_ZH = {
    "portrait": "正面平视、均匀平光、干净纯色背景、聚焦面部特征（角色锚点图）",
    "fullbody": "正面站姿、从头到脚完整入镜、平视均匀光、纯色背景，面部特征与角色定义完全一致",
    "threeview": "一张图含面部超大特写+全身正/侧/背三视图，所有视图同一角色仅角度变化，白底无阴影",
}
VIEW_EN = {
    "portrait": "front-facing, even flat lighting, clean solid-color background, focused on facial features (character anchor shot)",
    "fullbody": "full-body front-standing pose, head to toe, even lighting, solid background, facial features perfectly consistent with the character definition",
    "threeview": "one sheet with an extra-large facial close-up plus full-body front/side/back views, same character only angle changes, white background no shadow",
}


def render(card, view):
    c = components(card)
    if view not in VIEW_ZH:
        raise ValueError("view must be portrait/fullbody/threeview")

    # --- 中文（共用骨架，三模型同义，按习惯微调）---
    zh_core = (f"{c['sub_zh']}，{c['bone_zh']}，{c['skin_zh']}，{c['shape_zh']}，{c['spirit_zh']}。"
               f"{c['face_zh']}。{c['body_zh']}。{c['out_zh']}。"
               f"{c['el_zh']}。{VIEW_ZH[view]}。写实摄影质感、自然光、细节真实、保留皮肤肌理与血色。")

    # --- gpt-image-2（英文段落，负向并入）---
    gpt_en = (f"{c['sub_en']} with {c['bone_en']}, {c['skin_en']}, {c['shape_en']}, {c['spirit_en']}. "
              f"Face: {c['face_en']}. Body: {c['body_en']}. {c['out_en']}. "
              f"Expression & light: {c['el_en']}. {VIEW_EN[view]}. "
              f"Photorealistic, cinematic soft lighting, highly detailed, shallow depth of field. "
              f"Maintain consistent facial identity; {NEG_GPT_INLINE}.")

    # --- 即梦5.0pro（中文条目 + 独立 negative）---
    jimeng_zh = zh_core
    jimeng_en = (f"{c['sub_en']}, {c['bone_en']}, {c['skin_en']}, {c['shape_en']}, {c['spirit_en']}. "
                 f"{c['face_en']}. {c['body_en']}. {c['out_en']}. {c['el_en']}. {VIEW_EN[view]}. "
                 f"realistic photography, natural light, fine detail, real skin texture.")

    # --- flux2krea（英文标签，RAW 开头，独立 negative）---
    flux_en = ("RAW, photorealistic, ultra-detailed, real skin texture, 8k, "
               f"{c['sub_en']}, {c['bone_en']}, {c['skin_en']}, {c['shape_en']}, {c['spirit_en']}, "
               f"{c['face_en']}, {c['body_en']}, {c['out_en']}, {c['el_en']}, {VIEW_EN[view]}, "
               f"shallow depth of field, cinematic soft light")
    flux_zh = zh_core

    return {
        "gpt_image_2": {"zh": zh_core, "en": gpt_en, "negative": None},
        "jimeng_5_pro": {"zh": jimeng_zh, "en": jimeng_en, "negative": NEG_JIMENG},
        "flux2_krea": {"zh": flux_zh, "en": flux_en, "negative": NEG_FLUX},
    }


# ---------------------------------------------------------------------------
# 4. API 出图（可选）
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "gpt_image_2": {"base_url": "https://api.openai.com/v1", "api_key_env": "OPENAI_API_KEY",
                    "model": "gpt-image-2", "size_portrait": "1024x1024",
                    "size_fullbody": "1024x1536", "size_threeview": "1536x1024", "quality": "high"},
    "jimeng_5_pro": {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "api_key_env": "ARK_API_KEY",
                     "model": "doubao-seedream-3-0-t2i-250715", "size_portrait": "1024x1024",
                     "size_fullbody": "1024x1536", "size_threeview": "1344x768"},
    "flux2_krea": {"base_url": "https://api.bfl.ai/v1", "api_key_env": "BFL_API_KEY",
                   "model": "flux-krea-pro", "size_portrait": "1:1", "size_fullbody": "3:4", "size_threeview": "16:9"},
}
SIZE_KEY = {"portrait": "size_portrait", "fullbody": "size_fullbody", "threeview": "size_threeview"}


def load_config(explicit=None):
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.append(os.path.join(os.getcwd(), "config.json"))
    candidates.append(os.path.join(HERE, "..", "config.json"))
    candidates.append(os.path.join(HERE, "config.json"))
    for p in candidates:
        if p and os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                cfg = json.load(f)
            merged = {k: {**DEFAULT_CONFIG.get(k, {}), **v} for k, v in cfg.items()}
            for k in DEFAULT_CONFIG:
                merged.setdefault(k, DEFAULT_CONFIG[k])
            return merged
    return DEFAULT_CONFIG


def call_api(model_key, prompt_obj, view, out_dir, config):
    try:
        import requests
    except ImportError:
        print("  [跳过] 未安装 requests，无法调用接口（pip install requests）")
        return None
    cfg = config[model_key]
    api_key = os.environ.get(cfg.get("api_key_env", ""), "")
    if not api_key:
        print(f"  [跳过] 未设置环境变量 {cfg.get('api_key_env')}，不出图")
        return None
    size = cfg.get(SIZE_KEY.get(view, "size_portrait"), "1024x1024")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    size_param = {"size": size} if model_key != "flux2_krea" else {"aspect_ratio": size}

    if model_key == "gpt_image_2":
        url = f"{cfg['base_url'].rstrip('/')}/images/generations"
        body = {"model": cfg["model"], "prompt": prompt_obj["en"],
                "size": size, "quality": cfg.get("quality", "high"), "n": 1}
    elif model_key == "jimeng_5_pro":
        url = f"{cfg['base_url'].rstrip('/')}/images/generations"
        body = {"model": cfg["model"], "prompt": prompt_obj["zh"],
                "negative_prompt": prompt_obj["negative"], **size_param}
    else:  # flux2_krea
        url = f"{cfg['base_url'].rstrip('/')}/image/generations/{cfg['model']}"
        body = {"prompt": prompt_obj["en"], "negative_prompt": prompt_obj["negative"], **size_param}

    try:
        r = requests.post(url, headers=headers, json=body, timeout=120)
        if not r.ok:
            print(f"  [接口错误] {model_key} {view}: HTTP {r.status_code} {r.text[:200]}")
            return None
        data = r.json()
        # 适配多种返回：b64_json / url / 轮询 id
        img_b64 = None
        img_url = None
        if model_key == "gpt_image_2":
            item = (data.get("data") or [{}])[0]
            img_b64 = item.get("b64_json")
            img_url = item.get("url")
        else:
            img_url = data.get("url") or (data.get("data") or [{}])[0].get("url")
            img_b64 = data.get("b64_json") or (data.get("data") or [{}])[0].get("b64_json")
            task_id = data.get("id") or data.get("task_id")
            if task_id and not (img_url or img_b64):
                img_url = poll_bfl(requests, cfg, task_id)
        if img_b64:
            fn = os.path.join(out_dir, f"{model_key}__{view}.png")
            with open(fn, "wb") as f:
                import base64
                f.write(base64.b64decode(img_b64))
            print(f"  [已出图] {fn}")
            return fn
        if img_url:
            fn = os.path.join(out_dir, f"{model_key}__{view}.png")
            with open(fn, "wb") as f:
                f.write(requests.get(img_url, timeout=60).content)
            print(f"  [已出图] {fn}")
            return fn
        print(f"  [无图返回] {model_key} {view}: {str(data)[:200]}")
        return None
    except Exception as e:
        print(f"  [调用异常] {model_key} {view}: {e}")
        return None


def poll_bfl(requests, cfg, task_id):
    import time
    url = f"{cfg['base_url'].rstrip('/')}/image/get/{task_id}"
    headers = {"Authorization": f"Bearer {os.environ.get(cfg.get('api_key_env',''))}"}
    for _ in range(30):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            d = r.json()
            if d.get("status") == "Ready":
                return d.get("result", {}).get("sample") or d.get("url")
        except Exception:
            pass
        time.sleep(3)
    return None


# ---------------------------------------------------------------------------
# 5. 主流程
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="AI 角色打造提示词生成器（三模型标准）")
    ap.add_argument("--card", help="角色卡 JSON 路径")
    ap.add_argument("--desc", help="自由描述（暂仅作备注，建议用 --card 或交互向导）")
    ap.add_argument("--models", default="gpt_image_2,jimeng_5_pro,flux2_krea",
                    help="模型列表，逗号分隔")
    ap.add_argument("--views", default="portrait,fullbody,threeview", help="视图列表")
    ap.add_argument("--generate", action="store_true", help="配置接口后直接出图")
    ap.add_argument("--out", default="./character_output", help="输出目录")
    ap.add_argument("--config", help="config.json 路径")
    args = ap.parse_args()

    if args.card:
        card = load_card(args.card)
    else:
        card = interactive_card()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    views = [v.strip() for v in args.views.split(",") if v.strip()]
    os.makedirs(args.out, exist_ok=True)

    results = {}
    for view in views:
        results[view] = render(card, view)

    # 写提示词（JSON + MD）
    with open(os.path.join(args.out, "prompts.json"), "w", encoding="utf-8") as f:
        json.dump({"card": card, "prompts": results}, f, ensure_ascii=False, indent=2)

    md = [f"# 角色提示词 · {card.get('name','未命名')}", "", "## 角色定义卡", "```json",
          json.dumps(card, ensure_ascii=False, indent=2), "```", ""]
    for view in views:
        md.append(f"## 视图：{view}")
        for mk in models:
            p = results[view][mk]
            md.append(f"### {mk}")
            md.append(f"- **中文**：{p['zh']}")
            md.append(f"- **English**：{p['en']}")
            if p["negative"]:
                md.append(f"- **negative**：{p['negative']}")
            md.append("")
    with open(os.path.join(args.out, "prompts.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"\n[完成] 提示词已写出：{os.path.join(args.out,'prompts.md')} / prompts.json")

    if args.generate:
        config = load_config(args.config)
        print("[出图模式] 调用已配置接口…")
        for view in views:
            for mk in models:
                print(f"-> {mk} / {view}")
                call_api(mk, results[view][mk], view, args.out, config)


if __name__ == "__main__":
    main()
