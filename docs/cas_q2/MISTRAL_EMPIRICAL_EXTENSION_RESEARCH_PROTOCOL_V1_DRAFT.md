# Mistral 固定双候选 RAG 修复经验扩展：研究协议 V1 草案

External draft receipt SHA-256:
`787b6a3992988d31dccbc2a4c75561c51f498e1e555797cb5721096d336d70cf`.

日期：2026-09-13（Asia/Shanghai）
研究设计：**GPT-6 Astra，xhigh**
依托治理：repo `8088014e768349725ca6f1c4f0343b68c329616a` 的 `POST_PHI_FAILURE_RESEARCH_GOVERNANCE.md`
文档身份：**DRAFT_ONLY；NOT_ENGINEERING_FROZEN；NO_EXECUTION_AUTHORIZATION**
**CAS Q2 STATUS: NOT READY。**

本稿完整覆盖 G0–G8 的研究问题、合同、证据需求和停止门；“覆盖”不代表每项已有验收证据。带 `UNRESOLVED` 的字段是阻断条件，不能在执行时自行选择。本文不创建 namespace，不下载资产，不运行 tokenizer、模型、拟合、科学评分或 bootstrap，不选取 ID，不读取 Gold，不修改 repo。文中的未来步骤均须另行通过相应重大科研/真实性准入；本稿不能自行授权下一阶段。

## 0. 唯一决定、权威边界和废止事项

只评估一个既定 reader 条件下的经验增量：

`mistralai/Mistral-7B-Instruct-v0.3@c170c708c41dac9275d15a8fff4eca08d52bab71`。

不继续 Phi。`FAIL_P0_1_PHI_DEVELOPMENT_AUTHENTICITY`、V1–V4、全部 validator/auditor 失败和 forensic 补证原样保留；不将 Phi 答案、repair query、scores、eligibility、模型头、metrics 或失败后分层作为本研究输入。Phi 的失败是冻结验证契约失败，不能写成 Phi 科学效果为负。

原依赖 Phi 的投稿推进链已经终止。本稿是其后重新治理的**新文档分支**，不是旧链的替换节点。既有 `THIRD_READER_MISTRAL_PROSPECTIVE_PROTOCOL_V4_DRAFT.md` 和 placement contract 仅提供可审查的静态规格；其中“Phi PASS 前驱”“无论 Phi 结果直接执行”“三 reader 科学结论”“185→205 fits”和“2–3 天/8–13 工作日”不在本稿生效。Phi 尚未进行获准的科学头拟合；本分支若全部获准，仅增加十次 fit，账本无其他获准变化时为 **185→195**。旧文件不得删改。

当前唯一允许的是完成本文与独立 GO/STOP 文档审查。当前决定字符串：

**`DRAFT_COMPLETE_WITH_UNRESOLVED_GATES_NO_EXECUTION`**

## G0. 研究必要性与可证伪经验贡献

主问题：固定原/修复答案候选、共享检索池与 5% 全批次动作上限后，HGB 与 GbV 分别在监督匹配控制之上增加什么？这些增量是否同时改善全总体 EM 和 Damage，是否在另一个命名 reader 条件下保持？

| 主比较 | 增量方向 | 已公开 Qwen 事实 | Mistral 无论符号如何新增的知识 |
|---|---|---|---|
| C1：HGB_GBV_R − HGB_ONLY_R | 加入 GbV 的条件增量 | 严格 EM/Damage 联合门未通过 | 在固定不同 reader/容量条件下，该未闭合增量是正向、反向、权衡还是不精确 |
| C2：HGB_GBV_R − GBV_ONLY_R | 加入 HGB 的条件增量 | 严格联合门通过 | 指定 Qwen 发现是否在此固定 reader 条件下复现；若不复现，完整报告边界 |

ROA-FULL 相对 fusion 的复杂性审计保持次要地位；其历史候选否决不恢复。HGB 是固定上游估计器与必要比较器，HGB_GBV_R 是既有经验政策；二者均不改名为新算法。第三 reader、paired 形式、更多日志和“监督匹配”字样本身不是创新。

本问题有价值的条件是：两单信号控制完整、公平，区间足以区分有实际意义的效应，成本与来源限制可以明确报告。正结果可建立命名条件下的增量；精确的反向/权衡结果可建立边界；窄但跨零的区间只可限制效应大小；宽区间的不显著结果不构成等效或足够投稿贡献。若目的退化为取得第二个显著结果，G0 失败。

**结果影响披露固定文案：**“该扩展在 Qwen fresh study 结果已公开、Phi 获取真实性验收终止后形成。Mistral exact revision 的选择已有更早记录，但此次必要性判断、两主比较及新工程契约受已知 Qwen 结论和 Phi 工程失败影响。Mistral 科学输出尚未取得；这是前瞻冻结的同题 reader 条件扩展，不是全项目结果之前注册的非适应性独立确认。”

## G1. 单次新分支、前驱图与失败隔离

拟议根 namespace 为 worktree 内 `outputs/cas_q2/mistral_empirical_extension_v1/`，**本阶段不创建**。未来仅允许一次独占创建；存在任何字节即拒绝复用，不删除、覆盖、改名或改到 V2。固定子阶段名称为：

`assets` → `invented_preflight` → `input_freeze` → `development_runtime` + `development_replay` → `development_validation` → `development_scores` → `development_outcomes` → `matched_panel` → `test_runtime` + `test_replay` → `test_validation` → `test_scores_actions` → `prelabel_validation` → `outcomes` → `analysis` → `client_final_audit`。

每阶段有唯一 producer 和唯一独立 validator 输出子目录；不能把第二次调用称作同一次验证。启动器未进入正式 namespace 的失败也在外部 attempt ledger 中保存命令、返回码、日志、时间和控制哈希；pre-namespace 失败不抹去一次性预算，也不自动授权更正重跑。本文只规定将来可能使用的 DAG，不打包授予这些阶段的执行权。

允许的旧前驱仅限以下**内容用途**，并在后续 input graph 中逐文件绑定 accepted receipt、manifest、真实 bytes 和作用域：

1. 已验收 Qwen fresh cohort 的 **6,000 个身份**、C1 gold-free projection/候选池和 C2 原始检索/文档向量数组；不重复 C1/C2 神经计算，不复用 Qwen 输出作 Mistral 答案。
2. 已认证历史 development 的 4,500 个身份、既有 fit/cal 分配、gold-free question/document projection、原始检索/候选池、原生 prompt/config/source，以及七个**原始**上游模型文件。
3. 已验收 BGE/NLI 和环境资产、历史控制配方、合法已公开的聚合规划统计、固定 V2 参数和可独立验证的重放身份清单。
4. 未来本 Mistral 分支中已经取得 producer PASS、independent PASS 与 client acceptance 的前驱。

禁止将任何 failed Phi namespace 或 Phi runtime/input-freeze/replay PASS 作为 Mistral accepted execution predecessor。旧 `PHI_TEST_REPLAY_SELECTION_FREEZE_V1.json` 可以只作为身份选择历史来源；必须独立绑定其四个身份字段到 accepted Qwen cohort 和原重放身份，无需也不得依赖 Phi 输出。文件名含 Phi 不等于可复用其科学 payload。

前驱“accepted”不豁免历史缺口。七个上游原始 fit-time receipts 缺失、HGB 重现文件线程元数据不同导致 byte gate 失败等限制继续披露；只使用既定原始文件，不换成重现版，不再 fit。完整新 input graph 尚不存在，列为 U1。

## G2. 固定研究对象、配方与动作

### G2.1 人口、开发和同题身份

| 分区 | question groups | retriever traces | 固定角色 |
|---|---:|---:|---|
| development fitting | 3,600 | 10,800 | 仅 eligible 的 Mistral Recovery 标签训练 base heads |
| development calibration | 900 | 2,700 | 仅 eligible 的 Mistral 标签拟合各自 Platt；不得重拟合 base |
| test | 6,000 | 18,000 | 每数据集原有 2,000 题；完整固定动作后映射 outcomes |

三检索为原生 BM25、BGE dense、hybrid RRF。同题三个 siblings 始终同分区、同 bootstrap multiplicity。历史 development 与 test 身份不相交；不新抽样，不预备替补，不排除模型失败/空答案/相同答案，不扩大 6,000 题。同一 test 已有 Qwen outcomes，因此不是新题 population replication，也不声称训练语料独立或 benchmark 无污染。

fit/cal 采用原冻结身份分配；其定义为每数据集 1,500 题按 UTF-8 `cas-q2-empirical-fit-v1|20260924|<dataset>|<sample_id>` 的 SHA-256 升序、再 sample_id 排序，前 300 为 cal，余 1,200 为 fit。本阶段不读取清单、不重新选择身份；以后仅重建验证既有分配。要求 eligible fit 和 eligible cal 各有 Recovery 的两个类，否则终止，不重抽、不换标签或 seed。

### G2.2 acquisition 与评分语义

对全部 31,500 canonical traces 固定执行 `a0 → repair_query → repair_retrieval → a1`，三次逻辑 generation，不因将来只切换 900 行而少生成候选。生成是 greedy、batch=1、无 sampling；答案最多 48 new tokens，repair query 最多 64；沿用既有 answer/repair prompt 内容和 16,000-character context renderer。Mistral 原生 pinned chat template，单 user message，`add_generation_prompt=True`，无额外 system/tool/reader-specific instruction。EOS/pad、decode、tokenizer fast/slow、attn implementation 以最终 exact adapter 绑定，禁止运行时默认值漂移（U2/U3）。

只改变 reader 及其原生 tokenizer/template，repair retrieval 的差异来自该 reader 的新 repair query。原池、原检索配置和原始 E0 不变；不对 Mistral 重建“更合适”的池，不隐藏上下文来源是 bounded benchmark-derived pool 的限制。

BGE 固定 `BAAI/bge-base-en-v1.5@a5beb1e3e68b9ab74eb54cfd186867f64f240e1a`：BF16、CLS、原生 `F.normalize`、FP32 输出数组、维数 768、batch≤16、max_length=512、既有 query prefix、numpy exact。保留既有截断语义和原始向量，不新增 FP32 重归一化/换 cosine 算法。Mistral runtime/base score 的 BGE 为该阶段唯一实例。

四格 teacher-forced likelihood 沿用原 `ReaderLikelihoodScorer` 的答案位置、sum/mean/min、mask、position IDs、empty initial cache 与四格排列；reader 改为确切 Mistral，max **total** scoring length=8192，batch=1、`use_cache=False`。原 scorer 的 token-overflow 左侧 prompt 保留逻辑是既有语义，必须原样记录 truncation，不混入新的上下文裁剪策略。生成输入 8192 上限与 likelihood 总长 8192 是不同约束。**48 个生成 token 不保证 decoded/re-aligned 答案只有 48 个评分 token**；实际 answer IDs 必须独立重建，答案单独不能留出非空 prompt 时按既有 guard 终止。各 cell 保存截断前 render hash、截断后的真实 input IDs 和答案位置；不得用 render 字符串替代实际评分证据。

GbV 固定 `MoritzLaurer/deberta-v3-large-zeroshot-v2.0@5a4338ab2151dc8db04ad53b42b6153382bf4f99`，FP32、slow tokenizer、batch≤8、pair length≤512、正 entailment index=0。假设模板为 `The answer to the question "{question}" is: "{answer}"`；每 retrieved passage 独立、过长按原 20-word overlap 切分、无新科学截断、branch=max entailment probability、paired score=F1−F0。全部原 passage 参与，不能把 reader 16,000 字符 context 上限冒充 NLI 总文档长度上限。

### G2.3 七个固定上游与五个 reader 匹配头

七个原始上游 learned estimators 顺序固定：`state_symmetric_hgb`、`state_symmetric_logistic`、`no_cross_state`、`no_B`、`no_evidence_change`、`no_answer_form`、`ordinary_compact_logistic`。其模型 bytes、输入 schema、旧训练来源保持冻结，Mistral 产生 reader-specific 特征值但不重新训练这七个估计器。`B_rule`、`higher_own_likelihood`、`likelihood_margin` 是其余既有规则输入，`gbv_margin` 是第 11 个 numeric feature；这些不是额外 learned head。

| 新 reader 匹配 policy | numeric indices | 数值/缺失 flags/三 retriever 列 | 总宽 |
|---|---|---|---:|
| ROA-FULL | 0…10 | 11+11+3 | 25 |
| ROA-NOGBV | 0…9 | 10+10+3 | 23 |
| HGB_GBV_R | 0,10 | 2+2+3 | 7 |
| HGB_ONLY_R | 0 | 1+1+3 | 5 |
| GBV_ONLY_R | 10 | 1+1+3 | 5 |

目标固定 `R=1{a0_EM=0,a1_EM=1}`，不是 Net 或 Damage target。fit-only median imputation、mean、population std；zero std→1；missing flags 和 retriever indicators 不缩放。与已接受 empirical panel 相同的 missing/all-missing column 处理必须在实现前逐源绑定；不能在 Mistral 标签后定义回退（U3）。

base：L2 logistic、C=1、lbfgs、max_iter=5000、tol=1e-4、class_weight=None。cal：只在 disjoint cal logits 上 Platt logistic、C=1e6、lbfgs、max_iter=2000、tol=1e-4。五 base 加五 cal，**恰好十次科学 fit**；不允许 synthetic fit、重试 fit、CV/LODO、fit+cal refit、阈值/特征/正则搜索、模型平均或修改损失。固定 deterministic runtime seed `20260930`，不构造 seed panel；其设定不宣称跨硬件确定性。收敛或类检查失败即停，不增加迭代或换 solver。

fit 前封存有序 IDs、feature/target matrices 与哈希；每 fit durable receipt；独立 validator 只读 saved coefficients/transforms，重建所有 eligible development logits/probabilities，不调用 `.fit()`。允许重放同一 development 的参数算术，但禁止计算开发质量排名、挑 head 或 actions。

### G2.4 common eligibility、缺失与动作

先按原 normalization：lowercase、去 ASCII punctuation/English articles、空白合并。原始 `a0` 为空→`a0_empty`；否则 `a1` 为空→`a1_empty`；否则 normalized answers 相同→`normalized_answers_equal`；其余为 pair-eligible。确定性的原生 unscorable 分支（例如 NLI hypothesis/single-word 无法 fit）按冻结 reason 进入 shared forced-Keep；新 reader 的 OOM、坏 token、意外 NaN、journal/asset 不一致等工程故障**不能伪装成 unscorable 行继续运行**。

可被历史 schema 接受的缺失 numeric inputs 使用固定 flags/fit-only transforms；不得误把可插补 feature 缺失等同于删除整行。必须所有主要 policy 使用同一最终 common eligibility；任何未在契约白名单的 feature/score 不对称、missing flag 类型变化或无法重建的异常，终止 prelabel stage，不临时降低共同资格掩码以排除难例。完整 truth table/schema 对接仍需 U3 的 static closure。

全部 N=18,000 保留在分母。每可排名 policy 固定 `K=round(0.05*N)=900`，eligible score 降序、canonical `(dataset,retriever,sample_id)` 升序处理 ties，选择 `min(900, eligible_count)`；其余 Keep。无 score>0 threshold、dataset quota、每 policy 不同资格、预算扫描。Keep 的 switch 数为 0。

## G3. 原生公平比较与全部政策角色

主推断对象仅 C1/C2 两个比较、三个监督匹配 policy。三者同 development 角色、Recovery 标签、变换配方、base/cal fit 数、同一候选对、同 eligibility、同 K。单信号缺少另一信号是设计对照；不把预训练 verifier 的训练成本说成与 HGB 监督来源相等。

固定报告九个 policy：五 reader 匹配头、raw HGB、raw paired GbV、Keep、既定 sealed V2（参数不重训，Mistral 特征下为历史参数迁移诊断）。ROA-FULL/NOGBV 是次要复杂性/依赖控制；V2 是次要历史 comparator，不能争夺主比较或恢复候选地位。V2 的额外固定校正参数不属于七个 ROA upstream estimators，不增 fit，须单列 artifact 和历史监督。禁止 Phi 参数迁移；本 V1 不额外增加五个 Qwen panel 参数迁移政策。

本 V1 **不增加 Always Repair**。若未来独立审查仅允许把现成 outcomes 的 all-eligible repair 作为描述性附录，必须先作前瞻文本修订，明确其动作数更高、非 5% 同预算、无新 primary test；不能在看到结果后增加该曲线。

不增 cross-retriever probing、RECA 四格交互方法、证据 clusters、反事实替换、额外 verifier 或新 head。现有四格仅作为既定上游 likelihood 特征，不被改称独立方法。

共享 acquisition 全成本、各 score 的依赖增量、历史训练/资产成本分开核算。不得由共享同时计算全部特征的 elapsed 时间推导 HGB-only standalone 延迟，也不以 900 个 switches 把 94,500 canonical generations 宣传成按需计算预算。

## G4. 固定 estimands、四端点与统计计划

令 y0_i,y1_i∈{0,1} 是两个候选的 normalized EM，z_pi 是 policy p 的 switch 指示。定义 `R_i=(1−y0_i)y1_i`、`D_i=y0_i(1−y1_i)`。全总体：

`EM_p = 100/N Σ_i [y0_i + z_pi(y1_i−y0_i)]`；
`Damage_p = 100/N Σ_i z_pi D_i`；`Recovery_p = 100/N Σ_i z_pi R_i`；
`Net_p = Recovery_p−Damage_p = EM_p−EM_Keep`。

C1/C2 均报告 EM_p−EM_c 和 Damage_p−Damage_c，单位 percentage points，分母 N_all。正 EM 有利，负 Damage 有利。Neutral 是切换但 EM 状态不变（含 0→0 与 1→1）；同时报告未切换数和所有四转移计数，F1 单独次要报告。

bootstrap 固定如下：

1. NumPy `default_rng(20260930)`，精确 20,000 draws；固定 dataset 顺序与其已存在 canonical question 顺序在 manifest 中枚举，不靠 Python set 顺序。
2. 每 draw 每 dataset 从原 2,000 questions 有放回取 2,000；三个检索 siblings、全部 policy 同步搬移。每 draw 始终 6,000 groups/18,000 rows，K 始终 900。
3. fixed models、feature transforms、realized pools、candidate pairs 不变，不 refit、不重新检索。不把 20,000 draws 当 20,000 个新样本或功效。
4. 在 resampled 全批次按已冻结 score/canonical order **重分配 top-K**。重复某原 row 的 copies 相邻，copy ordinal 只决定同原 row 内部身份，无额外信息；weighted-copy kernel 必须对固定首 draw 及预写边界 fixtures 作独立 explicit-copy membership 检验。
5. 主 family 是两个比较×两个端点的四个 adjusted intervals。NumPy linear percentiles 为 `[0.00625, 0.99375]`（Bonferroni 0.05/(2×4)）；完整给出 unadjusted `[0.025,0.975]`，明确后者次要。approximate bootstrap coverage，不是精确 finite-sample guarantee。
6. 每比较严格联合门：**adjusted EM lower>0 且 adjusted Damage upper<0**。任何边界为 0 均不通过。若仅一比较通过，只写该比较；不合并 endpoints、不放宽为 Damage“不显著变差”。

固定次要输出：九 policy 全总体 EM/F1/Recovery/Damage/Neutral/Net、资格原因计数、动作数；原全局动作下 dataset/retriever cells；相同 draws 的 fixed-action sensitivity；ROA-FULL−fusion 的 EM/Damage unadjusted 95% 复杂性诊断。次要没有新增 superiority family，不能选较窄区间、最好 cell 或改 primary。不得加 budget curve/seed/新 subgroup/refit。

不同 reader 的各自 p/CI 一正一负不等于 reader interaction。两个 reader 可并排展示同一比较；不 pooled rescue、不多数投票、不以 Mistral 结果修订 Qwen 结论。Cross-reader effect difference 如未预先另设统计 family，在本文只作描述，不能宣称显著交互。

区间条件于固定训练 panel 与 realized bounded corpus，未覆盖训练/校准、检索池构建、模型选择和历史设计适应性不确定性；全批次排序亦使普通独立 row 公式不适用。test cohort 是原 deterministic hash sample，非声称随机概率样本。

## G5. Invented-only 资源、吞吐和数值预检合同（设计，未执行）

### G5.1 资产与环境 pin 的先后关系

官方精确 revision 的既有 metadata 报告 7,248,023,552 parameters、14,496,047,104 BF16 tensor bytes、三 indexed shards；不获取重复 `consolidated.safetensors`。已知 config SHA `affafc6478ec0fd07a32f0ca57aa2fc57743f4d17d6730f86a96ac24d1507f99`，index SHA `e489ba553b87cde188d921b1a8283c2e0b9d33d635b88147d96ff0fcd6250016`，tokenizer_config SHA `0533dec9cfe319163801b6618d0f3ec9cfa126b6288e3df5deca6e32acb09cd2`，chat-template SHA `e16746b40344d6c5b5265988e0328a0bf7277be86f1c335156eae07e29c82826`。这些是现有 selection records 的 metadata，不是本轮下载/验证权重。

exact weight/tokenizer bytes 尚未全部 pin（U2）。未来如果仅获预检准入，必须先独占资产 acquisition/verification，固定仓库 revision 的官方文件列表和可信 LFS SHA/OID、size、allowlist；对每 shard 做 full byte hash 与 safetensors header census，逐 tensor 一次覆盖、无 missing/duplicate、dtype/shape 对应 index。没有完整事前可验证清单不能加载模型。取得 receipt 不自动授权 benchmark。

工程环境基线为现有接受记录的 Torch 2.7.1+cu128、Transformers 4.53.2、NumPy 2.2.6、SciPy 1.15.3、sklearn 1.7.2、joblib 1.5.3；需要 tokenizer/offload 依赖及完整 wheel/native bytes 时先完成 U2/U3，不按“兼容最新版”升级。固定实际 Python、driver/CUDA、GPU UUID/total bytes、Windows、CPU thread/BLAS、环境变量、全部执行 import/AST/配置、命令和工作区身份。旧环境 PASS 只证明旧验收范围，不能替代 Mistral placement/CPU BF16 支持。

### G5.2 硬长度、精度与 placement

生成 prompt 上限 **8192 tokens**；总自回归边界 8192+64=8256。Phi 的 9472 不移植。保留 16,000-character renderer，不因超限另截 question/context。teacher-forced input 总长≤8192；评分答案 retokenization 上界按 native guard 至多8191，不能错误写为48。BGE `[16,512]`，NLI `[8,512]`，reader generation `[1,8192]` + 64 decode，likelihood 最坏 `[1,8192]`、词表32768，包含实际 full-sequence logits 和答案位置 FP32 reduction。

BF16 reader/BGE，FP32 NLI；无量化、无改变 tensor dtype、无 disk offload。reader 非 layer 的 embedding、final norm、lm_head 在 cuda:0，完整 decoder layers 的最小最高编号 suffix 固定驻 CPU，其余 cuda:0。令 M 为预检 host 实测 device total bytes，W 为 headers 总 tensor bytes，W_l 为第 l 层 bytes：

`KV = 2×32×8×128×2×(8192+64) = 1,082,130,432 bytes`；
`BGE = 218,968,576 bytes`；
`n* = min{n∈{0,…,32}: W−Σ_(l=32−n)^31 W_l + BGE + KV ≤ 0.85 M}`。

map 在 load 前写入 seal，只计算一次，不按观测峰值重选。现有 exact-device static snapshot M=17,102,864,384 bytes，W_l=436,224,000；预测 n*=3、layers29–31→CPU，静态项14,488,474,112 bytes≈84.71%。全 GPU静态下界≈92.37%。它们排除了 activations/logits/context/allocator，不是实际峰值或运行可行性 PASS。

**CPU placement 必须是真实计算放置。** 某些 offload hooks 将 CPU 权重临时搬回 GPU，不能以 storage map 冒充 CPU execution map。拟议合同要求 layer 权重固定驻其设备、相应 hidden/KV/position/mask 在固定边界转移，lm_head 回 GPU；只允许显式列明的 activation/device copies，禁止权重动态迁移/自动 map。确切 wrapper/hooks、CPU BF16 kernels、KV per-layer 位置、计时边界与源代码还未实现/审计（U3），是预检前必须闭合的工程设计，不能继承旧 `.to(cuda)` constructor 而声称已支持 offload。

按阶段固定：runtime 一个 reader+BGE；base-scoring 一个 reader+BGE；NLI-scoring 在前者正常结束、释放并退出后用独立进程只加载一个 FP32 NLI；CPU fitting/analysis 无神经模型。禁止 NLI 与 reader 无意共驻，禁止同进程两个 reader 或 runtime BGE+另一个 answer BGE。各 stage cold-load、cache 状态、load/unload 时刻均记录。

### G5.3 单次预检的有限 invented suite

所有文本是提前提交的 invented question/documents/answers，不引用 benchmark 身份、prompt payload、答案、标签或 Phi 输出。边界 token fixtures 只用 pinned tokenizer 构建，在模型 load 前封存精确 text/IDs；无法按 deterministic 构造规则产生规定长度即失败，不在看到生成质量后换例。预检验证 shapes/数值/资源，不评估“答对题”。

固定模型预算建议如下，须由独立审查与最终 manifest 原样接受后才可执行：

| 阶段/fixture | 预写固定组合 | warm/timed | 逻辑上界 |
|---|---|---|---:|
| reader greedy generation | input lengths 512/2048/8192 × a0(48)/query(64)/a1(48) | 每格1 warm+3 timed | 36 generations；output cap合计1920 |
| teacher likelihood | total lengths512/2048/8192 × answer-position counts1与(total−1) | 每格1 warm+3 timed | 24 cell forwards |
| BGE with reader resident | 最小合法长度/512 × batches1/16 | 每格1 warm+3 timed | 16 forwards，≤136 texts |
| NLI isolated | 最小合法pair长度/512 × batches1/8 | 每格1 warm+3 timed | 16 forwards，≤72 pairs |

BGE/NLI 第一长度的精确 token 数由特殊 token grammar 决定，最终 fixture manifest 固定最小合法长度，不把缺少特殊 token 的非法长度1送入模型（U2/U3）。generation warm/timed 都用原 EOS 和 max_new_tokens，记录实际输出，不强制改变科学 EOS。若不能实际观察完整64 decode，补足资源边界依赖下述**预先固定** direct-forward stress，不能临时加第二组生成。

同一唯一预检进程再执行 1 次 direct prefill（8192）+64 次单 token cached decode 的 worst KV stress，共 **65** reader forwards；输入 continuation token IDs 预先 invented 固定，非新逻辑 generation，单列统计；不得用强制64 token 的行为替代 canonical greedy。另固定3次 joint direct scoring stress（input8192、最长合法answer8191），3次BGE `[16,512]`，NLI独立3次`[8,512]`。这些额外9 forwards列入预算，不重复 suite。CPU journal rejection fixtures 使用 stub，零模型/零 fits。

这是 token/shape 边界测试设计；generated answer scoring 路径还需以实际 decode→alignment→四 cell 的短 invented pair 在上述24 cell内指定覆盖，不能只测裸 tensor bypass。最终 fixture manifest 必须证明所有原生 render/scorer paths 已覆盖，遗漏即 U3 未闭合，不默认增加调用。

GPU peaks 从 cold load 开始连续记录，对每 case reset 前先持久化阶段峰值；最终 gate 取包括 load、全部 generation、teacher full logits、BGE、NLI阶段的**最大值**。不能只测最后长 generation 而漏掉 teacher logits 峰值。要求 allocated≤0.90M、reserved≤0.95M、cudaMemGetInfo 等 device-level used≤0.95M，无 OOM/allocator retry/坏 counter/未声明 map变化。device global counter记录background processes；无法隔离或解释则FAIL，不扣掉对自己有利的未知memory。

host RAM/commit/pagefile、CPU suffix working set、CUDA/CPU copies、temperature/throttling、cold load、每casewall/prefill/decode tokens/s、physical disk与fsync latency均保存。host RAM硬上限、pagefile政策、总wall-clock额度和disk reserve尚需项目可承担预算（U5）；不能只记录而无上限，亦不能凭旧“Mistral2–3天”放行。

独立 validator 只读取保存的 exact inputs/arrays/logits/devices/counters/events并独立tokenization/算术重建，零额外神经 forward、零fit；不import producer/placement helper；完整 safetensors headers/map最小性、token/cell、聚合、durability、warm/timed/failure计数逐一对账。Astra xhigh client 再审原始 witness与前驱。预检任何门失败即停止 Mistral，本稿不授权更正run。

`input_freeze` 的 full cohort tokenization **不属于 invented-only 许可**。只有资源阶段通过且后续另获输入冻结准入，才可 value-blind读取既有ID/question/document投影，封存 a0/query deterministic prompts；dynamic a1 与全部 scoring prompt 在各实际调用之前同样执行 guard。其值不得用于调整科学规则或筛题。

## G6. 总调用、fit、token、存储与时间预算

### G6.1 计数常量与 replay

canonical N_D=13,500、N_T=18,000、N=31,500；development replay r_D=180、test replay r_T=180，R=360、A=N+R=31,860。development 使用既有历史 runtime replay 的180 ordered identities；test 使用既定180（每dataset×retriever20）身份历史。test identity-only freeze SHA `d33c3720d5b4ae53a7fb66d5d4e6e6d36c684957134db3c4b1bcc28ca68b56b6`。development exact identity manifest hash与test对Qwen来源重新绑定尚待U1；本阶段不读取或选择 IDs。

两 replay 各在 canonical 完成后、Gold前，以独立模型进程及空 likelihood cache 独占新 replay 子目录执行一次相同 ordered trace acquisition；三次 generation、repair query 和 document 选择必须 exact match。此 V1 另外把**同360已固定trace的likelihood/BGE/NLI神经评分replay**计入上界，以对应保存的 canonical score receipts；不新增身份。neural numeric/reduction/replay门按G7，不因随机结果容忍改变动作。完整validator另外只做非神经重建，不运行第三次模型。

E为canonical+replay中进入native评分的pair数，未知且0≤E≤A；最坏预算一律用E=A，不借Qwen eligible率估计硬上限。NLI的不适配/empty等只可按固定语义执行，不能为了预算跳过eligible分支。

| 工作 | 正式canonical+replay上界（不含预检） |
|---|---|
| 逻辑generation | `3A=95,580`；其中canonical94,500，replay1,080 |
| reader generation forward | 每逻辑调用prefill+decode总数≤max_new+1的保守计数，`≤163A=5,193,180`；必须另外记录实际nativeforward，不等同逻辑call |
| repair retrieval | `A=31,860`；BM25/dense/hybrid各10,620 |
| repair-query BGE | `2A/3=21,240` batch-one forwards；原池文档重嵌入0 |
| answer BGE | `2A=63,720` texts；按固定阶段batch≤16；不跨阶段合batch时forward上界保守`2A`，实际batchcount另记 |
| likelihood | 4E≤127,440 cell requests；缓存从空开始，neuralforward≤requests，cachehit只能引用同namespace已有durable witness |
| NLI | 2E≤63,720 branch invocations；**不是forward数**，见下式 |
| reader-matched fit | 恰好10；upstream fit0，replay/validators/synthetic fit0 |
| policy inference | 固定九policy，test18,000行与预先固定development参数replay；无新head，不把`.predict`或校准算术记作fit |
| resampling | 主analysis20,000 grouped draws；一次独立非神经全重建同20,000 draws；无新增resamplingseed、refit或Gold版本 |

令每个候选分支b的原evidence passage集合为P_b，word count为w(p)。原chunker每轮start至少前进1词，空passage至多一个chunk，故：

`c_b ≤ Σ_(p∈P_b) max(1,w(p))`；`Q_NLI = Σ_b c_b`；
`F_NLI = Σ_b ceil(c_b/8) ≤ Q_NLI`。

在gold-free池上，以固定retrieval top-k及其实际有界文档定义 `C*_d` 为任何合法retrieved分支的上述和的上界（可用该池最大的k个word counts之和）。于是 `Q_NLI ≤ 2A max_d C*_d`，更细预算按各dataset counts加权。**C*_d当前UNRESOLVED（U4）**；16,000字符渲染不限制NLI的原始passages。以后仅可在Gold/新answers关闭时做确定性的pool inventory，不能取Mistral实际“平均chunks”冒充worstbound。正式批次不得截断chunk数救预算。

预检额外上界：G_P=36逻辑generation；F_TF,P=27（24+3）；F_BGE,P=19（16+3）；F_NLI,P=19（16+3）；direct-reader stress F_DIR,P=65；无fit。generation forwards≤1956（3lengths×4repetitions×[(48+1)+(64+1)+(48+1)]）。故 reader全部forward保守上界 `163A + 1956 + 27 + 65 + 4A`，其他模型另加上述预算。修复retrieval的invented CPUfixture若不读真实pool，数量须在fixturemanifest中有限枚举；不产生benchmarkretrieval。

### G6.2 token 与 cost 公式

取 L_G=8192，L_TF=8192，L_BGE=L_NLI=512。**token是tokenizer各自的计数，不能跨模型当等价FLOPs**。保守计数：

`T_gen_input ≤ (3A+36)L_G`；
`T_gen_output ≤ 160A+1920 = 5,099,520`；
`T_teacher_input ≤ (4A+27)L_TF`，已包含答案tokens，不另重复加；
`T_teacher_answer ≤ (4A+27)×8191`（极保守，真实re-alignment另记）；
`T_direct_input ≤ 8192+64`（cached prefill+decode的新增输入计法），KV resident最大8256；
`T_BGE ≤ 512(2A/3+2A+184)`（预检136+3×16=184 texts）；
`T_NLI ≤ 512(Q_NLI+96)`（预检72+3×8=96 pairs）。

同时单列 padding-inclusive processed token slots：BGE `≤512×16(F_BGE)`，NLI `≤512×8(F_NLI)`；不要把文本tokens和padding开销混在同列。完整多模型总预算还含所有cold loads、retrieval CPU、serializer/fsync、tokenizer重建、hash/validation、bootstrap和封存。

以预检timed每类**最大**case wall与既定uncertainty multiplier `u_time`构造调度估计：

`T_plan = Σ_s n_load,s t_load,s + u_time[Σ_g n_g t_g,max + F_TF t_TF,max + F_BGE t_BGE,max + F_NLI t_NLI,max + N_ret t_ret,max + T_CPU + T_validation + T_copy]`。

必须测到长shape与CPUoffload每个native路径；greedy早EOS的普通timedcase不能估计完整maxdecode，用固定directstress界定该项。调度公式是基于syntheticwitness的估算，非数学runtime保证；硬bound由预先固定 `T_job_max`、阶段call/token/byte quotas和watchdog保证，超限终止不截结果。`u_time`、`T_job_max`、CPU/io系数、价率/能耗假设当前UNRESOLVED（U5）。费用公式 `C_max = rate_gpu×T_gpu,max + rate_cpu×T_cpu,max + rate_storage×B_retained×retention + fixed_acquisition`；本地GPU无租金不代表人工/占机成本0。没有可核验价率时不报人民币总额。

### G6.3 存储硬界：由schema计算，不能漏witness和副本

将每种记录的最大UTF-8 bytes上界在最终schema冻结中记为 s_type；由fixedkey/header开销、字符串最大bytes、数组元素数与整数/float的canonical serialization上界逐字段计算。不得从真实ledger最大行反推，也不得截断witness。需pin JSON格式（禁止NaN/Inf、固定floatroundtrip格式）、tokenID最大位数与vocab文件、prompt/answer/generationtext边界、top-k/文档bytes、labels派生字段及嵌套重复引用方式（U4）。尽量content-addressed引用共有文档，避免每事件重复整池，但不能靠未说明压缩比降低预算。

建议原始连续数组用固定dtype sidecar，schema/hash绑定：BGE FP32向量每条`768×4`bytes；pre-normalizationBF16向量每条`768×2`及norm标量；NLI每pair二类FP32logits`2×4`bytes；likelihood每target若为独立logsumexp保存词表logits，则保守`32768×4`bytes。究竟保存全targetlogits还是有独立来源的target-logit与logsumexp witness，必须事前定案，不能静默把后者叫“独立完整softmax验证”。完整target-logit保存可能极大，当前 U4 明确阻断；否则限制validation claim并经独立审查接受。

令 `J=8A+2(F_TF+F_BGE+F_NLI)+2×10+J_P+J_CPU`，其中8A是3gen+1repair-retrieval各intent/completion；autoregressive内层forward用已绑定call的逐forward witness，不把不fsync的hook冒充独立durablecall；TF/BGE/NLI每实际batch另外intent/completion。其余CPU/fit事件以冻结有限事件schema计数。一个可审查的无压缩上界是：

`B_science ≤ 3A s_gen + A(s_branch+s_repair) + F_gen s_gen_forward + 4A(s_TFrequest+s_TFwitness) + V_BGE s_BGE + Q_NLI s_NLI + J s_event + 10s_fit + 9N_T s_score_action + N_T s_outcome + 40000s_draw + s_protocol_manifests + s_immutable_logs`。

其中 `V_BGE≤2A+2A/3+184`；每个s包括按其真实最大数组形状确定的bytes，不允许同时把全logits和摘要都遗漏。`B_assets`须包括三shard/tokenizer/index/全部BGE/NLI/环境/历史模型，`B_inputs`包括允许复制的fixedcorpus/vectorarrays。正式固定保存canonical+replay+validator生产物，不做多份未记账cache。封存要求一份active加一份独立verified archival copy，保守：

`B_total_upper = 2(B_assets+B_inputs+B_science+B_preflight+B_failure_reserved)+B_working_temp`。

失败namespace永不回收以换预算；原有历史资产另计已占用disk，不凭硬链接假定不占空间。future disk free必须大于该上界再加预定reserve；`B_failure_reserved`含唯一失败attempt的partialworst输出，若成功与failure互斥可在有证明时用max，默认按和。实际磁盘容量、schema s_*、workspace/tmp peaks、保存全logits方案尚未闭合（U4/U5）。当前不能报一个假的“总GB够用”。

## G7. 数值契约、durable journals、独立验收与 Gold

### G7.1 不能把 Phi 失败变成新阈值经验样本

本协议不能继承对Phi的事后`.005`之类阈值，也不重验Phi。Mistral新验证规则必须标明受已知工程失败启发、在任何Mistral真实ledger前冻结；**不改共享BGE科学算子**。以下推导要求在static source/kernel审计和invented arithmetic fixtures中完成，容差表当前 U6，未通过即不可预检/benchmark。

对归一化的输入hidden h、native ε-clamp，原算子是 `y=round_BF16(h/max(norm_native(h), ε))` 后无损拓宽FP32。只验证 `abs(||y||−1)<某常数` 不足以认证算子，且h=0/clamp分支本不应强称unitnorm。必须保存pre-normalization h、native denominator/dtype、normalized y及source/实际kernel binding，独立重建分支与舍入。

一种可审查的推导模板是：若非clamp、normal-range且source证明 `|r_hat/r−1|≤η`，每分量division舍入相对误差≤u（BF16 unit roundoff 2^-8），则

`(1−u)/(1+η) ≤ ||y||₂ ≤ (1+u)/(1−η)`。

η必须由**真实**norm实现的accumulator/树规约/sqrt和输出舍入推导；可用已证明FP32 reduction的`γ_k=ku32/(1−ku32)`传播，但不能未经源码确认就假定Torch BF16 norm全程FP32。subnormal/overflow/ε-clamp另用绝对舍入界及精确分支处理，禁止直接套relativebound。η、clampε的实际dtype以及kernel路径目前未认证，故**本文不签发数字norm容差**。在不了解kernel时，把旧Phi最大偏差加余量不是推导。

ranking重建使用saved原FP32向量与固定pool矩阵/BLAS线程/运算顺序，精确重建rawdense/BM25/RRF数组及排序；新norm诊断不能替代此检查。保存向量/BF16量化结构可重建也不等于BGE模型forward已经跨机神经复现，scope要分清。

likelihood：保存真实input/target位置、dtype、targetlogits/logsumexp或完整targetlogits（见U4）、tokenlogprob与四格绑定；以independentFP64算术重算softmax/reduction，容差通过固定maxshape、finite logits范围/稳定logsumexp实现、累加次数及dtype传播推导。NLI保存全部二类logits，独立softmax、entailmentlabel、chunks与max/差值。CPUhead变换/coefreplay沿用既有 `1e-10` 固定验收上限，并事前用长短shape/极值/sigmoid边界的invented arithmetic证明其实现适用；若达不到不放宽。rawupstream savedparameter replay沿用原接受算术contract并披露scope，不再拟合。

所有离散身份、配置/源bytes、prompt/tokenIDs、eligibility/reason、排序ties/actions、journal linkage和generationreplay要求exact；不得用浮点容差放过离散差异。neural score replay的数值不等若超出预写错误模型即FAIL；即使在容差内，若导致固定action/ranking不一致仍FAIL，不能事后声明“近似等价”。取真实最大残差反推门限、放宽容差、另设misspelledfieldalias或跳过assert均视为实质协议修订，不能列普通bugfix后重跑。

### G7.2 pin 与 durable intent/completion

每调用前重新验证stageconfig/predecessorroot、offlineassetrevision和已封存source/environment graph。输入graph必须闭合真正被import/decoded的文件，包括native源码、模板compiler/Jinja绑定、执行wrapper、缓存路径、HF_HOME和所有metadata，而非仅方法函数hash。launcher、validator、independentclient三者的代码依赖和入口均记账，禁止把自行制造的PASS文件当receipt。

对每逻辑generation/repairretrieval、TF/BGE/NLIbatch、fit和重要CPUstage：

1. 在不可覆盖ledger中写intent，含runUUID、stage、global/callordinal、operation、identity、input/render/token/config/model/source/hash、parentreceipt、expectedoutputs与call预算；flush+OS durable sync成功后才可调用。
2. 调用完成后先写完整数据sidecar并flush/fsync，计算其真正内容hash；写completion，显式引用intenthash、实际rowhash、所有sidecarsha/bytes、实际forward/token/memory/time/cachereceipts、status；completion也durable落盘后才进入下一调用。
3. pertrace最终row bind三generation的**完整实际schema**、repair/query/vector/ranking、raw/evidence内容hash、provenance ordinal；只对摘取子字段hash不足以绑定完整row。规范清楚completion hash覆盖哪些字段，schema版本固定，不出现V2的3vs5字段fixture错配。
4. finalmanifest记录全部文件（包括失败日志、partial、journals、cache和前驱根），无排除隐藏有效载荷；manifest自引用按预先定义root算法处理，不能依靠忽略checks解释循环。独立重建schema/rows/callgraph并全量hash。

未配对intent、缺字节completion、重复callID、未记账forward/fit、mutation、未知schema、stdout成功而ledger失败、writer退出后还有后台写入，均终止FAIL。**本V1不允许resume或checkpointprefix续跑**，即使所有已完成行看似配对；不自动再launch不完整stage，失败部分不进科学分析。这个严规则增加现实失败成本，须在G8接受；不把partial9,540类事件作为可再用数据。所有fixtures必须在零模型stub下事前覆盖这些失败。

### G7.3 replay、prelabel与阶段访问

canonical/replay各独立writer和cache。完整validator不得importproducer或以其assert输出替代自己重建；可共用经pin的第三方tokenizer，但必须重建prompt/evidence/position而不信任producer准备结果。每个generationtoken/witness、每次retrievalranking与所有schema/crossledger数据全量检查；180replay只提供固定子集实际neural重复，不能描述为全量跨硬件复现。

development acquisition+replay真实性PASS后才可另开development评分和标签映射；其旧4,500题references仅用于生成Mistral R/EM/F1 targets、固定fit/cal，不进入question/evidence/score工程路径。以既有Qwenhistoricaloutcome当Mistrallabel是禁止的。原始target重复读取的来源限制继续记录。

test获取/评分/action processes从OS/file-guard层拒绝reference/support/decomposition/outcome文件，所有labelbearingdataset通过已认证gold-freeprojection取question/documents。绝不能因为同题Qwen已公开Gold而认为Mistraltest可提前打开。

18,000testpairs、七upstream/fivehead/V2参数、全部features/scores、commoneligibility、九policy完整actions、costreceipts、所有pins与independentprelabelvalidation封存后，才可能另行准入独立outcomeprocess。它只能物化固定6,000selectedreferences；不写rawreferences，不回写任何方法input，不修改score/action。独立metricvalidator用单独reference读取和normalizedEM/tokenF1实现重算所有metrics。未经最终Gold准入不得启动，即使stage名已经存在设计中。

一次analysis和independentfullrebuild后由Astra xhigh作真实性/公平性/Claim裁决，无论显著与否均终止本分支科学运行。保存全部失败；技术failure不能报告effect，scientificnull也不能触发工程retry。

## G8. 精度、最低实际意义、成本效益和出口

### G8.1 仅使用已公开开发聚合的规划换算

已有 `COST_AND_PRECISION_RESULTS.json` 的五个重叠development repetition是同4,500题的条件OOF/bootstrap诊断，**不是五独立复制**。取每端点五次bootstrap SD的最大值，不取最有利mean/seed。只做代数规划：

`SD_plan,e(u)=u×sqrt(4500/6000)×max_r SD_dev,r,e`，u∈{1,1.5}；
`H_plan,e(u)=Φ^{-1}(0.99375)×SD_plan,e(u)`，z≈2.498。

| 比较/端点 | worst原SD(pp) | n6000近似半宽 u=1(pp) | u=1.5(pp) |
|---|---:|---:|---:|
| C1 EM | 0.104588 | 0.226258 | 0.339386 |
| C1 Damage | 0.039337 | 0.085099 | 0.127648 |
| C2 EM | 0.086590 | 0.187323 | 0.280985 |
| C2 Damage | 0.037114 | 0.080290 | 0.120435 |

本表是已公开aggregate的算术换算，本轮未运行bootstrap/score/model。它不包含Mistral方差、expectedmeans、jointpower、拟合/校准不确定性或topK跨reader变化；不能报告“80%功效”或用这些半宽保证实际CI。来自五折OOFpolicy的SD搬到一个新固定panel仅是透明敏感性假设，1.5也不是上界保证。

Damage稀少时，jointsuccess常受Damage上界限制；0个观察Damage不等于trueDamage=0。bootstrap对从未观察的罕见事件不生成新信息，不能由退化区间推出安全保证。18,000行不是18,000独立样本，三个retriever同题相关。单trace事件对应100/18000≈0.005556pp，单question最多携带三个事件；离散性和动作排序变化不可忽略。禁止通过增加draw数解决事件稀少。

### G8.2 必须在任何实际预检前作出的价值判断

科学最低实际意义 `δ_EM` 与 `δ_Damage`（pp）及最大可接受半宽 `H*_EM,H*_Damage` **UNRESOLVED（U7）**。现有协议没有经科学论证的这些数值；本文不从Qwen已见均值、最小显著差异或Mistral未来结果倒推。它们不是自动新equivalence/noninferiority margins；严格主joint门仍对0。独立审查须以应用/论文知识问题明确“多小的增加正确答案/减少损伤仍值得完整计算账”，并在未见Mistraloutputs前给出理由和数值。

准入判定合同：审查同时检查最保守现有u=1.5规划半宽是否≤各H*，以及H*是否足以分辨预先声明δ；如不满足，不因u=1较有利改用它。若认为OOF→newreader不确定性使该近似根本无法支撑必要性，结论STOP，不构造虚假power。即使该gate满足，也只说明值得有限资源预检，不保证最终精度。

资源准入须事前冻结实际可承担 `T_job_max`、disk/hostRAM/commit/pagefile、token/forward/filecaps和保留成本；预检后按全部workload、coldloads/replays/likelihood/NLI/独立audits把cost公式填完。无法给出有意义上界或超出已定额度则STOP；不下调context、offloadmap、dtype、replay或validation以求过关。若有限inventedsuite不足以估计关键CPU/io/storage环节，只能在本次文档审查结束前补全零科学输出的合同，不在运行中追加预检循环。

### G8.3 最终报告与停止条件

可能的终局解释预先固定：

- C2在Mistral也通过：指定“fusion相对GbV-only”的Qwen发现于此同题reader条件复现；不能证明加入GbV优于HGB-only。
- C1仅Mistral通过：Mistral条件的新增GbV优势；Qwen同比较未过仍保留，不能写两reader普遍优势或显著interaction。
- 任比较收益与Damage方向冲突：报告权衡；只有窄CI排除有实际意义的效应才可讨论受限增量，不能把“不显著”直接当无效/等效。
- 全部CI太宽、资料/成本/来源限制使新增知识不足：保留完整结果，结束当前CAS Q2扩展，转透明技术报告。不新reader、新ID、seed、head、预算、RECA或方法搜索救场。

以下任一触发STOP：G0贡献理由不足；G2/G3公平性不能完整维持；U1–U7不能在相应阶段前闭合；正式预检唯一producer/validator/client任一FAIL；资源超上界或未记录迁移/计数；benchmark任何真实性/审计/Gold边界失败；fit类/收敛失败；唯一科学分析结束后缺乏足够精确的新增发现。失败不可用forensic代替frozenPASS，当前Phi历史也不得因新分支成功改写。

## 9. G0–G8 逐项自评、缺口所有权及允许下一步

`DESIGN_DEFINED`只代表科学条款已写定；`EVIDENCE_PENDING`代表必要futurewitness尚无，绝不表示自动授权取得。`UNRESOLVED_BLOCKING`必须在GO审查填定或STOP。

| Gate | 本稿覆盖与当前自评 | 未闭合项/关闭证据 |
|---|---|---|
| G0 | DESIGN_DEFINED | 提出明确C1未闭合增量/C2条件边界；最终发表价值受G8约束，非已获创新PASS |
| G1 | DESIGN_DEFINED + UNRESOLVED_BLOCKING | U1：确切accepted input graph、development replay hash、test identities的非Phi来源绑定；所有新namespace未创建 |
| G2 | 科学对象DESIGN_DEFINED；工程绑定UNRESOLVED_BLOCKING | U2/U3：完整资产与template/render/tokenization/placement/config、eligibility/missing truth table source绑定；未run/fit |
| G3 | DESIGN_DEFINED | 九policy角色/监督/动作预算固定；V2/七upstream确切artifacts纳入U1，无新baseline选择 |
| G4 | DESIGN_DEFINED | 2×2、20000、seed、jointCI、固定models/重分配与次要规则锁定；未来实现与独立explicitcopy gate未执行 |
| G5 | CONTRACT_DEFINED + UNRESOLVED_BLOCKING + EVIDENCE_PENDING | U2/U3/U5/U6：资产、真实CPUexecution、finitefixturemanifest、host/io硬额度、数值推导；actualmemory/throughputwitness全缺 |
| G6 | 公式与有限调用DESIGN_DEFINED；数值总账UNRESOLVED_BLOCKING | U4/U5/U6：C*_d、serialization/logits/storageclosure、时间价率资源cap、数值算术contract；不虚构总费用 |
| G7 | CONTRACT_DEFINED + UNRESOLVED_BLOCKING | U1/U2/U3/U4/U6：所有pins、durableschema、independentvalidator全图与误差证明；尚无MistralprelabelPASS |
| G8 | 聚合规划已给出；价值/可负担性UNRESOLVED_BLOCKING | U7：最低实际意义与precision要求；U5：可承担成本cap；必须review而非本稿自行GO |

缺口清单与最迟门：

- **U1 前驱/身份/原始artifact完整绑定**：只读acceptedrecords补足；在任何benchmark input-freeze前关闭。invented-only阶段只需其不含benchmark的资产/源码前驱，不能先偷读真实样本。
- **U2 资产与tokenizer完整bytes/metadata**：metadata引用不能替代LFS/完整filehash；在任何模型load前，依独立资产准入关闭。本文件不许可acquisition。
- **U3 source/config/schema/真正offload执行设计**：零模型静态设计和inventedfixtures规范先冻结；在任何实际inventedpreflight前关闭，禁止执行时选hooks/缺失规则。
- **U4 可计算workload与存储**：NLI corpus界在Gold-freeinputmetadata阶段关闭；serialization/logitswitness设计和预检存储必须在预检前关闭，全study界在benchmark前关闭。不能因未获真实inputinventory权限就臆造总量。
- **U5 资源硬额度/成本假设**：预检与正式job上限、disk/host预算由重大审查在预检前给定；finitewitness只填时间系数，不改上限。
- **U6 数值误差推导与独立验证可实现性**：在预检前关闭算术规格，inventedwitness检验实现；实际不符即FAIL，不重新拟合容差。
- **U7 最低实际意义与可解释精度判断**：在预检前关闭；无法给定合理门则STOP，不能先消耗模型计算期待看到效果再决定值不值得。

下一允许动作仍然只有**对本外部文档作独立重大科研 GO-for-one-invented-preflight / STOP 审查及文档缺口闭合**。当前没有无条件GO；若审查认为U3/U4/U5/U6/U7无法在文档证据中成立，直接STOP。若未来准入仅覆盖资产和invented-only，则不能跨越到full-input tokenizer、benchmark、fit或Gold。正式工程冻结须exactimplementation/pins/fixtures经独立审计；资源PASS后还须新的clientgate逐段授权。

P0：研究必要性/precision、前驱真实性、数值契约与有限预算；P1：命名reader广度、可核算成本、独立释放/重放与历史training来源；P2：全部新方法/reader/head/feature/seed/budgetsearch保持关闭，期刊年度CAS/ISSN/大类小类与机构规则另于投稿前核验。没有论文手稿或投稿执行许可。

## 10. 阅读快照与本轮操作声明

本稿引用repo治理、AGENTS、EMPIRICAL_REPLICATION_PROTOCOL_V1、PHI_READER_REPLICATION_PROTOCOL_V1、CURRENT_METHOD、既有selection/placement/metadata材料、DEVELOPMENT_PRECISION_PROTOCOL与其已公开COST_AND_PRECISION_RESULTS，并只读相关eligibility/GbV/BGE/likelihood源码。源码读取不等于运行或新实现审计通过。原worktree身份按本轮读取时HEAD 8088014e768349725ca6f1c4f0343b68c329616a且clean；其他并发文档后续变化属于新的快照，不自动称当前hash失败。

| 本轮输入快照 | SHA-256 |
|---|---|
| repo POST_PHI_FAILURE_RESEARCH_GOVERNANCE.md | `ecaf663edd3e5ffdb7a15569bf6c2932a0168865a90305377ee418ed5fcd9fb4` |
| repo EMPIRICAL_REPLICATION_PROTOCOL_V1.md | `86e882fb9edafaaf301b3a2494ef39485d43d98aac3fc4e8be97f9ba7e54691c` |
| repo COST_AND_PRECISION_RESULTS.json | `e16faff35811f95d10ea9b1bbfb3be715cba5ca46ec84ec1827e79c39835eb09` |
| repo src/verification/gbv_nli.py | `a9ca2f6391b91fec2b56c309bdfb2543ff0a6ae9c5f8cfe89ff7e14358c11503` |
| 原workspace src/retrieval/dense.py | `15e96f4f63336d694cef46421bbe3461cd0c095eba3af86a0fb78b36d0df91d2` |
| 原workspace src/scoring/reader_likelihood.py | `95952596de1e871bea4f565eaf8b4f8c54ed523e1c0ee66575b0896afd7cbb17` |

本轮新增科学fits=0，模型/tokenizer/神经forward=0，bootstrap=0，Gold/reference读取=0，ID选择=0，下载=0，repo修改=0。仅对已公开聚合SD作标明的规划算术，创建本外部Markdown草案。

**终态：`DRAFT_COMPLETE_WITH_UNRESOLVED_GATES_NO_EXECUTION`。CAS Q2 STATUS: NOT READY。**
