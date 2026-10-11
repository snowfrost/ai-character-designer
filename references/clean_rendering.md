# 画面净化四层控制（im2-clean-image + ai-material-realism + prompt-contamination-guard 蒸馏）

> 吸收自 im2-clean-image skill（github.com/q2522879285-source/im2-image-skills）· 2026-10-11（只学不装）；
> 同日二次吸收 ai-material-realism 的**材质物理五控**（§三.五）与 prompt-contamination-guard 的**提示词语义污染七类**（§十），来源：MOKE SkillHub（mokeaigc.com）。
> 定位：**gpt-image-2 提示词的默认收尾净化层**——任何角色提示词（定妆肖像 / 三视图 / 多人团 / 组照）交付前过一遍这四层，让画面「干净但不假干净」。
> 它解决：脏纹理堆积、蜡像/塑料感、背景杂讯、均匀细节密度（什么都清楚 = 什么都不清楚）、负向词越堆越脏、语义污染（旧概念残留/正向过载/冲突锚）。
> 它不解决：角色设定本身（走主流程）、皮肤细写（走六段式）、撞脸（走脸型库锚点）。

---

## 一、四层控制（不可拆）

| 层 | 管什么 | 一句话 |
|---|---|---|
| ① 材质光效层 | 画面物理可信 | 说出主材质及其物理行为，而不是堆「高清真实」 |
| ② 信息密度层级 | 视觉秩序 | 焦点区最细、支撑区中等、安静区大色块，细节密度递减 |
| ③ 干净渲染层 | 防伪影 | 控制细节、只留自然纹理、控制高光、最少重复图案 |
| ④ 负向卫生层 | 防污染 | 负向槽只写当前风险的宽泛失败类，不是旧失败记忆 |

**总纪律**：不靠 `8K / ultra realistic / sharp details` 这类词替代材质物理；不为了干净简化用户的想法；保住主体的构图、风格与情绪。

## 二、装配位置（与主管线骨架融合）

在 `prompt_standards.md` §0 骨架的**收尾之前**插入净化层，顺序：

```
主体/身份/动作 → 风格 → 相机构图层级 → 光路材质层 → 远近信息衰减
→ 干净渲染层（本文件 §三~四）→ 负向卫生层（本文件 §六）
```

## 三、材质光效层（人像场景版）

写角色提示词时回答这七个问题（简单肖像一句话带过，复杂造型多写几句）：

1. **主材质（hero surfaces）**：皮肤、头发、布料、皮革、金属、玻璃、宝石——画面里真正被看见的几种。
2. **表面响应**：哑光 / 缎面 / 高光 / 半透明 / 磨损 / 湿润——分别落在哪些区域。
3. **光行为**：主光方向 + 色温；轮廓光/反弹光只在有用时加。
4. **材质分离**：同色表面靠明度、冷暖、粗糙度、高光宽度、接触阴影区分，**不靠加新颜色**。
5. **曝光架构**：保护高光纹理、平滑高光滚降、可读的暗部、色不过曝。
6. **落地感**：接触阴影只出现在真实缝隙、重叠、接触区；拒绝脏 AO 光晕。
7. **光学**：景深/衍射/运动模糊只在支持画面时用，克制。

材质句骨架（英文直接可用）：

```text
The [hero material] shows [physical behavior] under [lighting condition],
with [local imperfections/topology] visible at [camera scale];
[specific areas] remain [matte/dry/absorbing] while [specific edges/surfaces]
catch [soft/sharp/specular] highlights.
```

通用材质质量块（附在材质段后）：

```text
physically distinct material classes, protected highlight texture, smooth cinematic
highlight rolloff, readable shadow-side structure, localized contact shadows,
distance- and roughness-correct reflections, restrained atmosphere, subtle finishing
```

### 三.五 材质物理五控（决策树，ai-material-realism 蒸馏）

§三的七问回答「材质是什么、怎么响应」，五控回答「**每种材质该调用哪个物理机制**」——写材质段时按材质查表选机制，不盲堆：

| 控制项 | 适用材质 | 一句话 | 生效条件 |
|---|---|---|---|
| **AO / 接触阴影** | 一切实体的落地、缝隙、接缝、脚下 | 让物体「贴在地上」而不是飘着，防贴图感 | 只在真实接触区；拒绝脏 AO 光晕（与 §三第 6 问同向） |
| **SSS 次表面散射** | 皮肤、耳廓、蜡、玉石、葡萄、薄叶 | 光穿进半透明介质再散出来（耳尖透红） | **必须有背光或强侧光**，正对平光下写了也看不见 |
| **粗糙度与各向异性** | 金属、刀刃、石材、拉丝表面、磨损工具 | 哑光面吸光、磨损边缘吃窄高光，写清哪块哑哪块亮 | 配合光源方向；同色物体靠粗糙度分离，不加新颜色 |
| **瑕疵** | 一切使用过的物体 | 指纹、微划痕、氧化、污渍——**停在表面，不破坏形体** | 瑕疵服务叙事与真实感，不是越多越好 |
| **3D 拓扑映射** | 针织、编织物、纸纹、树皮、浮雕面 | 纹理跟随几何起伏（织纹随褶皱转向），**不是 flat printed pattern** | 特写或掠射光下才值得写；大景别略过 |
| **镜面反射** | 水洼、湿皮肤、玻璃、抛光金属、亮漆 | 严格干湿边界 + 暗部吸收区 | 湿区反射、干区哑光，边界写死 |

**使用纪律**（源 skill Guardrails 蒸馏）：一轮只选 1 个 hero 材质交互 + 至多 1–2 个支撑材质分离，其余压缩——五控是决策树不是全家桶；光进不去的地方不写 SSS；不是所有面都该亮（真实材质=吸收+粗糙+选择性高光的混合）；完美干净=合成感。

## 四、信息密度层级（人像三区）

**均匀的细节密度是结构性失败**——不是让全图变糊，而是给每个区域分角色：

| 区 | 人像对应 | 规则 |
|---|---|---|
| 焦点区 | 面部 + 手部动作 | 最高边缘对比、最完整轮廓、只保留读出身份/动作/接触所需的细节 |
| 支撑区 | 躯干、服装主面 | 中等形状，只留解释空间与叙事所需的内部结构 |
| 安静区 | 背景、远景 | 大色块组织；小形状数量、纹理频率、边缘对比全部降低 |

从大到小建图：先锁 3–7 个主导形状群 + 至少一块连续平静区域 → 细节集中到 1–2 个焦点机制 → **显式写出**信息随距离/远离焦点而衰减 → 材质纹理只加在相机尺度、光线与叙事重要性能揭示的地方。

缩略图验收：一块清晰的高信息簇可见；至少一块大的安静面存活；背景边缘频率低于焦点区；画面读起来是「有意的取舍」而不是「全部清楚」或「全部糊掉」。

信息密度提示块：

```text
clear information-density hierarchy, large calm shape masses first, fine detail
concentrated at [focal mechanism], supporting forms simplified, non-focal contours
selectively incomplete, distant layers progressively lower-contrast and softer,
intentional loss of nonessential information while the hero silhouette remains readable
```

## 五、脏词替换表（写提示词前先扫一遍）

| 禁用（脏风险词） | 替换 |
|---|---|
| `ultra detailed` | `clear focal/support/quiet detail hierarchy` |
| `hyper detailed` | `selective fine detail` |
| `insanely detailed` | `realistic detail only` |
| `micro detail everywhere` | `detail concentrated only on meaningful surfaces` |
| `highly textured rendering` | `controlled material rendering` |
| `wet glossy` | `subtle reflections with strict wet/dry boundaries` |
| `glossy reflective` | `controlled highlights and roughness-correct reflections` |
| `cinematic bokeh background` | `organized low-frequency background with selectively softened depth layers` |
| `dark atmospheric background` | `smooth dark tones with low texture background` |
| `beautiful lighting` | `motivated key light, controlled bounce, protected highlight texture` |
| `realistic texture` | `physically distinct material response with natural texture only` |
| `no blur` | `sharp hero silhouette with clean intentional depth of field` |
| `no clutter` | `clean negative space and organized background shapes` |
| `no extra people` | `single clearly framed subject, empty surrounding space` |

> 与 `realism_vs_refined.md` 的关系：替换表管**渲染层脏词**，两风格路线通用；refined 路线同样受益（精致 ≠ 堆细节）。

## 六、负向提示卫生

**核心：负向槽不是旧失败的记忆馆。** 负向词不中性——它仍会把概念放进模型注意力。

顺序纪律：`正向可见目标 → 材质光效证明 → 干净渲染层 → 紧凑的当前风险 Avoid 块`。

**保留**的负向（宽泛、可复用、大概率）：
- 伪影类：`ghost texture` / `latent artifacts` / `hidden watermark-like marks` / `repetitive micro-pattern noise`
- 结构失败类（有人时）：`malformed anatomy` / `extra fingers` / `melted hands` / `asymmetric eyes`
- 假材质类：`uniform plastic gloss` / `pasted-on texture` / `milky reflections` / `dirty AO halos`
- 曝光失败类：`clipped highlights` / `crushed blacks` / `muddy shadows`
- 构图杂乱类：`extra subjects` / `stray text` / `watermark`

**删除或转换**的负向（旧、具体、比正向还生动）：
- 旧项目的道具/敌人/场景/配色/失败风格——会污染新图；
- `not like before` / `do not make it like X` 类句式；
- 目标画面里本来不太可能出现的被禁名词——**描述它反而可能召唤它**；
- 同一约束的重复版本；与正向风格/材质层矛盾的负向。

转换规则：`坏负向 → 正向可见状态 +（可选）宽泛失败类`。

**角色/人像 Avoid 模板**（与主流程「去底模脸五连」合并成一个紧凑块）：

```text
Avoid: malformed anatomy, melted hands, extra fingers, asymmetric eyes, facial artifact
marks, waxy skin, dirty pore noise, ghost texture, latent artifacts, stray text or watermark,
no CGI plastic look, no over-smoothed waxy skin, no overly symmetric doll-like face.
```

出图前五问：①正向是否比 Avoid 块强？②每条负向是否针对当前大概率风险？③有没有提到旧失败或项目专名？④有没有负向可以换成正向状态？⑤块够短吗（防注意力稀释）？

## 七、角色/人像配方（Portrait recipe，可直接套）

```text
[subject and identity], [pose/expression], [wardrobe/environment/style]. Natural facial
planes, clean eye highlights, matte skin with soft specular highlights, subtle pore texture
and peach fuzz only where visible, hair grouped into readable strands, fabric weave only on
close visible cloth, protected highlight texture, smooth highlight rolloff, soft diffused key
light with gentle bounce, clean rendering, focal detail concentrated on face and gesture,
broad calm support masses, controlled material rendering, clean gradients, controlled
highlights, organized low-frequency background with selectively softened depth layers,
minimal repetitive patterns.
```

短版清理块（提示词空间紧张时）：

```text
clean rendering, clear focal/support/quiet detail hierarchy, selective focal detail,
broad calm masses, realistic detail only, natural texture only, controlled highlights,
organized low-frequency background, minimal repetitive patterns, no ghost texture,
no latent artifacts, no low-contrast residual textures
```

条件模块按需加：
- **布料/服装**：`geometry-aware weave or knit structure, fibers following folds, grazing light revealing raised texture, no flat printed texture`
- **金属/兵器/机械**：`roughness variation, worn edges catching narrow anisotropic highlights, oxidized or matte flats absorbing light, no uniform chrome gloss`
- **玻璃/水/亮面产品**：`strict reflection boundaries, distance- and roughness-correct reflections, no milky global mirror floor`
- **暗背景**：`smooth dark tones, readable shadow floor, clean value separation, low texture background, controlled rim light, no noisy bokeh`
- **幻想/密集概念图**：`large readable shape groups, one or two focal detail clusters, continuous calm masses, no repeated micro ornaments`

## 八、脏图重生模式（Dirty Output Retry）

出图已经脏了（鬼影纹理、水印感、隐藏印记、低对比残留）时——**不要图生图反复洗**（迭代会放大潜空间脏污），重写提示词干净重生：

```text
Regenerate the same concept as a clean-slate image: [锁住主体/姿势/构图/风格/配色].
Preserve the main design and mood. Rebuild the rendering with clean material separation,
balanced detail, realistic detail only, controlled highlights, smooth background tones,
and minimal repetitive patterns.
Avoid: ghost texture, latent artifacts, hidden watermark-like marks, dirty texture buildup,
repeated micro-pattern noise, muddy shadows, low-contrast residual textures.
```

> 与「同角色换场必走图生图」铁律的关系：**身份保持**走图生图（脸锚点），**画质净化**走干净重生（clean-slate）——两件事别混。图生图出的图脏了，回到提示词层修净化层再生成，不要在脏图上叠图生图。

## 九、提示词语义污染七类（交付前最终门，prompt-contamination-guard 蒸馏）

> 核心视角：**提示词是一个加权的语义场**——标题、分段、正向措辞都不能把概念隔离开。
> 负向卫生（§六）管负向槽，本节管整个语义场的意外联想与意外加权。

| # | 污染类 | 识别 | 人像场景例 |
|---|---|---|---|
| 1 | **旧上下文残留** | 名词/道具/配色/失败词来自上一个项目或上一版尝试，而非当前任务 | 上一版角色的「酒红色」溜进新角色；为「防出现旧道具」而点名旧道具也算污染 |
| 2 | **纠错排除泄漏** | 用「不要/避免/不是/no/without」解释不想要的结果——被拒绝的名词仍在语义场里活跃 | 「不要蜡像感」反而召唤蜡像；正确做法是正向写「哑光皮肤带可见毛孔」（§六同源原则） |
| 3 | **默认模板污染** | 习惯性开头/房间/舞台/运镜/构图溜进来，用户没要求 | 每个角色都站在「极简影棚」；九连禁（fantasy05）就是这类 |
| 4 | **负载标签污染** | 抽象标签（压迫感/高级感/清冷感）替代了可见证据 | 只写「高级感」不写「哑光皮肤+低饱和+柔和明暗过渡」；标签只有在可见定义已在别处落地后才可作短句柄保留 |
| 5 | **正向语义过载** | 多条正向句用不同措辞描述同一可见事实——重复即加权，某效果变得过大或全局化 | 「断面/切面/裂面」三处出现＝一个几何被加权三倍；「清冷/疏离/淡漠/冷冽」连写＝表情被压死 |
| 6 | **内部流程泄漏** | 可粘贴提示词里混入工作流语言、审核备注、「上一版」「本段」「继续保持」 | 给王老师的交付稿里出现「此处按第 3 步修正」 |
| 7 | **冲突语义锚** | 两条指令给同一表面分配了不兼容的优先级 | 「克制哑光皮肤」+「水润透亮光泽」同写；refined 路线误叠 realism 负向（SKILL.md 知识污染自查第 1 条） |

**交付前三个动作**：

1. **逐句溯源**：`条款 | 来源 | 当前职责 | 污染类 | 保留/重写/删除`。合格来源只有：当前用户需求、用户给的参考及其角色分配、当前项目锁定、领域 owner 批准的事实——「听起来专业」「上一版成功的提示词里有」都不是来源。
2. **Deletion test**：对每条疑似重复的句子问「**删掉它，有没有任何唯一的可见生成选择消失？**」——有，保留在其权威归属段；没有，删除（意外加权）；两条冲突，按用户当前优先级留一条。⚠️ 不要为省字数删掉唯一的身份/材质/镜头事实——字数不是删除理由。
3. **Stateless-generator read**：假装生成器**完全不知道对话历史**，通读最终稿——每个代词和「如前所述」类指代在稿内可解析？没有旧项目名词幸存？没有被排除物只靠点名排除？没有机制被同义词重复加权？每个跨段条款都在贡献不同信息？

**二元门**：PASS = 每个模型可见条款有当前来源且职责唯一 / 排除已转为正向事实 / 每个 hero 机制只有一次权威出现 / 跨段条款信息不重叠 / 清理中没有丢失唯一控制。任一不满足 = FAIL，回到溯源表。

## 十、边界与防污染

- **与六段式皮肤公式（`prompt_craft.md` §11）**：互补不替代——六段式管皮肤**写什么**（一次一个物理状态→区域纹理→…），本文件管**全画面材质分离与防伪影**。六段式已写高光分布时，不重复加 `protected highlight texture`。
- **与 fantasy_life_force 皮肤黑名单（§2）**：同向——那边管「不能写什么」（油光/磨皮），这边提供「写成什么」的替换词。
- **与去底模脸负向（主流程注意事项）**：合并进 §六的人像 Avoid 模板，**一个紧凑块**，不叠两套。
- **与 portrait_3x4 的「负向词非必要不用」**：同源原则（正向锁优先、负向紧凑、用完即撤）；定妆肖像默认零负向，确需时按 §六只补一行。
- **与 ai-material-realism（MOKE SkillHub，2026-10-11 吸收）**：只吸收了 **Five Controls 决策树**（§三.五）与 Guardrails 纪律；其 Anti-Artifact / 脏词替换 / cleanup add-on 与 im2-clean-image **同源重叠**（两边词表几乎逐字相同），已由 §三/五/六覆盖，不重复收录；其灯光/运动真实化完整体系归视频侧（seedance25 系 skill），本文件只取人像出图所需。
- **与 prompt-contamination-guard（MOKE SkillHub，2026-10-11 吸收）**：§九是其人像场景版蒸馏；源 skill 还有跨段语义台账（mechanism | appearance | trigger | path | result | decay | owner 的机制登记表），适合复杂 VFX 视频提示词，人像场景一般用不到全表——多人团提示词若超 16 区块骨架的复杂度，可按台账思路登记每个视觉机制的唯一归属区块。
- **refined 路线**：本文件管「材质真实」，不是「皮肤瑕疵」——refined 同样适用（蜡像感 ≠ 精致）；但 `subtle pore texture and peach fuzz` 等词在 refined 路线按 `realism_vs_refined.md` 弱化。
- **重场景/建筑/体积光**等非人像场景的完整规则在源仓库（im2-image-skills），本 skill 只蒸人像所需；需要时去源仓库读 `heavy-scene-structure-and-mass.md` 与 `real-scene-light-atmosphere.md`。
