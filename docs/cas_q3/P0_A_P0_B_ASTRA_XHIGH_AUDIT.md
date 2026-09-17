# CAS Q3 P0-A / P0-B 独立科研终审

日期：2026-09-13（Asia/Shanghai）  
审计角色：GPT-6 Astra xhigh  
唯一裁决：**REVISE_P0_A_P0_B_BEFORE_CLOSURE**  
**CAS Q3 STATUS: NOT READY**

## 1. 最终结论

**两份文件均判 REVISE；当前 P0-A、P0-B 均不能关闭。** 主要障碍是最直接近邻的实质重叠未完整列出，以及一个明确错误的 Damage 排名 Claim。其余为增量归因、评估对象和单位的必要澄清。它们可以通过有界文档修订解决；本次没有发现要求撤销已接受 Qwen D 计算结果的证据。

| 审查对象 | 判定 | 理由 |
|---|---|---|
| Q3 Qwen-only 经验论文路线 | 维持 | 有效 Qwen 结果可作为条件性科学核心；目标转向不降低真实性、公平性和复现标准 |
| 不主张新算法的决定 | 通过 | 普通监督融合、双答案选择、成对验证差分、选择性修复均有直接近邻；HGB 仍是上游信号，HGB_GBV_R 仍是经验比较政策 |
| P0-A 文献覆盖与经验差异 | REVISE | 文献家族覆盖基本适当，但增益预测论文 v3 的成对 NLI、双答案预测器和实际选择实验被低估 |
| P0-B 数值转录 | 已核对一致 | 九政策总体点估计、六端点主区间、同 draw 固定动作敏感性与封存 JSON 一致 |
| P0-B Claim 映射 | REVISE | C5 将八个 switching policies 的最低 Damage 错写成九政策最低；C7 池身份不精确，单位和来源定位应补齐 |
| Submission Ready / 期刊接收 | 未通过 / 未判定 | P0-C 至 P0-I 未闭合；具体期刊、CAS 年度及适用大类/小类和机构规则未确定 |

唯一下一允许步骤是修订本报告 R1–R6 指出的文档，再对修订字节做独立复审。不得用此裁决启动新实验、新 baseline 推理、新 reader、新方法搜索或论文正文。

## 2. 审计对象、权威链与实际范围

工作树为 `E:/paper/ReliableRAG-cas-q2-p0-1`，阅读时 HEAD 为 `6900bc851d076a02044153105bdf800d67c88d7c`。两份被审文件当时未跟踪；`CURRENT_METHOD.md`、`CURRENT_TASK.md`、`EVIDENCE_INDEX.json` 有并发工作改动。这是明确的阅读快照，不是宣称它们已经提交或出现哈希失败。

本次读取 AGENTS、Q3 PROJECT_CHARTER / TARGET_TRANSITION / CURRENT_METHOD / CURRENT_TASK / EVIDENCE_INDEX、两份被审文件，以及 Q2 有效研究协议、C1 公开元数据、D 接受记录、fresh-result 决定、成本接受记录、GbV source-fidelity 记录、Phi 终局失败和 Mistral STOP 记录。只读取已经接受的聚合 `POINT_ESTIMATES.json`、`INTERVALS.json` 并核对哈希；没有读取逐题 Gold、reference strings、答案 payload 或 private group-order 内容。

这次是文献、聚合结果和 Claim 审计，不是重跑 D，不替代 P0-C 的完整方法/公平性审查、P0-D 的统计实现复审或 P0-G 的发布复现验收。旧 Q2 文档中的历史 next-step 指令由 Q3 正式转向覆盖；旧文档保留，不能据其历史措辞重启实验。

## 3. 必须修订项

### R1 — P0-A 第 32 行：补齐最近增益预测工作的实际重叠

当前表格仅描述“question, passages and generated answer”，容易把“固定双答案”误当作主要差异。实际链接当前指向 Dado、Carmel、Kurland 的 **arXiv:2604.07985v3，2026-08-19**。应固定此版本，并明确三点：§4.3.1 已有两答案 entailment 分数差；§4.3.2 的 Bert-Gen-2A 同时读取两个答案；§7 实际评估 predicted-gain 驱动的 Selective RAG，不能将其写成只有预测相关性而没有选择政策的工作。[原文 v3，§4.3、§7](https://arxiv.org/html/2604.07985v3)；[版本历史及 CIKM DOI 元数据](https://arxiv.org/abs/2604.07985v3)。

修订后的剩余差异只能是：本项目研究 **original-RAG / repaired-RAG** 固定候选上的监督匹配信号归因，两个单信号控制和两信号控制使用相同配方，在全局固定 900 次动作下分别报告全总体正确性与损伤，并保留未通过的比较。不能再用“双候选”“post-generation”“NLI 差分”“学习是否有益”作为独占新意。

这项修订不要求当场运行 Bert-Gen-2A。它是必要的概念近邻，不是本次已执行的数值 baseline；本项目没有证明优于它。若目标期刊要求与此类完整系统作数值竞争，现有 Qwen-only 证据不能支持 SOTA 论文定位，应重新审查投稿适配，不可暗中追加结果驱动实验。

### R2 — P0-B C5（第 88 行）：改正最低 Damage 比较集合

封存结果中 `Keep.damage=0`，`HGB_GBV_R.damage=11`。所以“among the nine policies”在字面上错误。

可允许的登记措辞为：**HGB_GBV_R 在八个均执行 900 次动作的 switching policies 中，具有最低观测全总体 Damage count/rate；Keep 的 Damage 为零。** 这仅是点估计排序，没有最优性、总体无害性或泛化保证。Keep 必须继续留在九政策表内。

该错误即使源于旧 Q2 解释中的宽泛措辞，也不能在新的 Q3 Claim authority 中沿用；无需修改或覆盖旧历史文档。

### R3 — P0-A 第 65–66 行：让增量归因方向明确

“comparison-dependent value boundary for the adapted external verifier”仍可能让读者把通过的比较理解成“外部 GbV 带来了联合收益”。必须在 P0-A 本身写明以下方向，与当前 Q3 CURRENT_METHOD 保持一致：

| 比较 | 所检验的附加信号 | 已接受结论 |
|---|---|---|
| HGB_GBV_R − GBV_ONLY_R | 在 GbV 上加入 HGB | 联合 EM 改善 / Damage 降低门通过 |
| HGB_GBV_R − HGB_ONLY_R | 在 HGB 上加入 GbV | 联合门未通过；主分析 Damage 端点有利，但 EM 不确定，固定动作敏感性 Damage 上界触零 |

因此可以说“两种信号增量的证据具有比较依赖性”，不能说“证实外部 verifier 对 HGB 的联合增益”，也不能说“GbV 无用”。一项显著、一项不显著，不是两种效应差异、交互或因果机制的正式检验。

### R4 — P0-B 身份绑定及 C7、P0-A 第 80 行：明确实际 reader 与三个池

P0-B 应直接给出或唯一链接到：`Qwen/Qwen2.5-3B-Instruct@aa8e72537993ba99e69dfaafa59ed015b17504d1`。仅说“named Qwen”而未命名不是充分的读者身份登记。完整运行配置仍归 P0-C；这里不要求重复所有工程细节。

`EMPIRICAL_REPLICATION_PROTOCOL_V1.md` 的池定义是每个 dataset 构造一个共享 deduplicated pool；C1 已接受聚合数分别为 HotpotQA 19,352、2Wiki 11,746、MuSiQue 23,618，总计 54,716。应将“one realized candidate pool”改成 **three fixed dataset-specific bounded candidate pools, shared across compared policies/retrieval conditions within each dataset**，或精确等义中文。一个研究批次/一个 candidate-generation pipeline 不等于一个跨三数据集混合语料池。

不能据此声称全 Wikipedia 检索、外部总体独立复制或三个独立 reader。18,000 是 6,000 question groups 的三检索条件展开，bootstrap 也不是将 18,000 行视作独立题目。

### R5 — P0-B 表头、指标定义和来源定位：消除单位歧义

九政策表中的两个 `Damage` 列分别改为 `Damage count`、`Damage rate (%)`；`EM/F1` 标出 `%`，所有 delta / comparison range 标出 `pp`。明确：

- Recovery：执行 switch 后 EM 从 0 到 1 的计数。
- Damage：执行 switch 后 EM 从 1 到 0 的计数。
- Neutral：其余已执行 switch 的计数；不是完全没有 F1 变化。
- `Damage rate (%) = 100 × Damage count / 18,000`，不是除以 900 或原本正确的 3,238 行。
- `Delta EM (pp) = 100 × (Recovery − Damage) / 18,000`。

P0-A 使用 Rescue、P0-B 使用 Recovery；应统一为封存字段 Recovery，或显式说明二者指同一 0→1 事件，不能暗中定义第二种指标。信号名称含 faithfulness，不意味着本研究的 EM/Damage 验证了真实 faithfulness 改善。

补上 analysis manifest 的实际路径 `outputs/cas_q2/empirical_analysis_v1/SHA256_MANIFEST.json`。为“完整映射”附以下定位即可，无需复制每个 secondary cell，也无需重算：

| 报告对象 | 封存 JSON 定位 |
|---|---|
| 九政策总体 | `POINT_ESTIMATES.json: policies.<policy>` |
| 三个 ordered point comparisons | `POINT_ESTIMATES.json: comparisons[]`，按 `left/right` 匹配 |
| 主比较区间 | `INTERVALS.json: reallocated.comparisons[].endpoints.<endpoint>` |
| 固定动作敏感性 | `INTERVALS.json: fixed_action.comparisons[].endpoints.<endpoint>` |
| dataset / retriever / cross cells | `POINT_ESTIMATES.json: fixed_global_action_breakdowns.dataset / retriever / dataset_x_retriever` |
| secondary 95% 区间 | 各 endpoint 的 `secondary_unadjusted_95_range_pp` |

### R6 — 先修正文档，再同步关门状态

目前 P0-A 开头、P0-B 开头/末尾、CURRENT_TASK 第 53/56 行和 EVIDENCE_INDEX 已宣称 CLOSED / completed。独立终审不能确认这些状态。应先保留本轮 REVISE，修完 R1–R5 后，以修订后的 A/B 文件及具体 SHA 复审，再同步状态索引。

通过 A/B 也只关闭其各自范围；不得由“两个 P0 已过”推出 Submission Ready，不得跳过 P0-C 至 P0-I。此项是交接要求；本审计没有修改任何 repo 文件。

## 4. 直接邻近工作覆盖的独立判断

现有 13 行覆盖了恰当的任务家族，**不需要无限扩展文献数量**。但引用存在不等于已准确呈现最近工作的机制。下列判断只认证相应概念边界，不认证外部论文全部数值或其工程正确性。

| 近邻与一手来源 | 独立核对后的结论 |
|---|---|
| [Generate but Verify，IJCNLP-AACL 2025](https://aclanthology.org/2025.ijcnlp-long.56/) | AwF 区分正确性与忠实性，并连接 faithfulness 评估和 downstream fallback。现有主任务边界合理。项目必须使用“paired adaptation of GbV Post-Answering NLI”；不能把本地 own-evidence 差分称作者的 paired-policy 公式或数值复现。具体 recipe 沿用已读 `GBV_SOURCE_FIDELITY_REVIEW.md` 的接受范围。 |
| [TrustMargin v1，§3](https://arxiv.org/html/2606.08397v1) | 已生成 Direct/RAG 两答案后，以 question-only、question+passages、passages-only 三种似然视图组成先验及绑定 margin，不再生成新答案。A 的概念边界基本正确；本地 E0/E1 四格不能冒名实现它。 |
| [Gain prediction v3，§4.3 / §7](https://arxiv.org/html/2604.07985v3) | 是本次最实质的覆盖缺口；须执行 R1。不能把本地双答案/成对 NLI/选择动作当成该工作没有的对象。 |
| [D2R-RAG v1](https://arxiv.org/html/2606.29377v1) | 诊断和选择 repair operations，并以 latency/VRAM 约束及 contextual bandit 表述预算；本项目只在候选获取后固定动作数量。A 正确区分 action allocation 与实际计算预算。 |
| [When Should LLMs Search? v1](https://arxiv.org/html/2607.05752v1) | 已有 no-search / forced-search 配对结果监督搜索路由。A 对行动时点的区别合理，但“结果衍生监督”不可作为新意。 |
| [Pair-ID v1](https://arxiv.org/html/2608.08944v1) | 固定失败状态做证据增删的离线配对响应审计；与本项目全 trace selector 的决策对象不同。该差异不足以清除算法创新。分别冻结 cohort 不等于已经证明两篇工作的样本交集为零。 |
| [Doctor-RAG v1，§5.2](https://arxiv.org/html/2604.00865v1) | post-hoc 修复失败的 agentic trajectories、定位早期失败并复用 prefix。A 对已知失败总体与全部候选总体的区别合理。 |
| [CRAG v1，§4](https://arxiv.org/html/2401.15884v1) | 检索 evaluator 根据质量触发 refinement / web evidence，再生成答案；A 的选择时点边界合理。 |
| [Self-RAG 原文，§3](https://arxiv.org/html/2310.11511v1) | 训练 generator 输出 retrieval / critique tokens，控制检索和生成；不是冻结 reader 后仅拟合 selector。OpenReview 获取受限时采用作者 arXiv 全文核对。 |
| [Adaptive-RAG，NAACL 2024，§3.2](https://aclanthology.org/2024.naacl-long.389.pdf) | 训练 classifier 路由 no / single / multi-step retrieval，属于候选生成前策略。A 的任务边界合理。 |
| [Self-Knowledge Guided Retrieval，EMNLP 2023](https://aclanthology.org/2023.findings-emnlp.691/) | 官方论文页已明确 retrieval 可能损害原回答，并提出自适应使用外部资源；A 不能把避免检索伤害作为新发现。 |
| [Verify-and-Edit，ACL 2023](https://aclanthology.org/2023.acl-long.320/) | 用外部知识 post-edit reasoning chain；A 的“修订生成”与“固定候选选择”区别合理。 |
| [Detrimental Contexts，EMNLP 2023](https://aclanthology.org/2023.findings-emnlp.776.pdf)；[The Distracting Effect，ACL 2025](https://aclanthology.org/2025.acl-long.892/) | 已有 detrimental context 分析及 distracting passage 识别/训练工作，支持伤害动机，不能支持本项目首次发现 retrieval harm。 |

一手原文的阅读限制需要透明：本轮 GbV PDF 多次返回服务错误；本次没有将这些失败记为全文重新核验。对该论文的任务定义使用官方 ACL 页面，对本地 recipe 的来源与复现边界使用已接受的 source-fidelity 审查。部分背景工作的深层实现不在本轮独立复现范围。决定 R1 的 v3 原文以及 TrustMargin、D2R-RAG、paired-routing/repair 等直接机制内容已读取，不以搜索摘要代替核心碰撞判断。

经过 R1 修订后，可以给出的判断是“选定近邻下仍有狭窄、可能值得发表的经验归因问题”，不是“证明经验发现首创”，也不是“达到任何已指定 Q3 期刊的贡献标准”。期刊科学兴趣和适用分区仍属 P0-H。

## 5. 聚合数值和 Claim 终审

封存点估计、区间及 analysis manifest 的 SHA 全部与 P0-B 所列一致。核对未发现三张数值表的实质转录错误；四位小数表述与原始聚合值一致。以下比较不能因目标由 Q2 转向 Q3 而变化：

| Ordered comparison | EM 差，pp [调整区间] | Damage 差，pp [调整区间] | 联合门 |
|---|---:|---:|---|
| ROA-FULL − HGB_GBV_R | +0.0444 [−0.1333, +0.2037] | +0.0611 [0.0000, +0.1278] | 未通过 |
| HGB_GBV_R − HGB_ONLY_R | +0.0556 [−0.1556, +0.3167] | −0.0833 [−0.1833, −0.0056] | 未通过 |
| HGB_GBV_R − GBV_ONLY_R | +0.2333 [+0.0722, +0.4333] | −0.0722 [−0.1444, −0.0278] | 通过 |

这三组依次对应 `(+8 Net,+11 Damage)`、`(+10 Net,−15 Damage)`、`(+42 Net,−13 Damage)`。最后一组不是“恢复 42 个独立问题”：它是 18,000 trace 条件上的额外正确事件净数，存在 question siblings。2Wiki、HotpotQA、MuSiQue 或单一检索器上的有利 cell 不构成新的确认性结果。

主分析为 20,000 次 dataset-stratified question-cluster draws，每 draw 重新全局分配 top-K，六端点 family 的分位点为 0.004166666666666667 / 0.9958333333333333。固定动作敏感性只有 fusion − GBV_ONLY_R 仍通过联合规则，不能用于替代主分析或挽救另外两组。无须也不允许本次重算 bootstrap。

| Claim ID | 本次处理 |
|---|---|
| C1 | 保留为唯一联合主阳性；必须绑定 R4 的 reader / cohort / retriever / pools / K 和精确 comparator |
| C2 | 保留“不支持联合优势”；不能改写为两方法等价、GbV 无效或单端点无差异 |
| C3 | 保留“不支持 ROA 推进”；点 EM/F1 第一名不能凌驾于主规则 |
| C4 | 保留八政策对 Keep 的正点 EM/F1 描述；不追加八组显著性措辞 |
| C5 | 必须 R2 修订；当前陈述错误 |
| C6 | 保留普通两输入监督政策身份；补 R3 的归因方向及 GbV adaptation 边界 |
| C7 | 必须 R4 修订；不外推 reader、总体或 corpus 范围 |
| C8 | 保留 fixed-model / realized-pool 条件性；无 refit uncertainty、exact coverage、equivalence、noninferiority 或风险保证 |
| C9 | 保留“本研究共同获取和评分图”的成本边界；不据此推断每种独立部署都会需要相同计算 |

在 A/B 修订后，科学核心仍可以是 **Supervision-Matched Selection of Paired RAG Repairs: An Empirical Study of Accuracy and Damage** 所指的经验问题；标题不能使读者误认新的 repair generator、全系统计算预算保证或新风险控制算法。最终标题仍须经过后续稿件 Claim 审查。

## 6. 禁止项、其余 P0 和停止条件

本轮关门审计不能放行以下事项：Phi 拟合/评分/Gold 或 V5；Mistral 预检/下载/模型工程；RECA 或其他新方法搜索；追加 reader / feature / budget / seed / head；挑选新的有利 subgroup；重跑已封存 D；稿件正文；补造历史 fit receipts 或未测成本。第三 reader 和独立算法不是此 Q3 经验路线的机械前提，也不是失败项目的救援许可证。

必须继续披露七个原始 estimator 的 fit-time ID/matrix receipts 与原始拟合独立 witness 缺失。Phi 的 frozen semantic gate 终局失败不等于其每个 runtime witness 都伪造，但其输出不得进入科学结果；Mistral 无科学效应数据。不能把工程失败包装成反证，也不能把其大量 trace 数包装成复制支持。

成本接受的是共享执行图：54,000 canonical generation receipts 包含 acquisition 的工作，900 次输出切换不意味着只花 5% 的生成成本。未测 standalone-policy latency、统一 end-to-end latency、canonical C2/C3 peaks 和 FLOPs 必须保留，stage timers 不能随意相加。完整表仍归 P0-F。

P0-C/D/E/F/G/H/I 继续开放。若准确披露最近工作后，目标期刊认为剩余问题只是重复的简易融合榜单；或论文核心需要未支持的 GbV 增量/普遍融合优势；或必要审稿材料的公平性、溯源和可交付性无法成立，则暂停投稿路线。不能靠删强控制、隐藏失败、降低 Phi 阈值或把预印本近邻遗漏来解决。

P0-A/B 关闭的充分条件是 R1–R5 被可核验地完成、R6 状态与独立复审一致，同时不改动任何封存科学结果。是否关闭本研究的全部 Submission Ready 门是另一个决定。CAS 分区年度、ISSN、大类/小类及机构认定未定，本次没有猜测或认证任何期刊分区，也不签接收概率。

## 7. 阅读快照 SHA-256

下表路径除特别说明外均相对上述 worktree。审计结果文件自身 SHA 由写入完成后的外部命令返回，不进行自引用。

| 文件 | SHA-256 |
|---|---|
| docs/cas_q3/P0_A_DIRECT_NEIGHBOR_LITERATURE_AUDIT.md | `e17db232f5e722a7ed64ca3f5d9fef5ddb403b00c3585fa5fd3414f6b2694b32` |
| docs/cas_q3/P0_B_RESULT_CLAIM_MAP.md | `10e8cf4310917abe432e8992d21e03d6268ca8cea97ee969780404187fc97dd5` |
| docs/cas_q3/PROJECT_CHARTER.md | `a4ccc791214f17447c9deb8c6703b88e468803a5ca13093d3fbf992e5944e879` |
| docs/cas_q3/TARGET_TRANSITION.md | `b6dd69153db3f90b90874fce65d4c026a601aac292b184ae3557b20bd8bdcf64` |
| docs/cas_q3/CURRENT_METHOD.md | `c8c60806a320d4e80f11d233c7214819ad375499256a1e7a782ca16578845527` |
| docs/cas_q3/CURRENT_TASK.md | `f574106e889eb30df2d2df063bf203144b115acecafe990d1103eaffad909641` |
| docs/cas_q3/EVIDENCE_INDEX.json | `cf3d4e6e2316fec18aeeda1f14d87b801c108c20f512be16a6e5603f7ecf8113` |
| docs/cas_q2/EMPIRICAL_REPLICATION_PROTOCOL_V1.md | `86e882fb9edafaaf301b3a2494ef39485d43d98aac3fc4e8be97f9ba7e54691c` |
| docs/cas_q2/EMPIRICAL_C1_RESULTS.json | `a21d8eadd43946ea2f55511b6ad04b2d3f5267390be1bef9f0fe9cff63ed399d` |
| docs/cas_q2/P0_3_FRESH_RESULT_DECISION.md | `7e3c450b83e373b5ab8e60cbc35a3342d9efbaf41e6c84885f512e95ebda8870` |
| docs/cas_q2/EMPIRICAL_D_ACCEPTANCE.md | `839989e744c74df5deb5b54a2cba8f4bf75e9ef11470d38901efd1ef29f30e85` |
| docs/cas_q2/EMPIRICAL_COST_ACCEPTANCE.md | `901775251f3dd2478cf11f65dea0fafb2d7557bc520ea10ef5c5e864e24819cb` |
| docs/cas_q2/PHI_READER_DEVELOPMENT_RUNTIME_V4_FAILURE_ACCEPTANCE.md | `ebf7a49010e0752fa3a52bba3099fe5429bab6cd47e4faf779c86e1fd29a26b3` |
| docs/cas_q2/MISTRAL_EMPIRICAL_EXTENSION_PROTOCOL_GO_STOP_REVIEW.md | `2fbef9e52ad2ed7dd32c708f8d3ed46cb5069259175e780a12ce39d00b36bf4a` |
| outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json | `b03ddad8fa35f582a63403c029942104c3f5da1a961110edc2a62f09871f4d3b` |
| outputs/cas_q2/empirical_analysis_v1/INTERVALS.json | `6d454afeec7c125c0cc4d182556af6db214a867aa4f62f7a6fbd1e6e22b09331` |
| outputs/cas_q2/empirical_analysis_v1/SHA256_MANIFEST.json | `498b83e75538032de3711bd6ce190eac049631d8393c875744d83aa0318097f6` |

操作声明：repo 修改 0；Gold / reference strings / private ID selection 0；tokenizer / model / neural forward / scientific fit / score / bootstrap 0；实验或模型资产下载 0；只读核验与本外部 Markdown 文件写入。只读查找中个别假定文档路径不存在、网页 PDF 获取失败，均不构成科学 attempt，也未被冒记为验证通过。

**唯一裁决：REVISE_P0_A_P0_B_BEFORE_CLOSURE。**  
**CAS Q3 STATUS: NOT READY。**
