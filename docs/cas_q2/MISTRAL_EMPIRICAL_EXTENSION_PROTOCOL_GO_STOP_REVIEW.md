# Mistral 经验扩展协议独立 GO/STOP 审查

External independent review receipt SHA-256:
`4efaf1725d6ed80ba85548dd507513aed1ffd5f511247cc0b4063ad64da79481`.

日期：2026-09-13（Asia/Shanghai）
独立审计员：GPT-6 Astra High
唯一裁决：**STOP_MISTRAL_EXTENSION_BEFORE_ENGINEERING**
**CAS Q2 STATUS: NOT READY**

## 1. 裁决与范围

拒绝将当前草案推进到工程或 invented-only 预检设计准入。本文是最终 STOP 审查记录，不是有条件放行，也不授权下载、tokenizer、模型、fit、科学评分、Gold、预检、另一个 reader 或新方法搜索。

草案已写明多数科学对象及失败边界，且没有把 Phi 失败伪装为 accepted predecessor。但 U3、U4 的预检 witness/序列化部分、U5、U6、U7 都是草案明文要求在预检前闭合的文档前提，当前仍未定案。独立审计不能用“以后实施时补齐”替代这些前提，也不能自行创造没有应用依据的最低效应或可承担资源额度。仅这些缺口就足以 STOP，不需要等待一次实际 OOM、验证失败或无效结果。

审查对象是外部 `MISTRAL_EMPIRICAL_EXTENSION_RESEARCH_PROTOCOL_V1_DRAFT.md`，实际 SHA-256 与要求一致：

`787b6a3992988d31dccbc2a4c75561c51f498e1e555797cb5721096d336d70cf`。

repo 检查时 HEAD=`8088014e768349725ca6f1c4f0343b68c329616a`，`git status --short` 为空。已读取指定治理、选择、Phi 失败、Qwen/Phi 科学协议、公开 COST_AND_PRECISION_RESULTS 及 EVIDENCE_INDEX 的当前状态与记录；另只读既有 Mistral config/index 和相关 GbV、BGE、likelihood 源码以核对公式与语义。未读取逐样本答案/Gold、未选择或重新抽取 ID。

## 2. G0–G8 独立裁决

| Gate | 独立发现 | 本次判定 |
|---|---|---|
| G0 必要性 | C1 检验在 HGB 上增加 GbV，C2 检验在 GbV 上增加 HGB；方向正确，保留 Qwen 不同结论，承认复杂性不成立。正、负、权衡都有潜在信息。但信息是否足够有用仍依赖未定 G8，不能凭第二 reader 数量判断发表价值。 | 研究问题成立；完整必要性未通过 |
| G1 前驱/隔离 | Phi 终止与旧投稿链关闭明确；禁用 Phi 科学 payload 和失败执行 PASS；身份清单只允许经 Qwen/历史来源重新绑定。新 root 和一次性 attempt 原则清楚。U1 的完整 accepted graph、development replay hash、非 Phi 身份绑定尚缺。 | 没有发现明确复用失败 Phi 的许可；完整前驱未闭合 |
| G2 固定对象 | 4,500/6,000 groups、13,500/18,000 traces、3,600/900 fit/cal、五 heads、七原始 upstream、K=900、Recovery target 和配方与有效历史科学合同相符。exact EOS/pad/fast/slow/attention、完整 eligibility/missing truth table 仍交由 U2/U3。 | 对象和主要配方固定；执行会影响科学数值的分支未封闭 |
| G3 公平性 | fusion 与两个单信号控制同监督/候选/资格/动作预算；五 heads+raw HGB+raw GbV+Keep+V2=九 policy。V2 次要，排除额外 Qwen panel transport 是当前新分支明示选择，未暗中弱化主要对照。完整 artifact/schema 尚欠 U1/U3。 | 主要公平结构合理；不等于公平执行已获证 |
| G4 统计 | 两比较×两端点，20,000 grouped draws，每 draw top-K 重分配、fixed panel、不重拟合、四端点 Bonferroni 和严格联合门一致。不以 reader 各自显著性差异断言交互。精度是否有意义仍缺 G8。 | 统计 estimand/主次结构在文档上成立；实现与精度准入未通过 |
| G5 资源 | 长度、dtype、静态 suffix map、峰值门和有限调用预算已有定义。真实 CPU BF16 执行 wrapper/KV/copy 图、最终 fixture manifest、host/commit/pagefile/disk/wall 上限仍缺；不能用 metadata 当 runtime PASS。 | 阻断 |
| G6 总预算 | canonical/replay/generation/fit/token 的主要代数可复算。NLI C*_d、s_type、完整 witness 选择、cold-load次数/CPU IO成本、时间和存储硬额度未定，当前没有数值总上界。 | 阻断 |
| G7 验收/Gold | durable intent/completion、失败保留、动作先封存后 Gold、独立验证、不 resume 原则明确。真实 kernel 的误差证明、likelihood/NLI/replay容差、完整源码依赖图和可独立重建 witness 仍缺。 | 阻断 |
| G8 成本效益 | 使用已有公开 SD，未假造 Mistral 均值、方差或功效；但 δ_EM、δ_Damage、H* 和可承担资源均 UNRESOLVED，无法评价是否值得进行一次预检，更无法评价完整研究成本。 | 决定性阻断 |

G0/G3/G4 中“结构合理”仅是该条文的审查结论，不是任何运行准入。不存在部分通过累积成 GO 的规则。

## 3. 参数、权重与显存独立复算

固定 reader：`mistralai/Mistral-7B-Instruct-v0.3@c170c708c41dac9275d15a8fff4eca08d52bab71`。

从已存 config 的 H=4096、I=14336、32 layers、32 attention heads、8 KV heads、head_dim=128、V=32768、untied embeddings 推导，不构造模型：

- 每层 attention 参数：`2H²+2H(8×128)=41,943,040`。
- 每层 MLP 参数：`3HI=176,160,768`；两 RMSNorm 参数 `2H=8,192`。
- 每层总参数 `218,112,000`，BF16 bytes=`436,224,000`。
- 非 layer 参数：`2VH+H=268,439,552`。
- 总参数：`32×218,112,000+268,439,552=7,248,023,552`。
- BF16 weights：`2×7,248,023,552=14,496,047,104 bytes=13.5004959106 GiB`，与 index total_size 一致。它是 tensor payload 字节，不是全部 shard 文件/资产/运行内存大小。
- 保守 KV：`2×32×8×128×2×8256=1,082,130,432 bytes`。
- BGE 静态项按既有清单计数：`109,482,240×2+512×8=218,968,576 bytes`。本次只复算该清单的算术，没有重新读取 BGE 权重 headers。

用 M=`17,102,864,384`：

| 静态项 | bytes | 占 M |
|---|---:|---:|
| reader+BGE+全32层保守KV | 15,797,146,112 | 92.36549947% |
| 卸载末两层 | 14,924,698,112 | 87.26431887% |
| 卸载末三层 | 14,488,474,112 | 84.71372857% |

因此静态规则的最小 suffix 为 n*=3、layers29–31；85% 静态门的整数 bytes 上限为14,537,434,726。90% allocated 和95% reserved/device-used门分别为15,392,577,945和16,247,721,164整数bytes上限。草案约84.71%与92.37%算术正确。

这些不是峰值证明。CPU 层实际 KV 放置尚未绑定；保留全32层GPU KV项作为保守预算可以，但不能称其为真实分布。一次8192×32768的BF16 full-sequence logits就有536,870,912 bytes；8191个target位置的FP32 logits有1,073,610,752 bytes，尚有临时advanced-index副本、激活和kernel工作区。必须测试原生scorer，而不只是生成KV。两类峰值阶段可能互斥，不能简单把所有项当同时峰值相加，也不能忽略它们。

真实 layer execution 不可由 storage map 推断。草案已发现 `.to(cuda)` 原constructor和动态offload hooks问题，但尚未给出替代的 exact设计。因此它目前没有可验收的设备/迁移契约。

## 4. 调用、fit、token 与有限预检预算复算

N_D=13,500、N_T=18,000、N=31,500；r_D=r_T=180，R=360，A=31,860。三 retriever siblings 分组，`round(.05×18000)=900`。五个 heads 的宽度为25/23/7/5/5，五base+五cal=10 fits；账本当前185，未来全获准成功也只增到195，不是205，本次新增0。

| 项目 | 独立结果 |
|---|---:|
| canonical generations | 94,500 |
| replay generations | 1,080 |
| canonical+replay逻辑generations | 95,580 |
| 每trace保守reader generation forwards | (48+1)+(64+1)+(48+1)=163 |
| 正式generation forward上界 | 5,193,180 |
| repair retrieval | 31,860 |
| repair-query BGE，两个需embedding的retriever | 21,240，前提是两份replay的retriever计数确实平衡 |
| answer BGE texts | 63,720 |
| 正式TF cells | ≤127,440 |
| 正式NLI branches | ≤63,720，绝不是NLI forward上界 |
| test policy-action单元 | 9×18,000=162,000 |
| acquisition durable events | 8A=254,880 |
| fit intent/completion | 20 |

U1没有完成development replay身份与分层绑定，因此`BM25/dense/hybrid各10,620`及`2A/3`仍是基于平衡前提的预算，不是本次已认证身份事实。不得用算术结果替代清单验证。

预检：3 lengths×3 generation roles×4 repetitions=36 generations，输出cap=3×4×160=1,920，保守generation forwards=3×4×163=1,956。TF=3×2×4+3=27；BGE=2×2×4+3=19 forwards，texts≤136+48=184；NLI=19 forwards，pairs≤72+24=96；direct cached stress=1 prefill+64 decode=65。额外3TF+3BGE+3NLI=9，未漏入模型分类账。reader全部保守forward上界为：

`163A+1956+27+65+4A=5,322,668`。

BGE全部forward保守上界为`2A/3+2A+19=84,979`，texts上界为85,144；NLI为`F_NLI+19`。这些仍依赖前述replay分层与固定forward语义，不保证最终资源够用。

| token公式 | 独立上界 |
|---|---:|
| `(3A+36)×8192` generation input tokens | 783,286,272 |
| `160A+1920` generation output tokens | 5,099,520 |
| `(4A+27)×8192` teacher total input tokens | 1,044,209,664 |
| `(4A+27)×8191` teacher target tokens | 1,044,082,197 |
| direct cached新增input tokens | 8,256 |
| `512×(2A/3+2A+184)` BGE tokens | 43,593,728 |
| NLI tokens | `512×(Q_NLI+96)`，数值未闭合 |

teacher target token是teacher input的子集，不能加成总独立输入token；generation input不包括每次cached decode重复处理prefix，不能当FLOPs；BGE/NLI padding slots分别有`512×16F_BGE`和`512×8F_NLI`保守界。这些单位区分正确。

只读原GbV chunker确认每轮start至少前进一词，故`c_b≤Σ max(1,w(p))`成立，`Q_NLI≤2A max C*_d`是合法但粗糙的上界。`F_NLI=Σceil(c_b/8)`要求实际batch size固定为8且每branch独立batching；只写`batch≤8`时不能保证该等式，仍可用`F_NLI≤Q_NLI`作保守界。最终batch/config须绑定，不能在运行时选择。C*_d未提供，NLI全成本无法定量。

## 5. 存储、时间与数值公式审查

`J=8A+2(F_TF+F_BGE+F_NLI)+20+J_P+J_CPU`按逻辑调用durable定义是合理模板；inner autoregressive forward应单列witness，不能偷算作已fsync事件。J_P/J_CPU和各类s_type仍未冻结，故不是有限数值文件上界。

`B_total_upper=2(B_assets+B_inputs+B_science+B_preflight+B_failure_reserved)+B_working_temp`正确表达一份active加一份verified archive的保守账本结构；但它只是带未知项的模板。development targets/outcomes、独立validator输出、preflight sidecars、模板/词表/环境副本和可能重复缓存都需要实际schema逐项归属，不能因为存在generic manifest项就认为已计入。

最明显的未决科学验收分支是保存完整target词表logits，还是只保存target-logit/logsumexp摘要。二者的独立softmax可验证程度与存储成本不同，不能留给工程选择。若采用草案最坏target数并保存每target全部FP32词表logits，仅此项为：

`(4A+27)×8191×32768×4=136,849,941,725,184 bytes≈124.4643 TiB`。

两份保存约248.9286 TiB，尚未含其他数据。这是对草案极保守硬界的敏感性算术，不是预测实际输出会如此大，也不是声称必须保存如此多。它证明“全logits或摘要”尚未选择时不能判断存储可承受，更不能隐式缩小witness。

T_plan公式量纲成立，前提是n_load、各模型forward counts、cache/copy/CPU/IO/验证边界互不漏计且单位一致。`u_time`、`T_job_max`、host/commit/pagefile与disk reserve未定；`rate×time`费用式只能作为计价模板，不能签实际成本PASS。有限预检真实吞吐可以是未来才有的证据，预检可承受额度与停止watchdog却必须事前明确。草案G5.2规定NLI独立进程，G5.3又使用“同一唯一预检进程”措辞，最终controller/worker/load DAG必须消除歧义并给出精确cold-load预算。

BGE norm推导在非clamp、normal range、0≤η<1且逐分量相对舍入界成立时正确：

`(1−u)/(1+η)≤||y||₂≤(1+u)/(1−η)`，BF16 `u=2^-8=0.00390625`。

`γ_k=ku32/(1−ku32)`需`ku32<1`及真实FP32规约误差模型。源码仅显示native F.normalize，不证明accumulator/规约树/sqrt/output rounding；η、k、ε dtype、subnormal/clamp界均未认证，不能实例化数值容差。本文没有从Phi最大偏差反推门限。likelihood独立FP64 softmax/reduction同样缺finite-logit范围、kernel契约、witness选择和误差传播；既有CPUhead `1e-10`只能作为已冻结上限，不能代替新输入域的适用性证明。U6尚不能支持一次正式预检验收。

## 6. 统计与精度独立复算

EM、Recovery、Damage、Net公式正确，`EM_p−EM_Keep=Recovery_p−Damage_p`逐行恒等。两policy的Damage差使用N_all分母，未误换为switch denominator。bootstrap每dataset保持2,000 groups，三siblings共同multiplicity，因此每draw N=18,000、K=900。重复row weighted-copy选取必须使用冻结score/tie顺序，与显式复制一致；20,000不是样本量，也不覆盖model-training uncertainty。

四端点Bonferroni双侧尾概率`0.05/(2×4)=0.00625`，对应98.75%每端点区间及近似95% simultaneous family。分位点应按quantile API传0.00625/0.99375，或percentile API传0.625/99.375，工程不得混用单位。严格EM lower>0且Damage upper<0规则正确。

本次只用Python标准库读取已公开聚合JSON、math和statistics.NormalDist作代数；没有bootstrap、fit、score、tokenizer或模型运行。独立取得：

`z=Φ^-1(0.99375)=2.4977054744123737`；`sqrt(4500/6000)=0.8660254037844386`。

| 比较/端点 | 5次已公开SD中的max(pp) | 精确z的u=1半宽(pp) | 精确z的u=1.5半宽(pp) |
|---|---:|---:|---:|
| C1 EM | 0.10458756345156081 | 0.2262308894 | 0.3393463341 |
| C1 Damage | 0.039336803597886605 | 0.0850885112 | 0.1276327668 |
| C2 EM | 0.08659008070238117 | 0.1873009593 | 0.2809514390 |
| C2 Damage | 0.03711401760325547 | 0.0802804553 | 0.1204206829 |

草案表采用z=2.498，能够复算其0.226258/0.339386等显示值；这是明示近似带来的微小数差，不是决定性错误。显示六位时应说明使用近似z，不能暗称exact inverse-normal结果。

最坏u=1.5半宽约0.33935/0.12763/0.28095/0.12042 pp仍不能比较任何H*或δ，因为四个价值阈值未给定。不能从已有均值、这些半宽或期望显著性倒推阈值。OOF→新reader固定panel的平方根缩放和u=1.5均是敏感性假设，不提供Mistral功效下界。单trace事件`100/18000=0.0055555556 pp`，单question最多三个相关事件；零Damage/退化bootstrap不能排除未观察稀有伤害。

## 7. 结果驱动、Phi前驱与claim边界

新草案主动披露Qwen已见结果、Phi工程失败与新分支时间线，这优于把它称为全项目前注册。没有发现草案允许读取Phi科学输出选模型、筛题、调head或调阈值；不能仅因形成于Phi失败之后就断言不当数据窥视。选择固定且保留无论效果如何报告的原则。

但研究问题和资源重新治理受历史结果影响，确实存在设计适应性。该事实已披露，不能被metadata pin或新的Mistral命名空间消除。G1允许的“Phi命名身份文件”须独立关联到accepted Qwen/历史身份，不可把Phi的token/input/replay PASS一并带入执行图。U1未闭合意味着这仍是文档意图，不是已验证依赖图。

目前仍有未绑定且可能影响科学或可复现性的分支：fast/slow tokenizer、EOS/pad/attention；CPU执行hooks/KV/copy和kernel；eligibility/unscorable/missing truth table；NLI实际batch；完整logits或摘要及其可验证claim；finite fixtures与数值容差。多数已被草案诚实标为UNRESOLVED，标记缺口不能替代关闭。

未来即使完整研究获准且成功，只有同题、指定Qwen和Mistral条件下的信号增量证据；不能恢复Phi科学有效性、ROA-FULL、新算法、全系统零样本迁移、训练数据独立或population replication。C2双reader通过也不证明GbV相对HGB有增量；C1只有Mistral通过不推翻Qwen未通过。不同显著性不是interaction。

## 8. 决定性缺口和终态

本次STOP按重要性由以下任一项独立支持：

1. **U7/G8**：没有经研究用途论证的δ与最大半宽，无法证明完整成本将换来可解释、值得发表的新增知识。
2. **U5/G5/G6/G8**：预检和正式job的wall-clock、host RAM/commit/pagefile、disk reserve、输出额度未固定，无法定义可承担范围或硬停止。
3. **U3/G5/G7**：真实CPU执行、原生scorer兼容、fixture coverage、copy/load/cold-state与关键tokenizer/schema分支仍未绑定，连一次预检的确定性对象都不完整。
4. **U6/G7**：归一化和神经评分数值验收尚无可执行的误差模型；已知Phi失败后不能再把容差推迟到真实ledger出现后。
5. **U4/G6/G7**：witness设计与预检存储未定；完整softmax验证和摘要验证是不同证据强度，不能放行后再选择。

U1 benchmark input graph与U2最终权重字节有其后续阶段门，单纯“尚无实际吞吐/权重”本身不作为本次唯一拒绝理由；本次拒绝针对必须先于预检解决的文档与价值契约。不能把本次STOP改写成“补充后自动GO”。依治理当前CAS Q2实验扩展应停在工程之前，保存Qwen已有效研究、Phi全部失败与本次草案/审查；不自动进入新reader、新协议运行或方法搜索。

## 9. 输入哈希与操作声明

| 输入 | SHA-256 |
|---|---|
| 外部本次研究协议草案 | `787b6a3992988d31dccbc2a4c75561c51f498e1e555797cb5721096d336d70cf` |
| POST_PHI_FAILURE_RESEARCH_GOVERNANCE.md | `ecaf663edd3e5ffdb7a15569bf6c2932a0168865a90305377ee418ed5fcd9fb4` |
| THIRD_READER_SELECTION_DECISION.md | `ff9346902d957a2c49d46f5b1f52409f397b40dfd85138275d1bfd457e391802` |
| PHI_READER_DEVELOPMENT_RUNTIME_V4_FAILURE_ACCEPTANCE.md | `ebf7a49010e0752fa3a52bba3099fe5429bab6cd47e4faf779c86e1fd29a26b3` |
| EMPIRICAL_REPLICATION_PROTOCOL_V1.md | `86e882fb9edafaaf301b3a2494ef39485d43d98aac3fc4e8be97f9ba7e54691c` |
| PHI_READER_REPLICATION_PROTOCOL_V1.md | `a89c44f7935c1df838954d47085b7bc7df950db3d6bb2549ac664a58465fef16` |
| COST_AND_PRECISION_RESULTS.json | `e16faff35811f95d10ea9b1bbfb3be715cba5ca46ec84ec1827e79c39835eb09` |
| EVIDENCE_INDEX.json | `19cbe3e9a17d09a18e39cff39de1a2322741503d0fb012470580ec16572e45f2` |

本次只有read-only文档/源码/metadata/公开aggregate读取、标准算术及创建本外部Markdown报告。repo修改=0，草案修改=0，下载=0，模型/tokenizer运行=0，neural forwards=0，scientific fits=0，科学score/bootstrap=0，Gold/reference读取=0，ID选择=0。审计过程中出现的查找路径不存在错误只影响只读检索，不构成任何实验attempt或新增科学namespace。

**唯一裁决：STOP_MISTRAL_EXTENSION_BEFORE_ENGINEERING**
**CAS Q2 STATUS: NOT READY**
