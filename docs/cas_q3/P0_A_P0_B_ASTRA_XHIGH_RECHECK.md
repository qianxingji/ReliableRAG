# CAS Q3 P0-A / P0-B 修订后独立复核

日期：2026-09-13（Asia/Shanghai）  
审计角色：GPT-6 Astra xhigh  
唯一裁决：**PASS_CLOSE_P0_A_P0_B**  
**CAS Q3 STATUS: NOT READY**

## 1. 决定与通过范围

对本报告绑定的两份修订文件，**上轮 R1–R6 全部解决，未发现剩余的 P0-A/P0-B 阻断项；允许关闭这两道门。**

P0-A 通过的是选定直接近邻下的狭窄经验定位及方法创新否定结论。P0-B 通过的是完整结果映射、主次统计角色及允许/禁止 Claim 的边界。两者均不代表新算法获认可、通过某一本期刊的贡献门、完整公平性/统计实现重新验收或 Submission Ready。

本次维持唯一研究路线：`PROCEED_Q3_QWEN_ONLY_EVIDENCE_AND_JOURNAL_FIT_GATE_NO_NEW_EXPERIMENTS`。Qwen 可以作为有条件的经验论文科学核心；Phi、Mistral、新算法和额外实验没有因本次通过而获得执行授权。

## 2. 对象与身份核验

工作树：`E:/paper/ReliableRAG-cas-q2-p0-1`。实际 HEAD 为 `6900bc851d076a02044153105bdf800d67c88d7c`，与要求的基线一致。A/B、原审计的 repo 副本、P0-C 和状态文件均按当前磁盘读取；并发文档修改属于阅读快照，未被误称为提交完成或哈希失败。

| 文件 | 实际 SHA-256 | 核验 |
|---|---|---|
| docs/cas_q3/P0_A_DIRECT_NEIGHBOR_LITERATURE_AUDIT.md | `43a52dc64e196e483298c8b0620cda1b709fb0f42d98f9a5bcc67a053dc49c41` | 与指定修订一致 |
| docs/cas_q3/P0_B_RESULT_CLAIM_MAP.md | `dddeb099aaee4b0f95b6e20868b42182ac0ad61e5a67a320a134718c7e3f5d6b` | 与指定修订一致 |
| docs/cas_q3/P0_A_P0_B_ASTRA_XHIGH_AUDIT.md | `9fcfba7320f296348895bc2937d39ce0411582c2a99cbdb3422c4d46248e8393` | 与上轮外部 receipt 完全一致 |
| docs/cas_q3/P0_C_METHOD_FAIRNESS_ACCOUNT.md | `117e9a8fe31bd8cd7c051ebbddf58554234dbbcfc3291019c1a40366e1d31d73` | 与指定边界参考一致 |

P0-C 只作为 reader、候选、监督和执行范围的交叉参考。本次不签发 P0-C 独立终审，也不把其自身的 CLOSED 标签当作本次完成了源码/执行层重新验收。

## 3. R1–R6 逐项复核

| 上轮项目 | 修订证据与判断 | 结果 |
|---|---|---|
| R1：最近 gain-prediction 原文重叠 | P0-A 第 32 行固定 arXiv:2604.07985v3（2026-08-19）并列出 §4.3.1 成对 NLI 差分、§4.3.2 Bert-Gen-2A 双答案输入、§7 Selective RAG。剩余差异收窄到 original/repaired RAG、监督匹配、全局 900 动作、完整正确性/损伤及未通过比较；明确未证明数值优于 Bert-Gen-2A。与上轮实际读取的 [v3 原文](https://arxiv.org/html/2604.07985v3) 一致。 | 已解决 |
| R2：最低 Damage 的比较集合 | P0-B C5（第 100 行）改为八个均执行 900 动作的 switching policies，并明示 Keep 的 Damage 为零。九政策表保留 Keep=0、fusion=11，禁止 optimality / overall harmlessness / transport 外推。 | 已解决 |
| R3：增量归因方向 | P0-A 第 65–72 行明确加入 HGB 到 GbV 的联合门通过；加入 GbV 到 HGB 的联合门未过，并保留后者主 Damage 有利、EM 不确定及敏感性触零。另明确不证明 GbV 无用，也不检验 interaction、causal mechanism 或两增量差异。 | 已解决 |
| R4：reader 与语料池身份 | P0-B 开头给出 exact Qwen revision；三套 dataset-specific pools 及 19,352 / 11,746 / 23,618、总 54,716 与既有 C1 公开证据一致。C7 明示 6,000 groups 展开为 18,000 traces，不能当独立题目；A 同步使用三个池及其共享范围。 | 已解决 |
| R5：单位、事件定义与来源定位 | P0-B 区分 Damage count / Damage rate (%)、EM/F1 (%) 与差值 pp；给出 Recovery/Damage/Neutral 定义及 18,000 分母；说明 Neutral 不保证 F1 不变；统一 Recovery/Rescue；禁止从 EM/Damage 推出 faithfulness 改善。manifest 实际路径及总体、主区间、敏感性和 secondary JSON locators 均已补齐。 | 已解决 |
| R6：先修订、后独立复核关门 | A/B 开头与末尾、CURRENT_TASK、CURRENT_METHOD、EVIDENCE_INDEX 均撤回 A/B 的提前 CLOSED，改为 revised / pending recheck；index 把 A/B 列入 missing_p0，未列入 completed_p0；旧 REVISE 审计已原字节保存。此次独立 PASS 现在完成待复核条件，可据其同步关闭 A/B。 | 已解决 |

复核没有扩大上轮要求：不要求为解决概念近邻问题临时运行 Bert-Gen-2A、TrustMargin 或另一 reader，也不因稿件定位为 Q3 而放宽任何科学结论。

## 4. 数值和 Claim 无回退

本轮完整读取修订 A/B。九政策点估计、六端点主区间和同 draw 固定动作敏感性未发生科学数值改变；对应三个封存文件重新哈希与上轮一致。本轮没有重复聚合、bootstrap 或执行原分析器。

| 封存证据（相对 worktree） | SHA-256 |
|---|---|
| outputs/cas_q2/empirical_analysis_v1/POINT_ESTIMATES.json | `b03ddad8fa35f582a63403c029942104c3f5da1a961110edc2a62f09871f4d3b` |
| outputs/cas_q2/empirical_analysis_v1/INTERVALS.json | `6d454afeec7c125c0cc4d182556af6db214a867aa4f62f7a6fbd1e6e22b09331` |
| outputs/cas_q2/empirical_analysis_v1/SHA256_MANIFEST.json | `498b83e75538032de3711bd6ce190eac049631d8393c875744d83aa0318097f6` |

以下边界继续成立：

- 唯一联合主阳性为 HGB_GBV_R 相对 GBV_ONLY_R：EM +0.2333 pp、Damage −0.0722 pp，调整区间在两个有利方向均排除零。
- 相对 HGB_ONLY_R 的联合门未通过；不得改成 GbV 带来联合收益、GbV 无效或两政策等价。
- ROA-FULL 推进仍被拒绝；最高点 EM/F1 不改变结论。
- 对 Keep 的八组正点估计、dataset/retriever/cross cells、secondary 95% 区间维持其描述或次要角色。
- Damage 最低只涉及八个等动作数 switching policies；Keep 零损伤明确保留。
- HGB 是上游输入/比较器，HGB_GBV_R 是普通监督经验政策；不存在已清除的新方法。
- 区间条件于固定模型与 realized pools；无训练不确定性覆盖、精确有限样本保证、等价/非劣或风险保证。

文献审查保持上轮已披露的访问/深度限制：本轮是对已读取原文和修订陈述的复核，没有宣称重新进行无遗漏系统综述，也没有把此前 GbV PDF 访问失败改记为全文重审成功。必要的 source-fidelity 与 adaptation 边界继续由既有接受记录约束；最终提交前仍需按照文献截止规则检查新增工作。

## 5. 关门后的权限与剩余问题

**P0-A/P0-B 阻断项：无。** 可以把这两份文件和状态索引改为已通过，并绑定本次独立复核 receipt；上轮 REVISE 历史必须保留。该同步是审计状态落地，不允许改动本次已审核的科学陈述、数值和边界；若发生实质改动需重新审查。

当前文档把 P0-C 标为 CLOSED，本次只承认其是并行阶段状态，不新增 P0-C 认证。P0-D 至 P0-I 仍未因本次决定关闭：统计陈述、溯源/污染/失败披露、成本、发布复现、具体期刊及适用 CAS 规则、稿件授权和最终独立审核均有各自验收范围。

仍须披露七个原始 per-estimator fit-time ID/matrix receipts 和独立 original-fit witness 缺失、单一有效 reader 条件，以及缺失 standalone latency、统一 end-to-end latency、canonical C2/C3 peaks 和 FLOPs。共同 acquisition/scoring 成本不等于独立部署每一政策的成本，更不等于 5% compute。

Phi 维持终局 `FAIL_P0_1_PHI_DEVELOPMENT_AUTHENTICITY`；Mistral 维持 `STOP_MISTRAL_EXTENSION_BEFORE_ENGINEERING`；两者不能成为科学复制或 robustness 数据。禁止新模型/tokenizer/fit/score/Gold、另一个 seed/budget/feature 搜索、修阈值救 Phi、自动 V5，以及未获授权的论文正文。

P0-A 关闭意味着剩余经验问题已被准确限定，不能消除其较窄、无新算法、未对 HGB_ONLY_R 联合胜出的投稿风险。具体期刊、分区年度、大类/小类和机构认定未知，故本次不签期刊适配、接收概率或 Submission Ready。

## 6. 状态文件快照及操作声明

| 文件 | 阅读时 SHA-256 |
|---|---|
| docs/cas_q3/CURRENT_METHOD.md | `dc60c3998de22f087d2e580ec4fba19d76124c46466ea2784496b5b7373bb022` |
| docs/cas_q3/CURRENT_TASK.md | `76c72c3b3728ef975ae430d0eb80583ab9584554b2a45412845420660e1f29fe` |
| docs/cas_q3/EVIDENCE_INDEX.json | `ab518b290c4a8b0ebaca2c13cb63649bc0d6f05efcfa8ba1d3b95989f0502c2a` |

本轮 repo 写入 0；模型/tokenizer/forward/fit/科学 score/bootstrap 0；Gold/reference strings/逐题答案读取 0；ID 选择 0；实验或模型资产下载 0。操作仅为文档读取、现有文件哈希和本外部复核 Markdown 写入。本文件自身 SHA-256 在完成写入后另行返回。

**唯一裁决：PASS_CLOSE_P0_A_P0_B。**  
**CAS Q3 STATUS: NOT READY。**
