# P0-I independent manuscript audit — Astra xhigh

Signed date: 2026-09-13 (Asia/Shanghai). Auditor: GPT-6 Astra, xhigh, independent P0-I reviewer.

**DECISION: PASS_SOURCE_LEVEL_WITH_BLOCKERS**

**CAS Q3 STATUS: NOT READY.** 本裁决接受修订后稿件的源文件级科学陈述与现有有限证据相容；不签发最终 Submission Ready，不等于期刊接收预测，也不关闭尚未完成的编译、作者、许可、公开材料和 CAS 期刊资格门。

## 1. 审计对象、独立性与执行边界

审计工作树为 `E:\paper\ReliableRAG-cas-q2-p0-1`，分支 `work/cas-q2-p0-1`，起点 HEAD `d5ea8b2d695343e958fdc800554758f4d7c501cc`。稿件及构建脚本为此次授权形成的未提交文件；本签署绑定下列最终内容哈希，不把 HEAD 本身当作已经包含稿件的承诺。原工作区 `E:\paper\ReliableRAG` 未修改。

已完整阅读 AGENTS.md、Q3 PROJECT_CHARTER、CURRENT_TASK、EVIDENCE_INDEX、P0-A/B/C/D/E/F、P0-I PREFLIGHT/AUTHORIZATION；阅读 main/supplement、全部 BibTeX、六张生成表、两幅 PDF、ASSET_RECEIPT、MANUSCRIPT_VERIFICATION、两份构建/验证脚本及稿件模板、BUILD_STATUS。数值追踪到已经接受的 POINT_ESTIMATES、INTERVALS 及相应统计/成本/来源验收文件。补充阅读公开的独立指标实现源码以准确说明规范化规则；未执行指标计算。

本轮只做文献核查、文稿修正、封存 aggregate 到表图的格式构建、只读报告核对与 PDF 渲染。未读 Gold/reference/answer payload、逐题结局或 bootstrap draws，未调用模型/tokenizer、未拟合、未重跑 bootstrap、未改封存输出或补造历史证据。对既有科学执行真实性的接受范围承继相应验收；本轮不是再次独立重做全科学实验。

CURRENT_TASK、EVIDENCE_INDEX、BUILD_STATUS 属于并发更新的治理文档，按阅读时快照解释。主代理在审计开始时加强静态 verifier 并调整 revision 排版；发现并发写入后已协调暂停 paper/scripts 写入，再基于最终文件校验。本轮审计独立于主代理的静态检查，不将该 verifier 称作本审计员另写的独立科学实现。

## 2. 第一层：数值真实性与证据追踪

**通过当前报告范围。** 两份输入 aggregate 保持原封存 SHA-256：

| 输入 | SHA-256 |
|---|---|
| POINT_ESTIMATES.json | `b03ddad8fa35f582a63403c029942104c3f5da1a961110edc2a62f09871f4d3b` |
| INTERVALS.json | `6d454afeec7c125c0cc4d182556af6db214a867aa4f62f7a6fbd1e6e22b09331` |

18,000 traces / 6,000 question groups、三个 retriever siblings、4,267 eligible、八个 switching policies 各 900 actions、Keep 零 actions 均与封存报告相符。九行 overall 和 54 行 dataset/retriever 结果与 aggregate 对应。另用只读、未导入 builder 的解析核对六行 ordered comparisons 的 36 个点估计/区间标量及行标签/联合结论，并核对九个 policy 的事件分割、Net、最终正确数、900/0 动作和 rate 公式，全部通过。

主要数值应保持如下完整顺序；单位均为 percentage points：

| Ordered comparison | ΔEM [adjusted range] | ΔDamage [adjusted range] | 联合规则 |
|---|---|---|---|
| ROA-FULL − HGB_GBV_R | +0.0444 [−0.1333, +0.2037] | +0.0611 [0.0000, +0.1278] | 未通过 |
| HGB_GBV_R − HGB_ONLY_R | +0.0556 [−0.1556, +0.3167] | −0.0833 [−0.1833, −0.0056] | 未通过 |
| HGB_GBV_R − GBV_ONLY_R | +0.2333 [+0.0722, +0.4333] | −0.0722 [−0.1444, −0.0278] | 通过 |

HGB_GBV_R 的 352 Recovery、11 Damage、341 Net、19.8833% EM、25.2780% F1 可追踪。唯一通过的比较对应 42 个更多最终正确答案、13 个更少 Damage 事件，不能改写成 42 个更多 Recovery。Keep EM 17.9889%；融合策略具有八个等动作 switching policies 中最低的观测 Damage，但 Keep 的零 Damage 必须同时保留。

EM/F1/Damage rate 是百分比，差及区间是百分点；overall denominator 为 18,000，secondary dataset/retriever cell denominator 为 6,000，均不是 900 或 4,267。Neutral 可以改变 F1，不是所有指标都不变。六张表、图中轴单位与正文现已一致。

成本披露与 P0-F 对齐：54,000 canonical generation receipts、51,901,556 prompt tokens、826,362 output tokens；2,250 answer-embedding forwards、16,932 likelihood forwards、136 cache hits；8,534 NLI forwards / 42,946 pairs。C2/C3 的 retrieval components 与 embedding 计数没有被混成生成调用。540 generation receipts 的 bounded replay 单列。五个 stage timers 不相加，两个 C4 allocator peaks 不相加。没有把未测量的独立部署、统一端到端时间、canonical C2/C3 peaks、BGE tokens、逐解码输入 token touches、FLOPs、能耗写成零或由现有计数推导。

证据充分性限于认证的执行图和已接受的 aggregate 计算。原始七个 estimator 的 fit-time ID/matrix receipts、独立原始 fit witness、独立恢复的更早完整 training-manifest pin 仍缺失。字节固定与 saved-parameter replay 不证明每次原始训练事件；这项历史缺口不可由本次静态 PASS 消除。

## 3. 第二层：公平性与统计陈述

**通过受限的五个 current-head 对照解释。** 五个 head 使用相同 4,500 development questions、3,600 fit / 900 calibration、相同 paired candidates、eligibility、preprocessing、模型族及 action count。fusion 的两个 numeric inputs 实际还带 missingness/retriever indicators，共七列；不得说仅有两个总设计矩阵列。HGB 是固定上游信号，顶层融合是普通校准 logistic regression。

这不是所有上游 signal 的总历史 label budget 匹配。七个历史 estimator 的重建 membership 是 601 traces / 518 groups，来自 7,200 traces / 4,800 groups 的 universe；这些历史 groups 与此前 3,000 V2 questions 纳入排除。raw HGB、raw GbV、V2 保留为 contextual controls，不承担 matched incremental attribution。稿件和补充材料已明确该限制。

Recovery 监督目标是 0→1，不直接优化 Net、也没有训练期 Damage constraint。GbV 是 branch-own evidence 的 `F1(a1,E1) − F0(a0,E0)` project adaptation；并非已发表的 paired-policy 公式，也没有声称复现作者原代码或测量 faithfulness outcome。具体 verifier/revision、FP32、512 tokens、20-word overlap 和 entailment index 已披露。

20,000 dataset-stratified question-cluster bootstrap、seed 20260926、linear quantile、三比较×两端点、0.05/12 与 1−0.05/12 的双侧 Bonferroni percentile 范围陈述正确。primary 在每次 draw 重分配全局 top-K；fixed-action sensitivity 复用 draw 且保留原动作 membership，每次 draw 的动作副本不必正好 900。零端点算 inconclusive。F1、所有八个 vs Keep、dataset/retriever breakdown 均不升级为主检验。

不得将这些条件 bootstrap 范围说成对 fit/calibration/candidate generation/corpus construction 不确定性的覆盖，或精确有限样本保证。确定性 hash cohort 也不是 probability sample。三个 retriever siblings 受同题聚类保护，但固定 benchmark pool 与拟合模型的更广不确定性没有因此被估计。

融合对 HGB-only 的 Damage 单端点在 primary 中为负、EM 跨零；fixed-action 中 Damage 上端点触零。两者均不能支持联合改进，更不能反推无效、等价、非劣或 GbV 无用。两个增量比较一过一不过，不是二者增量差异显著的检验，不是因果交互证据。

## 4. 第三层：Claim 与文献定位

**现有证据足以支撑修订稿当前窄 Claim，不能支撑独立算法贡献。** 可用标题是现有的 “Supervision-Matched Selection of Paired RAG Repairs: An Empirical Study of Accuracy and Damage”。核心是固定 reader/candidates/current supervision/action count 下的比较及其负面边界，不能改成通用安全 RAG、新型 arbitration architecture 或最先进算法标题。

直接邻近工作的实质重合得到承认：Dado v3 已含 two-answer NLI difference、Bert-Gen-2A 及 selective evaluation；TrustMargin 已进行生成后两答案 arbitration；Generate but Verify 已建立 faithfulness verification；adaptive/corrective、budgeted repair、counterfactual routing 和 paired evidence intervention 都有前例。因此 original-RAG vs repaired-RAG 的场景变化及普通 logistic 融合不是已经清除的新颖机制。未与完整外部系统数值对比，就不声称优于它们。

本轮核对的一手页面及具体作用包括：[Generate but Verify](https://aclanthology.org/2025.ijcnlp-long.56/)、[Dado v3](https://arxiv.org/abs/2604.07985v3)、[TrustMargin](https://arxiv.org/abs/2606.08397)、[D2R](https://arxiv.org/abs/2606.29377)、[search routing](https://arxiv.org/abs/2607.05752)、[Pair-ID](https://arxiv.org/abs/2608.08944)。新增 [Doctor-RAG v2](https://arxiv.org/abs/2604.00865v2) 以覆盖失败轨迹定位/修复和有效前缀复用；用 [C-Pack v5](https://arxiv.org/abs/2309.07597v5) 官方版本纠正 BGE 引用标题、六名作者和年份。新近 preprint 按所引用版本说明，不冒称均为已经同行评议。此前 P0-A 通过范围与本轮具体修订共同支撑相关工作定位；本轮没有以检索数量证明穷尽全领域。

允许的主句必须同时带有以下限制：单一 Qwen2.5-3B-Instruct、固定三数据集/三检索条件、同一 6,000-question cohort、预先存在的 answer pairs、五 head 的 matched supervision、全局 900/18,000 动作、唯一通过的是 fusion vs GbV-only。HGB-only 与 ROA 的非通过结果在 abstract、results、discussion、conclusion 均保留。

禁止声称：新架构/新算法、reader-general 或 3B 以外模型大小效果、跨 reader 确认、通用域/完整 Wikipedia/生产可迁移性；faithfulness 提升、形式化 safety guarantee；5% compute/retrieval/generation 或 latency 节省；所有 policy 对 Keep 获得 confirmatory 改进；superiority over HGB-only；由一过一不过推断显著增量差异；完全语义去污染、完备历史训练真实性、公开端到端可复现。

Phi 的最终真实性/语义门失败保持终局，仅作排除披露；不是 reader effect 的负结果或第二 reader。Mistral 在 engineering/model execution 前停止，不提供任何 robustness 证据。两者与独立新算法均不是当前 Qwen-only 经验路线的自动硬前提；也不因本次稿件 PASS 获准恢复。

## 5. 第四层：模拟 CAS Q3 审稿人审查

### Major concerns：已适当披露但仍可能导致拒稿

1. **知识增量有限。** 主要联合阳性是 HGB 相对 GbV-only 的增量，而融合未超越 HGB-only 的联合门。方法简单是事实。经验贡献能否满足具体期刊取决于该刊对严谨 negative-boundary studies 的接受程度，不能用“Q3”替代编辑判断。
2. **单 reader 与低基线正确率。** 一个名义 3B reader、特定 repair operator 和 context pools 提供较窄证据；Keep 17.9889% EM 不支持推广到强 reader 或常规大型开放域系统。现稿限制已经明确，但不能承诺审稿人不会要求扩展。
3. **历史来源不完整。** 七个 upstream estimator 的原始 fit 证据缺口真实存在。当前 matched-head 结果可以作为固定信号条件比较报告；完整训练溯源不成立。若期刊要求每个上游 estimator 的原始事件级可复现，该材料无法满足，不得制作事后 receipt 冒充原始证据。
4. **外部 baseline 范围。** 原版 GbV 被适配，未运行完整 Dado/TrustMargin/Doctor-RAG 等系统。当前协议支持内部固定信息条件的 attribution，不支持外部 SOTA 或算法优越性。如果期刊将完整外部实验比较作为必要门，应转适配刊或停止该投稿，而不是由本审计偷偷授权新实验。
5. **资源结论不足以指导部署。** canonical workload 可复核，policy standalone、end-to-end latency、whole-system peak 和效能节省不存在。保留 workload 描述有价值，但不能成为效率贡献。
6. **推断是条件性的。** 稀疏 Damage 事件、固定 head、固定 cohort/pool、单 operator、pretraining/semantic contamination 未排除，限制外推；改写 CI 名称不能补足这些不确定性。

作为模拟审稿结论：这是一篇可以被评审的窄经验研究，其优点是完整 matched control panel、同题聚类推断、显式 harm accounting 和不隐藏负结果；不构成接收建议。当前实际提交仍应 hold，因为下一节的文件/合规/资格门未关闭。即使关闭，acceptance 仍由真实编辑和审稿决定。

### Minor concerns 与投稿排版待查

表名/内部 policy 缩写多，journal conversion 时可增加简短术语索引，不能改变对照含义。较宽 overall table 与长 revision/引用在真实 TeX 排版下可能拥挤，必须在编译 PDF 中检查。现有 PDF figure 使用基本 Helvetica 字体；本轮不签 target-journal font embedding/PDF profile 合规。当前匿名写作与单独 author template 分离适当，最终需按期刊匿名制度调整。

## 6. 本轮直接修复及验证结果

已修复如下明确错误或歧义，未改科学结局：

1. Qwen revision 原有多余尾字符；更正为精确 40 位 `aa8e72537993ba99e69dfaafa59ed015b17504d1`，补齐 BGE exact revision。
2. 表注/坐标混淆 percent 与 percentage point；更正 overall/secondary units 和 denominator。
3. Keep 比较原措辞留下进入 primary family 的例外；现在八个比较全部明确 descriptive。
4. Pipeline 图原有 a0 流向 repair query 的错误依赖；改成 question/E0 分支，明确 a0 不进入 query，Keep 零动作。
5. Recovery–Damage 图的近邻标签引线与重叠；重绘并检查两个 PDF。
6. GbV formula 的 branch-own evidence、局部 adaptation、非作者 paired formula、具体模型/运行选择补明。
7. Recovery loss 非 Net 优化或 Damage constraint、Platt calibration 使用 disjoint logits、历史与 current supervision 区别补明。
8. bootstrap seed/quantile/sensitivity、条件范围和固定动作副本含义补明。
9. 确定性 cohort、public source frame、历史 membership/manifest pin 缺口、未知活动/语义污染边界补明。
10. Neutral 与 F1、metric normalization、多 reference/special-answer 约定补明。
11. workload/replay/cache-hit 计数和未测量成本项补齐。
12. Dado v3 最近邻描述加精确机制/section，加入 Doctor-RAG，修正 C-Pack BibTeX 元数据；现在 22 条引用，均被使用。

修改文件：`paper/manuscript.tex`、`paper/supplement.tex`、`paper/references.bib`、`scripts/build_cas_q3_manuscript_assets.py`，以及重新生成的表图、ASSET_RECEIPT、MANUSCRIPT_VERIFICATION；另新增本审计报告。主代理加强的 verifier 被使用但不是本审计员改写。未修改封存结果、实验脚本、权重或原工作区。

执行并通过：

```powershell
python scripts\build_cas_q3_manuscript_assets.py
python scripts\verify_cas_q3_manuscript.py
pdftoppm -r 144 -singlefile -png paper/figures/paired_pipeline.pdf tmp/pdfs/astra_after_pipeline
pdftoppm -r 144 -singlefile -png paper/figures/recovery_damage.pdf tmp/pdfs/astra_after_recovery
```

Builder: `PASS_AGGREGATE_ONLY_MANUSCRIPT_ASSET_BUILD`，model forwards = 0，fits = 0，Gold/answer reads = false。Verifier: 126 checks，abstract 204 words，22 bibliography entries。额外只读核对：六 comparison rows / 36 scalars / 九 event partitions 通过；不是重算置信区间。126 项静态检查既不证明 TeX 编译，也不独自证明文字逻辑、文献机制或原始历史训练；本报告分别进行了人工审查。

两个 PDF 均已在 144 dpi 渲染后实际查看，流程依赖、坐标单位、标签可读性通过。Poppler 返回 exit 0，但输出过 Symbol/ArialUnicode display-font warnings；未观察到所用 ASCII/Helvetica 图中文字缺失，不把它表述成零 warning 的最终 journal PDF 验收。最后一次仅 supplement 指标段落修改后再次 build/verify，两个图的字节哈希完全未变，因此已有最终图视觉检查仍有效。

环境 inventory 未发现 `latexmk`、`pdflatex`、`xelatex`、`lualatex` 或 `tectonic`。**没有编译 main/supplement，没有正文 PDF 版面验收，不得签最终 Submission Ready。**

## 7. 剩余阻断项与唯一允许下一步

P0-I 的 source-level 审阅可记为通过；P0-I 的 compiled-artifact/最终投稿验收仍开放。唯一允许下一阶段是在现有 Qwen-only 证据和 Claim 不变的前提下，完成投稿材料收口：

| 必须门 | 闭合证据 |
|---|---|
| 真实 TeX build 与视觉验收 | 在具有 TeX 的环境编译 main/supplement，保留引擎/包版本和完整日志；修正真实 error、缺失 reference/citation、溢出、表图字号、分页及目标 PDF/font 约束，再查看完整 PDF。 |
| Owner/author inputs | 真实作者、机构、贡献、funding、COI、ethics/acknowledgements、所需 writing-assistance disclosure 和最终声明由负责人提供；不得代填不存在事实。 |
| Project license / public package | 权利人选择许可；核对第三方材料和期刊 data/code policy，完成被允许的 release 或审稿访问安排；当前匿名 aggregate candidate 不是已公开端到端实验包。 |
| 目标期刊与 CAS Q3 资格 | 确定 title/ISSN、采用年度、大类/小类与机构认可规则的一手证明及实际 scope/format；不得以 JCR quartile 或搜索摘要替代 CAS。 |
| 最终交接一致性 | 将本轮最终文件哈希、22 条 bibliography、source-level audit 状态同步 EVIDENCE_INDEX/CURRENT_TASK/BUILD_STATUS；再次检查稿件、补充、表图、cover letter 和 release 声明一致。 |

上述步骤不授权新 Gold、fit/model/score、追加 comparison、独立算法搜索、Phi V5、Mistral或 reader 扩展。若最终期刊要求当前证据无法满足的实验/历史溯源，应作显式新的科研治理决策或更换符合既有证据的期刊；不能删除负结果、放宽 Phi 门或改写 provenance 达到提交。

停止条件：发现 aggregate/原接受证据实质矛盾或审计无法追踪；必须依赖不存在的历史 fit 证明、虚假的外推或算法新颖性才能成立；负责人不能提供真实声明/合法发布安排；没有符合制度的 Q3 且 scope 接受该经验研究的投稿目标。遇到这些情形不得签 Submission Ready。拒稿风险仍在，不因 Q3 转向降低真实性、公平性或复现标准。

## 8. 最终签署文件哈希

| 文件 | SHA-256 |
|---|---|
| paper/manuscript.tex | `e1e74ea00877eee6f96f2f73c9ee50a1bbff37bc8172676be902045f0acd384f` |
| paper/supplement.tex | `b11f614e311a750cc73f4a280ed0f9792ff5d1775cef25b0cfbce34571def752` |
| paper/references.bib | `caa1ba0653f050c03445e1b100efb635dd17f813239e5a47822afc276247978e` |
| paper/figures/paired_pipeline.pdf | `807bb54a83c341fec81d887571a932b04925b2a77f77badf5f46748eef3cd4a2` |
| paper/figures/recovery_damage.pdf | `915395bc073f9ba7292d9f64154bda58838308d6479e5fc5a1985adaf51ce0b7` |
| paper/ASSET_RECEIPT.json | `0d3590ffcd25a92a81c2ae638f87a3ded3141574bca80377b179d9f57df5d228` |
| paper/MANUSCRIPT_VERIFICATION.json | `ac18509708498911f19f099d1816f22e9da4d365d6a12ac2b9dc913a3dba75cb` |
| scripts/build_cas_q3_manuscript_assets.py | `7c3689812a026ff511d7c45542a7bf62a661e277b6aa235f2fe417573e0dab63` |
| scripts/verify_cas_q3_manuscript.py | `e70bbd29581cbdb7d648be6b55f5292357744db872450c699b482a9eeec0bf71` |

六张表的精确哈希在上述 ASSET_RECEIPT 中受绑定。本报告自己的 SHA-256 在交接消息提供，避免自引用。签署结论只绑定这里的稿件状态；此后影响方法、数值、Claim 或排版的变更应进行相应复核。

Signed: GPT-6 Astra / xhigh, independent P0-I manuscript reviewer. **CAS Q3 NOT READY; source-level scientific statements accepted within the disclosed limits.**
