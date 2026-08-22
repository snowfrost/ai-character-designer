#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai-character-designer :: generate.py
把「角色定义卡」渲染成 三模型（gpt-image-2 / 即梦5.0pro / flux2krea）标准的 中英双语提示词；
若配置了接口（config.json + 环境变量），可直接出图：肖像 / 全身 / 三视。

交互流程（对话式捏脸，先问后做，没想法才自动）：
  第 0 步  开场：摸清用户有没有想法
  第 1 步  角色基本信息：性别 / 年龄 / 国籍族裔 / 身份职业 / 时代服装 / 性格
  第 2 步  骨皮形神四问（大白话二选一）→ 骨(修/敦) 皮(浓/淡) 形(聚/散) 神(锐/柔)
  第 3 步  16 型定位确认（四维 → 阵营 → 类型名）
  第 4 步  面部结构捏脸（逐项定脸型/眉眼/鼻/唇/皮肤/发型，写差异不写美）
  第 5 步  渲染三模型提示词

用法：
  # 交互向导（推荐）
  python generate.py

  # 自动模式（用户没想法，按职业/时代推导，仍会先问基本信息）
  python generate.py --auto

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
import random

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

# 四大阵营（皮 × 神）→ 16 型细格（骨 × 形）→ 类型名
CAMP_16 = {
    "凌越者（浓×锐）": {"修聚": "犀利精英", "修散": "冷艳前卫", "敦聚": "威严强势", "敦散": "庄重豪迈"},
    "造梦者（浓×柔）": {"修聚": "惊艳风情", "修散": "浪漫亲和", "敦聚": "活力热烈", "敦散": "丰盈柔媚"},
    "洞察者（淡×锐）": {"修聚": "精密理智", "修散": "清冷极简", "敦聚": "严谨秩序", "敦散": "坚韧简约"},
    "抚慰者（淡×柔）": {"修聚": "纯净温婉", "修散": "恬静治愈", "敦聚": "亲切朴实", "敦散": "温和敦厚"},
}
CAMP_LOOKUP = {  # (皮, 神) → 阵营名
    ("浓", "锐"): "凌越者（浓×锐）",
    ("浓", "柔"): "造梦者（浓×柔）",
    ("淡", "锐"): "洞察者（淡×锐）",
    ("淡", "柔"): "抚慰者（淡×柔）",
}


def type16_of(bss):
    """由四维落点返回 (阵营, 类型名)。"""
    skin = bss.get("皮", "淡")
    spirit = bss.get("神", "柔")
    camp = CAMP_LOOKUP.get((skin, spirit), "抚慰者（淡×柔）")
    grid = f"{bss.get('骨', '修')}{bss.get('形', '散')}"
    name = CAMP_16[camp].get(grid, "自定义")
    return camp, name


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
    "纤细": "slender", "挺拔": "upright posture", "松弛": "relaxed", "微侧": "slightly turned",
    "真丝": "silk", "亚麻": "linen", "羊毛": "wool", "蕾丝": "lace", "皮革": "leather",
    "柔光": "soft sheen", "垂坠": "draping", "修身": "fitted", "落肩": "drop-shoulder",
    "宽松落肩": "loose drop-shoulder", "宽松": "loose", "侧窗光": "soft side window light",
    "浅景深": "shallow depth of field", "低对比": "low contrast", "平光": "flat even lighting",
    "逆光": "backlight", "米白": "off-white", "浅驼": "light camel",
    # ---- 补全：常见角色卡词条（2026-08 扩充）----
    "婴儿肥": "baby fat", "颧骨柔和": "soft cheekbones", "颧骨适度": "moderate cheekbones",
    "不突出": "not prominent", "杏眼": "almond-shaped eyes", "双眼皮偏窄": "narrow double eyelids",
    "内眼角微垂": "slightly drooping inner eye corners", "眉形平弯": "gently curved brows",
    "线条清晰": "clean defined lines", "五官缜密收拢": "dense refined feature arrangement",
    "五官松弛舒展": "relaxed open feature spacing", "鼻梁纤细": "slender nose bridge",
    "鼻头圆润微翘": "rounded slightly upturned nose tip", "唇偏厚": "fuller lips",
    "下唇饱满": "full lower lip", "嘴角自然上扬": "naturally upturned mouth corners",
    "自带笑意": "naturally smiling", "暖白肤色": "warm fair skin", "哑光质感": "matte texture",
    "细小雀斑": "tiny freckles", "自然淡血色": "natural light blush", "深栗棕": "deep chestnut brown",
    "微卷发": "slightly wavy hair", "空气感刘海": "airy bangs", "脸颊碎发": "wispy face-framing strands",
    "发丝柔亮": "softly lustrous hair", "匀称偏纤": "balanced and slim", "匀称挺拔": "balanced and upright",
    "挺拔但松弛": "upright yet relaxed", "姿态自然": "natural posture", "棉麻针织": "cotton-linen knit",
    "米杏": "cream", "奶白": "milky white", "明亮带笑": "bright with a smile",
    "眼神温暖不压迫": "warm non-intrusive gaze", "柔光侧窗": "soft side window light",
    "长脸偏方": "long slightly square face", "下颌线清晰": "defined jawline", "有分量": "with weight",
    "内双偏单": "inner-double lid leaning monolid", "眼型略圆": "slightly rounded eyes",
    "眉形平缓略粗": "flat slightly thick brows", "眉距稍宽": "slightly wide brow spacing",
    "鼻梁高直": "high straight nose bridge", "鼻翼略宽": "slightly wide nostrils",
    "鼻头圆润": "rounded nose tip", "唇中等偏薄": "medium-thin lips", "唇峰柔和": "soft cupid's bow",
    "唇角平直": "straight mouth corners", "轻微笑意": "faint smile", "暖调自然肤色": "warm natural skin tone",
    "轻微青影胡茬感": "slight stubble shadow", "乌黑短发": "jet-black short hair", "侧分": "side part",
    "前额碎发": "wispy forehead strands", "发质硬挺": "firm hair texture", "修身挺括": "fitted and crisp",
    "衬衫棉质": "cotton shirt fabric", "深灰蓝": "dark grey-blue", "平静温和": "calm and gentle",
    "目光带暖意": "gaze with warmth", "神情克制": "restrained expression", "微带笑意": "slight smile",
    "暖调": "warm-toned", "7头身": "7 heads tall", "7.5头身": "7.5 heads tall",
    "1.6头": "1.6 heads wide", "2头": "2 heads wide",
    # ---- 新：时代/职业/性格 → 穿搭与神态词条 ----
    "古装": "ancient Chinese costume", "汉服": "Hanfu", "唐装": "Tang-style costume",
    "民国": "Republic-era Chinese", "旗袍": "qipao", "长衫": "changshan",
    "现代": "modern", "都市": "urban", "未来": "futuristic", "科幻": "sci-fi",
    "架空": "fantasy setting", "武侠": "wuxia", "将军": "general", "剑客": "swordsman",
    "侠客": "wandering swordsman", "刺客": "assassin", "侦探": "detective",
    "医生": "doctor", "总裁": "CEO", "爱豆": "idol", "画家": "painter",
    "学生": "student", "教师": "teacher", "护士": "nurse", "女王": "queen",
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
        "subject": {"gender": "女", "age": "25", "ethnicity": "东方",
                    "occupation": "画家", "era": "民国", "personality": "外冷内热的独立女性"},
        "bone_skin_shape_spirit": {"骨": "修", "皮": "淡", "形": "散", "神": "柔"},
        "camp": "抚慰者（淡×柔）",
        "type16": "恬静治愈",
        "face": {"face_shape": "鹅蛋脸（偏圆）", "brows_eyes": "眉平、眼型上三下二、内眼角略低",
                 "nose": "鼻梁自然骨感、鼻翼偏窄、鼻基底饱满", "lips": "唇薄、唇峰清晰",
                 "skin": "冷白自然肤色、哑光质感、保留轻微毛孔", "hair": "乌黑及肩直发、脸颊留细碎软发"},
        "body": {"head_to_body": "7.5头身", "shoulder_width": "1.8头", "build": "匀称偏纤", "posture": "松弛自然、身体微侧"},
        "outfit": {"silhouette": "修身落肩", "material": "真丝柔光", "palette": "米白+浅驼"},
        "expression_light": {"gaze": "温柔平静、眼神不夸张", "expression": "克制微微笑意", "light": "柔和侧窗光、浅景深、低对比"},
        "identity_lock": {"locked": ["面部五官", "脸型结构", "身材比例", "发型发色"],
                          "mutable": ["衣服", "配饰", "场景元素"]},
    }


# ---- 面部结构默认建议（按骨皮形神四维推导，写差异不写美）----
FACE_DEFAULTS = {
    "骨": {"修": {"face_shape": "鹅蛋脸（偏瓜子、颧骨走高清秀）"},
           "敦": {"face_shape": "方圆脸（下颌线清晰、有分量）"}},
    "皮": {"浓": {"brows_eyes": "眉眼量感大、浓眉、眼神抓人", "skin": "白皙亮泽、妆感浓、唇色发色鲜明"},
           "淡": {"brows_eyes": "眉眼清淡自然、眼型上三下二", "skin": "自然肌理、哑光、保留毛孔血色"}},
    "形": {"聚": {"brows_eyes": "五官紧凑、眉唇线条精致清晰", "nose": "鼻梁高直、鼻翼偏窄"},
           "散": {"brows_eyes": "五官舒展、间距宽松自然", "nose": "鼻梁自然骨感、鼻翼适中"}},
    "神": {"锐": {"brows_eyes": "眼型细长、眼神冷冽有距离", "lips": "唇偏薄、唇线利落"},
           "柔": {"brows_eyes": "眼型圆润、眼神温柔亲近", "lips": "唇偏饱满、唇峰柔和"}},
}


def face_defaults(bss):
    """由四维合成一份默认面部结构（后合并进角色卡 face 字段）。"""
    merged = {}
    for dim, val in bss.items():
        for k, v in FACE_DEFAULTS.get(dim, {}).get(val, {}).items():
            merged[k] = v
    merged.setdefault("face_shape", "鹅蛋脸")
    merged.setdefault("brows_eyes", "眼型上三下二")
    merged.setdefault("nose", "鼻梁自然骨感、鼻翼偏窄")
    merged.setdefault("lips", "唇薄、唇峰清晰")
    merged.setdefault("skin", "自然肤色、保留毛孔与血色")
    merged.setdefault("hair", "乌黑直发、发丝自然有光泽")
    return merged


# ---------------------------------------------------------------------------
# 3. 交互向导（对话式捏脸：先问，后做；没想法才自动）
# ---------------------------------------------------------------------------
def ask(prompt, default=""):
    """带默认值的提问；直接回车用默认。"""
    try:
        ans = input(prompt).strip()
    except EOFError:
        ans = ""
    return ans or default


def ask_choice(prompt, opts, default=None):
    """二选一（或更多）；输入序号或文字；无法解析时给默认。"""
    lines = "\n  ".join(f"{i}. {o}" for i, o in enumerate(opts, 1))
    while True:
        ans = ask(f"{prompt}\n  {lines}\n  (回车默认: {default}) > ")
        if not ans:
            return default
        if ans.isdigit() and 1 <= int(ans) <= len(opts):
            return opts[int(ans) - 1]
        for o in opts:
            if ans in o or o in ans:
                return o
        print(f"  无法识别「{ans}」，请输入序号或选项文字。")


def auto_bss(subject):
    """自动模式：按性别/职业/时代推导骨皮形神，并给出理由。"""
    occ = (subject.get("occupation") or "").lower()
    era = (subject.get("era") or "").lower()
    per = (subject.get("personality") or "").lower()
    gender = subject.get("gender", "女")
    text = f"{occ}{era}{per}"

    rules = [
        # 古装/武侠/权谋
        (["将军", "帝王", "女王", "权臣", "霸道", "总裁", "ceo"], ("敦", "浓", "聚", "锐")),
        (["侠客", "剑客", "刺客", "侦探", "特工", "杀手"], ("修", "浓", "散", "锐")),
        (["医生", "律师", "教授", "学者", "研究员", "工程师", "程序员", "博士"], ("修", "淡", "聚", "锐")),
        (["护士", "幼师", "教师", "村", "邻家", "妈妈", "奶奶"], ("修", "淡", "散", "柔")),
        (["爱豆", "idol", "偶像", "舞者", "歌手", "明星", "模特", "元气"], ("修", "浓", "散", "柔")),
        (["女王", "御姐", "女强", "明艳", "港风"], ("敦", "浓", "聚", "柔")),
        (["清冷", "高冷", "寡言", "极简", "禁欲"], ("修", "淡", "散", "锐")),
        (["温暖", "治愈", "温柔", "软萌", "奶"], ("修", "淡", "散", "柔")),
    ]
    reason = ""
    for keys, bss in rules:
        if any(k in text for k in keys):
            reason = f"职业/时代/性格含「{keys[0]}」类设定"
            return dict(zip(["骨", "皮", "形", "神"], bss)), reason

    # 兜底：按性别给一个中等默认
    bss = {"骨": "修", "皮": "浓" if gender == "女" else "淡", "形": "散", "神": "柔"}
    reason = "没有命中强关键词，给了通用默认（女浓男淡、修散柔）"
    return bss, reason


def interactive_wizard(auto_mode=False):
    """第 0~4 步：开场 → 基本信息 → 四问 → 16型 → 面部结构。"""
    print("=" * 60)
    print("AI 角色打造 · 对话式捏脸向导")
    print("先陪你聊角色想法，最后才生成提示词。没想法也可以直接回车/说「你定」。")
    print("=" * 60)

    # 第 0 步：开场
    has_idea = ask("\n[0/5] 你已经有角色想法了吗？（有/没有，回车=没有）> ").lower()
    if not auto_mode and has_idea in ("有", "y", "yes"):
        desc = ask("\n  太好了！说说你的想法（身份/性格/大概长相，一句话即可）：\n  > ")
        print(f"  → 收到：{desc or '（未填写，将按后续问答补齐）'}")
    elif auto_mode:
        print("\n  → 自动模式：你没想法，我按基本信息推导，并会说明理由。")
    else:
        print("\n  → 没想法没关系，我一步步带你定位。")

    # 第 1 步：基本信息
    print("\n[1/5] 先聊聊角色基本信息（先做人，再捏脸）：")
    gender = ask_choice("  性别？", ["女", "男"], default="女")
    age = ask("  年龄段？(少年/青年/熟龄/中年/老年，或具体年龄如 25，回车=青年) ", default="青年")
    ethnicity = ask_choice("  长相族裔？", ["东方（中/日/韩）", "欧美", "中东", "拉美", "混血", "东南亚"], default="东方（中/日/韩）")
    occupation = ask("  身份/职业？(如 将军/医生/总裁/侠客/爱豆…，回车=自由设定) ", default="")
    era = ask_choice("  古装还是时装？（时代/世界观）",
                     ["现代都市", "古装（武侠/汉唐宋明清）", "民国", "未来科幻", "架空奇幻", "日常"],
                     default="现代都市")
    personality = ask("  性格/气质一句话？(可选，如「外冷内热的独行侠」，回车=跳过) ", default="")

    subject = {
        "gender": gender,
        "age": age,
        "ethnicity": ethnicity.split("（")[0],
        "occupation": occupation or "自由设定",
        "era": era.split("（")[0],
        "personality": personality,
    }

    # 第 2 步：四问
    print("\n[2/5] 骨皮形神四问（凭直觉二选一，回车=该维自动）：")
    q_bone = ask_choice("  骨：整体气质「灵动轻盈」还是「沉稳敦厚」？", ["灵动轻盈", "沉稳敦厚"], default=None)
    q_skin = ask_choice("  皮：长相「第一眼抓眼」还是「耐看舒服」？", ["第一眼抓眼", "耐看舒服"], default=None)
    q_shape = ask_choice("  形：五官「紧凑聚焦」还是「舒展松弛」？", ["紧凑聚焦", "舒展松弛"], default=None)
    q_spirit = ask_choice("  神：气质「冷冽疏离」还是「温柔亲近」？", ["冷冽疏离", "温柔亲近"], default=None)

    bss = {
        "骨": "修" if q_bone == "灵动轻盈" else ("敦" if q_bone == "沉稳敦厚" else None),
        "皮": "浓" if q_skin == "第一眼抓眼" else ("淡" if q_skin == "耐看舒服" else None),
        "形": "聚" if q_shape == "紧凑聚焦" else ("散" if q_shape == "舒展松弛" else None),
        "神": "锐" if q_spirit == "冷冽疏离" else ("柔" if q_spirit == "温柔亲近" else None),
    }

    auto_used = []
    if any(v is None for v in bss.values()):
        auto_bss_val, reason = auto_bss(subject)
        for k in bss:
            if bss[k] is None:
                bss[k] = auto_bss_val[k]
                auto_used.append(k)
        print(f"\n  （自动补全未答维度：{', '.join(auto_used)} → {reason}）")

    camp, type16 = type16_of(bss)
    print(f"\n[3/5] 16 型定位结果：骨皮形神 = {'-'.join(bss.values())}")
    print(f"      阵营：{camp}  |  类型：{type16}")
    ok = ask("      符合你想要的感觉吗？(回车=确认，输「改」调整) > ").lower()
    if ok and ok in ("改", "g"):
        dim_map = {"骨": ("修", "敦"), "皮": ("浓", "淡"), "形": ("聚", "散"), "神": ("锐", "柔")}
        print("      可调整维度：骨(修/敦) 皮(浓/淡) 形(聚/散) 神(锐/柔)")
        for dim, opts in dim_map.items():
            cur = bss[dim]
            new = ask_choice(f"      {dim} 当前 = {cur}，要改吗？",
                             [f"{o}（{'修：灵动' if o=='修' else '敦：沉稳' if o=='敦' else '浓：抓眼' if o=='浓' else '淡：耐看' if o=='淡' else '聚：紧凑' if o=='聚' else '散：舒展' if o=='散' else '锐：疏离' if o=='锐' else '柔：亲近'}）" for o in opts],
                             default=cur)
            bss[dim] = new[0]
        camp, type16 = type16_of(bss)
        print(f"      调整后：骨皮形神 = {'-'.join(bss.values())}  |  {camp} · {type16}")

    # 第 4 步：面部结构捏脸
    print("\n[4/5] 面部结构捏脸（写差异不写美；回车=接受推荐）:")
    face = face_defaults(bss)
    for key, label in [("face_shape", "脸型"), ("brows_eyes", "眉眼"), ("nose", "鼻子"),
                       ("lips", "嘴唇"), ("skin", "皮肤"), ("hair", "发型")]:
        val = ask(f"  {label}（推荐：{face.get(key, '')}）\n    > ")
        if val:
            face[key] = val
    # 加一个不完美细节破蜡像
    detail = ask("  加个不完美细节破蜡像？(如 单眼皮/高颧骨/雀斑/法令纹，回车=用推荐) ", default="")
    if detail:
        face["skin"] = (face.get("skin", "") + f"、{detail}").strip("、")

    # 组装角色卡
    card = default_card()
    card.update({
        "name": ask("\n[5/5] 角色名/代号？(回车=未命名) ", default="未命名角色"),
        "subject": subject,
        "bone_skin_shape_spirit": bss,
        "camp": camp,
        "type16": type16,
        "face": face,
    })
    return card


# ---------------------------------------------------------------------------
# 4. 三模型提示词渲染
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


def components(card):
    bss = card.get("bone_skin_shape_spirit", {})
    bone_en, bone_zh = BSS["骨"].get(bss.get("骨", "修"), BSS["骨"]["修"])
    skin_en, skin_zh = BSS["皮"].get(bss.get("皮", "淡"), BSS["皮"]["淡"])
    shape_en, shape_zh = BSS["形"].get(bss.get("形", "散"), BSS["形"]["散"])
    spirit_en, spirit_zh = BSS["神"].get(bss.get("神", "柔"), BSS["神"]["柔"])

    sub = card.get("subject", {})
    eth_zh = sub.get("ethnicity", "东方")
    eth_en = {"东方": "East Asian", "欧美": "European", "中东": "Middle Eastern",
              "拉美": "Latina", "混血": "mixed-race", "东南亚": "Southeast Asian"}.get(eth_zh, eth_zh)
    gen = sub.get("gender", "女")
    gender_en = "woman" if gen == "女" else "man"
    sub_zh = f"一位{sub.get('age','')}岁{eth_zh}{gen}性"
    if sub.get("occupation"):
        sub_zh += f"，职业/身份：{sub['occupation']}"
    if sub.get("era"):
        sub_zh += f"，时代背景：{sub['era']}"
    if sub.get("personality"):
        sub_zh += f"，性格：{sub['personality']}"
    sub_en = f"a {sub.get('age','')}-year-old {eth_en} {gender_en}"
    if sub.get("occupation"):
        sub_en += f", {to_en(sub['occupation'])}"
    if sub.get("era"):
        sub_en += f", {to_en(sub['era'])}"

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
# 4.5 出图检查清单 + 角色卡审核（源自 aesthetics.md §7 与 PPT 比例规则）
# ---------------------------------------------------------------------------
# 人物比例规则（PPT「形——尺子概念」）
PROPORTION_RULES = {
    "head_body": {
        "label": "头身比（站姿）",
        "female": (6.0, 7.0, 9.0),   # 女约 7 头；网感/二次元可到 9，超 9 显怪
        "male":   (6.5, 7.5, 9.0),   # 男约 7.5 头；同上限
    },
    "shoulder": {
        "label": "肩宽",
        "ok": 3.0,                   # ≤3 头可接受（夸张）
        "absurd": 4.0,               # ≥4 头离谱
    },
    "sit": (5.0, 5.5),               # 坐姿 5–5.5 头
    "squat": (3.0, 4.0),             # 蹲姿 3.5–4 头
}
# 三庭五眼硬规则
FACIAL_RULES = [
    ("三庭", "发际→眉→鼻底→下巴 三等分；下庭缩短=幼态，拉长=成熟"),
    ("五眼", "脸宽≈5 只眼长；眼睛位置约在头部 1/2 处"),
    ("额", "饱满≠发面：要有额结节拐点 + 额沟明暗，勿全亮死白"),
    ("眼", "眼形上三下二（平行四边形）；眼白有球体明暗；45° 侧眼=平三角"),
    ("眶周", "折叠度=骨相关键：大→深邃，小→疲倦无神"),
    ("鼻", "鼻唇角 90–100°；鼻基底饱满不凹陷；双C线/海鸥线到位"),
    ("唇", "颏唇沟 120–130°；上唇珠中线、下唇线外柔"),
    ("E线", "鼻尖-上唇-下巴 三点一线（直面/凸面/凹面），仅参考"),
    ("下颌", "下颌角拐点：低=端庄成熟，高=甜美清秀；守下颌线"),
    ("颏颈角", "约 120°；下巴短会显土气"),
    ("折叠度", "高折叠=脸小立体：颧骨微露不凸、眉骨立体、下颌线分明"),
    ("四角", "鼻额角/鼻唇角/颏唇沟/颏颈角 均做 100°+ 才精致"),
    ("皮相", "拒绝「馒化」：适度凹陷=高级脸，全填平=发面馒头"),
    ("浓淡", "浓颜：五官占比大/色浓；淡颜：小巧协调/留白多"),
    ("妆容", "重心四选二：腮红/唇妆/眉毛/眼妆；氛围感=腮红+唇，冲击=眉+唇"),
]


def parse_num(s):
    """从「7.5头身 / 9头 / 1.8头 / 九头身」解析数字；失败返回 None。"""
    if not s:
        return None
    import re
    cn = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
          "七": 7, "八": 8, "九": 9, "十": 10}
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if m:
        return float(m.group(1))
    for ch, v in cn.items():
        if ch in s:
            return float(v)
    return None


def validate_card(card):
    """审核角色卡：头身比/肩宽是否合理；返回警告列表。"""
    warns = []
    body = card.get("body", {})
    gender = card.get("subject", {}).get("gender", "女")

    hb = parse_num(body.get("head_to_body", ""))
    if hb is not None:
        lo, std, hi = PROPORTION_RULES["head_body"][("female" if gender == "女" else "male")]
        if hb > hi:
            warns.append(f"[比例] 头身比 {hb} 超过 {hi} 头（{gender}），超出九头身会显奇怪，建议≤{hi}")
        elif hb < lo:
            warns.append(f"[比例] 头身比 {hb} 低于 {lo} 头（{gender}标准约 {std} 头），偏矮小")
        else:
            warns.append(f"[比例] 头身比 {hb} 在合理区间（{gender}标准 {std} 头，网感可到 9）")

    sw = parse_num(body.get("shoulder_width", ""))
    if sw is not None:
        if sw >= PROPORTION_RULES["shoulder"]["absurd"]:
            warns.append(f"[比例] 肩宽 {sw} 头 ≥ 4 头，离谱，建议≤3 头")
        elif sw > PROPORTION_RULES["shoulder"]["ok"]:
            warns.append(f"[比例] 肩宽 {sw} 头偏夸张（>3 头），建议≤3 头")

    # 坐/蹲比例仅当 posture 提示时检查（可选）
    posture = body.get("posture", "")
    if "坐" in posture:
        warns.append("[比例] 坐姿建议 5–5.5 头身")
    if "蹲" in posture or "跪" in posture:
        warns.append("[比例] 蹲姿建议 3.5–4 头身")

    # 皮肤/蜡像自查
    skin = card.get("face", {}).get("skin", "")
    bad_words = ["完美皮肤", "8k", "超现实", "无瑕", "瓷娃娃"]
    for w in bad_words:
        if w.lower() in skin.lower():
            warns.append(f"[反蜡像] 皮肤含「{w}」触发词，建议改「保留毛孔/肌理/血色」")
    return warns


def checklist_section(card):
    """生成出图检查清单（markdown 段落），随 prompts.md 输出。"""
    lines = ["## 出图检查清单（出图后逐项核验）", ""]
    lines.append("### 人物比例（PPT 规则）")
    g = "女" if card.get("subject", {}).get("gender", "女") == "女" else "男"
    std = PROPORTION_RULES["head_body"][("female" if g == "女" else "male")]
    lines.append(f"- 头身比：{g}约 {std[1]} 头（合理 {std[0]}–{std[1]}，网感≤{std[2]}）"
                 f"；当前卡：{card.get('body', {}).get('head_to_body', '未填')}")
    lines.append("- 肩宽：≤3 头可接受，≥4 头离谱")
    lines.append("- 坐姿 5–5.5 头身 / 蹲姿 3.5–4 头身")
    lines.append("- 三庭五眼：发际→眉→鼻底→下巴 三等分；脸宽≈5 眼长；眼睛在头部 1/2 处")
    lines.append("")
    lines.append("### 面部硬规则（逐项打勾）")
    for k, v in FACIAL_RULES:
        lines.append(f"- [ ] **{k}**：{v}")
    lines.append("")
    lines.append("### 反蜡像 / 千人一面")
    lines.append("- [ ] 皮肤保留毛孔/血色/肌理，无「完美皮肤/8K/超现实」类词")
    lines.append("- [ ] 每个部位写了具体差异（单眼皮/高颧骨/雀斑/法令纹…），而非「美/精致」")
    lines.append("- [ ] 妆容重心明确（四选二），浓/淡颜定位一致")
    lines.append("")
    lines.append("> 检查不过就回到角色卡改对应字段重新渲染，或出图后 PS 微调（见 engineering.md §8）。")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. API 出图（可选）
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
# 6. 主流程
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="AI 角色打造提示词生成器（三模型标准）")
    ap.add_argument("--card", help="角色卡 JSON 路径（有则跳过交互向导）")
    ap.add_argument("--auto", action="store_true",
                    help="自动模式：用户没想法，按基本信息推导骨皮形神（仍会先问基本信息）")
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
        card = interactive_wizard(auto_mode=args.auto)

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    views = [v.strip() for v in args.views.split(",") if v.strip()]
    os.makedirs(args.out, exist_ok=True)

    # 审核角色卡（比例/反蜡像），打印警告
    warns = validate_card(card)
    if warns:
        print("\n[审核] 角色卡检查发现以下事项：")
        for w in warns:
            print(f"  ⚠ {w}")
    else:
        print("\n[审核] 角色卡比例与反蜡像规则检查通过 ✓")

    results = {}
    for view in views:
        results[view] = render(card, view)

    # 写提示词（JSON + MD）
    with open(os.path.join(args.out, "prompts.json"), "w", encoding="utf-8") as f:
        json.dump({"card": card, "prompts": results,
                   "checklist": checklist_section(card)}, f, ensure_ascii=False, indent=2)

    md = [f"# 角色提示词 · {card.get('name','未命名')}", "",
          "## 角色定义卡", "```json",
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
    md.append(checklist_section(card))
    with open(os.path.join(args.out, "prompts.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"\n[完成] 提示词已写出：{os.path.join(args.out,'prompts.md')} / prompts.json")
    print(f"[完成] 出图检查清单已附在 prompts.md 末尾，出图后逐项核验。")

    if args.generate:
        config = load_config(args.config)
        print("[出图模式] 调用已配置接口…")
        for view in views:
            for mk in models:
                print(f"-> {mk} / {view}")
                call_api(mk, results[view][mk], view, args.out, config)


if __name__ == "__main__":
    main()
