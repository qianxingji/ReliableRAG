# Phi 终局失败后的科研治理与方法路线决定

日期：2026-09-13（Asia/Shanghai）
决策模型：**GPT-6 Astra，xhigh**
治理决定：**DESIGN_ONLY_BOUNDED_EMPIRICAL_REASSESSMENT；NO_PHI_CONTINUATION；NO_AUTOMATIC_MISTRAL_EXECUTION；NO_NEW_METHOD_SEARCH。**
**CAS Q2 STATUS: NOT READY。**

External independent decision receipt SHA-256:
`3db67d216583c6a719ea5dffda9dc7b516d4f805b7d8ebc1951eff8b0091c95d`.

## 1. 终局决定及唯一下一阶段

当前论文继续以**固定双候选 RAG 修复的监督匹配、信号增量与 Damage 权衡**为唯一可能的投稿主轴。它是有条件的经验研究路线；当前证据尚不足以证明已具备可竞争 CAS Q2 的完整贡献。不存在已清除、可工程冻结的独立算法。

Phi V4 的 `FAIL_P0_1_PHI_DEVELOPMENT_AUTHENTICITY` 是终局，不继续 Phi，不使用 V3/V4 做拟合、评分或科学主张，不放宽 norm 阈值、不重新归一化、不自动 V5，也不重跑 semantic validator。

**唯一下一允许阶段：一次有界、结果盲、仅外部文档的“经验研究重设计与资源准入协议冻结审查”。** 本阶段只判断：既定 Mistral reader 能否在固定控制与可承担成本下回答一个尚未闭合、值得发表的经验问题。交付一份完整的研究协议草案及其 GO/STOP 审查依据，允许只读现有接受记录、源码/配置和已公开聚合统计；不下载资产、不运行 tokenizer/模型/拟合/科学评分，不选取新测试 ID，不读取任何新 Gold，不修改 repo。

本阶段不是无限方法探索，也不是 Mistral 工程阶段。这里“结果盲”专指尚未取得的 Mistral 新输出/效果；本方向已受 Qwen 已公开结论影响，不能称为在全项目结果之前注册的非适应性设计。只有完整协议通过独立重大科研审查后，才可能另行开放**一个**与 benchmark 隔离的 invented-only 资源/数值预检阶段；该未来阶段不由本文直接授权。协议若不能在第 7 节条件下成立，则停止当前 CAS Q2 实验扩展，保存已完成 Qwen 研究和失败历史为技术报告。不能从设计不通过转入另一个 reader 或新方法的搜索循环。

## 2. 权威状态、旧文件失效部分与历史保留

本次实测工作树 HEAD 与 `origin/work/cas-q2-p0-1` 均为 **`d2cb5e6def4e43053aa61701cc9663775c6f71bd`**，worktree clean。读取了要求的五份外部方法/方向报告及 repo 的 PROJECT_CHARTER、CURRENT_TASK、CURRENT_METHOD、CONFIRMATION_DESIGN、CONTROLS_PROTOCOL、P0_3_FRESH_RESULT_DECISION；另读当前 Phi failure acceptance 与 third-reader selection。没有打开逐样本科学 payload、Gold 或模型权重。

权威顺序是用户当前指令与最新提交的失败/选择决定，随后才是仍适用的冻结协议；旧章程和方案中保留的历史段落不能越过最新状态。具体处理如下：

- `NEXT_PAPER_RESEARCH_DIRECTION_ASTRA_XHIGH_2026-09-13.md` 第 4 节路径 C 的“Phi 证据链失败”条件已经触发；第 6 节从 Phi 通过进入拟合/Gold 的顺序，以及结尾“尚缺 Phi 终态”的状态描述均已失效。
- `P0_3_ASTRA_XHIGH_FINAL_METHOD_ROUTE.md` 中“完成获准 Phi 后做一次投稿裁决”的前提已经失败。**原依赖 Phi 的投稿推进链终止**，不能把 Mistral 换名塞进原链再声称停止条件从未发生。
- 本次允许的是用户重新要求治理裁决后形成的**新设计分支**，仅有文档权限。它保留原终止事实，不追加第三次 Phi 验证，也不自动接受替代实验。
- `CONFIRMATION_DESIGN.md` 明示是被 supersede 的历史草案；其旧 ID 可用数、未完成叙述和候选假设不提供新执行权限。`CONTROLS_PROTOCOL.md` 的原控制已完成，不能因为页首仍有“not yet executed”而重复运行。
- Mistral 选择固定且早于最终 Phi 失败裁决形成独立评审记录；它是 P1 条件选项，没有已获执行许可。本文不把“选择过模型”升格成资源或科学准入。

Phi 失败是验证契约失败，不是已经观察到 Phi 科学效果不佳。Forensic 正面补证继续保留，但没有科学效应可供比较；不得写“Phi 未复现 Qwen”或把它当作负效果样本。

## 3. 论文主问题与真实可发表贡献

建议问题表述：

> 在原答案和修复答案已经固定、所有政策共享候选池与全批次动作预算时，验证信号和上游风险信号各自带来多少监督匹配后的增量？增加复杂性是否改善全总体净正确性收益与 Damage；结论的 reader、检索和成本边界是什么？

建议工作标题：**Repair or Preserve? A Supervision-Matched Audit of Paired RAG Repair under Harm and Action Budgets**。

必须纠正信号方向归因：

| 比较 | 实际检验什么 | Qwen 已知结论 |
|---|---|---|
| HGB_GBV_R − GBV_ONLY_R | 在该学习配方下，在 GbV 信息之外加入 HGB 的条件增量 | EM/Damage 联合门通过 |
| HGB_GBV_R − HGB_ONLY_R | 在该学习配方下，在 HGB 信息之外加入 GbV 的条件增量 | 联合门未通过；不能称验证器已有稳定新增收益 |
| ROA-FULL − HGB_GBV_R | 更多既有特征/复杂性相对简单 fusion 的增量 | 未通过；ROA 不恢复候选资格 |

“fusion 胜 GbV-only”不能被用来证明“加入验证器优于 HGB-only”。比较仍是固定政策/监督条件下的经验归因，不等同于现实世界因果识别。

可能发表的知识增量是：**同一候选对上，信号增量具有方向性和比较器依赖；保留正确答案的 Damage 代价必须与收益一起审计；动作预算和全系统计算预算须分别核算。** 这些结论要由足够强、足够精确的控制证据支持，不以罗列概念替代结果。

旧方向文件的 C1“定义固定双候选与不对称损失”、C2“监督匹配”、C3“reader/成本边界”是研究设计结构，**不能单凭定义被计作三项已建立的创新贡献**。配对决策、风险控制、验证选择和 reader 评测已有近邻；独立贡献应来自这套约束下不可由已有结果直接回答的、可复核的经验发现。第三 reader 和更多运行日志均不构成算法创新。

HGB 保持上游输入/比较器身份；HGB_GBV_R 保持既有经验政策名称。训练目标仍按冻结配方预测 Recovery，评估同时考察 Net/Damage；不能趁重设计把学习目标改成 Net、增加 Damage head 或换损失函数后，还称为原政策复制。

## 4. 三种推进选择的明确裁决

| 选择 | 裁决 | 科学原因 |
|---|---|---|
| 继续 Phi 或解释后放行 V4 | **否决** | 唯一 corrected semantic run 已终止失败；新治理不能把事后数值容差变成原冻结通过。 |
| 直接转 Mistral 执行 | **否决** | 同题 reader 扩展有研究用途，但实验必要性、功效/精度与资源边界未闭合；当前估算不是实际资源 witness。 |
| 先发明一个独立方法 | **否决作为当前下一阶段** | 已有多个独立方向未清除，单纯以投稿压力重开搜索是结果驱动循环。没有新技术证据支持恢复 RECA 或另命名。 |
| 先做有界经验研究重设计/资源准入协议审查 | **唯一允许** | 可在零新科学输出下决定是否值得取得另一 reader 的证据，并保留无效/资源失败时停止的出口。 |

条件 reader 固定为 `mistralai/Mistral-7B-Instruct-v0.3@c170c708c41dac9275d15a8fff4eca08d52bab71`。本阶段不重新比较模型排行榜，不把 Granite 等备用项变成失败后的自动替换。Mistral 若最终获准，研究身份应写“在 Phi 获取验收终止后，另行注册的 reader 条件扩展”，不称 Phi 原实验完成或恢复。

其预期价值在于检验指定两个单信号比较在另一个固定 reader/容量条件下是否成立；不是因为更大模型更可能产生显著结果。即便它同时胜两个单信号控制，Qwen 对 HGB-only 的历史失败仍保留，不能产生“两 reader 均胜所有控制”的结论。

## 5. 独立方法候选的失败优先审计

以下沿用已完成的一手原文审计和数学检查；本轮没有启动额外文献方向搜索或科学验证。已知近邻包括 [TrustMargin](https://arxiv.org/html/2606.08397v1)、[相关 knowledge gradient](https://people.orie.cornell.edu/pfrazier/pub/Correlated_main_paper.pdf)、[Learn then Test](https://arxiv.org/html/2110.01052)、[NLProofS](https://aclanthology.org/2022.emnlp-main.7.pdf) 和 [Twin Worlds](https://arxiv.org/html/2608.28018v1)。详细原文位置在三份方法审计中保留；不因本轮没有发现新文章就声称“无碰撞”。

| 方向 | 可证伪性与非平凡性审计 | 必须面对的公平比较/反例 | 本次资格 |
|---|---|---|---|
| RECA 四格交互、跨分支正簇 | 固定答案的 `I=m(E1)−m(E0)` 可观测；但替换分解为删除作用 D 与加入作用 A，`I=D+A`，I>0 不识别新增证据作用。hybrid 依赖 BM25/dense，hash 去重不建立独立证据 | TrustMargin 忠实 paired adaptation；相同交叉张量的 endpoint-only、真正 shift-only、单来源/最强来源、agreement、简单线性/浅树；构造 `m(E0)=−2,m(C)=1,m(E1)=1` 即 I>0/A=0。旧 shift 消融在单元素簇下与 full 等价 | 不清除；不工程冻结 |
| RECA 加入作用/最弱来源重构 | C 中性上下文可隔离 A，明确了测量对象；但 LOO/加入差分与 min 聚合仍是已知计算结构 | 必须胜同信息量 endpoint/最佳单来源及固定聚合，且不能仅靠更少动作降低 Damage；虚假但一致的两个来源仍可触发错误 Repair | 可作概念诊断，不是已获准的新方法 |
| 批次探测价值 | `ν=E[max_(S∈F)Σμ_i^post]−max_(S∈F)Σμ_i` 归约为 KG；困难在可靠估计 `P(G,Z_future|s)`，当前没有新估计器/误差界 | 相同 posterior/观测/费用的忠实 KG、边界距离+更新尺度、固定/随机 probe；两步互补而单步价值为零的反例否定一般 myopic 最优性 | 不清除；保留为未解决问题 |
| 配对风险校准 | 改写有界配对损失有意义；通用 LTT/CRC 已可容纳很多政策族，不能借标题制造新保证 | 原工具的适用假设、选择后分母与批次依赖；无 Gold 的似然不自动是正确率。须有独立校准数据 | 比较框架，不是新算法 |
| 结构化证据证明 | 证明图/步骤 verifier 已有先例；结构合法没有解决抽取事实和蕴含的语义真实性 | NLProofS/充分性验证、同 token 简单验证；“稳定证明了错误前提”的反例 | 不清除 |
| 实体替换等变性差分 | Twin Worlds 核心机制已覆盖；`mean(M1−M0)` 精确等于固定线性权重 | 同完整探针矩阵的固定差分/简单监督模型；稳定抓错出生/死亡关系仍完全等变 | 不清除 |

可证伪不等于方法新颖；引入额外观测也不等于决策结构新颖。反过来，本审计不要求证明任何普通模型都无法表达候选函数，也不把“能写成一个分数”当成普遍否决理由。合理非平凡性应来自明确的新信息/估计结构、成立的性质或有限样本优势，再由同信息量、同监督、同费用控制排除简单解释。当前方向均未达到这个标准。

不存在对 RECA 的“先跑一轮再判断创新性”授权。若未来出现实质新技术成果，需另案完成概念论证与未见确认总体设计；不能用旧 Qwen 6,000 题、失败 Phi 或拟议 Mistral 作为随时可用的方法筛选池。

## 6. 泄漏、选择偏差和结果驱动风险

1. **Qwen D 的历史确认身份保留，但不会自动延续。** 对当时预先固定的政策，它是原有效 fresh study；对之后构思的 RECA/新模型，已公开的结果属于开发影响来源，不能再当未见确认。
2. **Phi V3/V4 不进入科学研究。** 工程诊断可说明失败历史，不能提取其答案、scores、coverage 或 norm 分层来调整学习配方、筛题和选择新方法。
3. **同题 Mistral 是条件扩展。** 已知问题/Gold 历史使它不能代表独立问题人口；新 reader 输出尚未取得，使固定学习配方的条件复现仍可有信息量。必须披露 Qwen 后设计历史和共享检索/上游系统，不宣传独立训练语料或完全无污染。
4. **运行时无 Gold 与开发无监督不同。** reader 匹配头可在预先固定的 development fit/cal 上训练；不允许 test 进入拟合/变换/校准。历史 4,500 题、fresh 6,000 题的角色及全部 retriever siblings 必须在新协议逐一绑定，不能混用。
5. **主比较不能被结果改变。** 同时保留 fusion−HGB-only 与 fusion−GbV-only，ROA 保留次要复杂性审计。不能因为某一 reader 的结果更好，改焦点、扩大样本、增加 seed、替换 reader 或选区间。
6. **资格/预算泄漏同样重要。** 全总体分母含空/相同/不可评分而 Keep 的行；eligibility、tie-break、失败行处理和动作 cap 均提前锁定。不能以“清洗无标签数据”为名缩小困难样本或改变比较器动作量。
7. **技术失败不作为效果筛选。** Mistral 的选择依据和 Phi 失败时间线必须保存。Mistral 若以后也在冻结门失败，不能不断换模型直到得到一个可发表正结果。

## 7. 文档阶段的冻结前置条件与唯一交付

唯一交付建议命名为 **`MISTRAL_EMPIRICAL_EXTENSION_RESEARCH_PROTOCOL_V1_DRAFT.md`**，放在外部交接目录。它必须完整回答下列项目，不能留下“执行时选择”的科学分支：

| 条件 | 必须在协议中固定/说明 |
|---|---|
| G0：贡献必要性 | 写明尚未闭合的是 GbV 相对 HGB 的增量及两个指定比较的 reader 条件边界；说明无论正/负结果会新增什么知识。若仅为了获得第二个显著结果，不通过。 |
| G1：独立分支与证据隔离 | 明示 Phi 终止和旧投稿链关闭；所有 Mistral namespace 从空白单次创建；不依赖失败 Phi 作为 accepted predecessor。新的前驱只能是明确允许复用的 Qwen/检索/历史资产及将来独立通过的 Mistral 工程门。 |
| G2：固定研究对象 | 沿用已选择的模型 revision、同一 6,000-question cohort/三检索资产、固定原/修复候选生成流程、5 个 reader 匹配头与 7 个固定上游估计器。主 test 18,000 行，`K=900`；开发 fit/cal 与 eligible/tie/缺失规则逐项绑定。不是零样本全系统迁移。 |
| G3：原生公平比较 | fusion/HGB-only/GbV-only 为主；raw HGB/raw GbV/Keep、ROA-FULL/NOGBV/V2 按既有主次角色完整报告。Always Repair 如展示，明确是更高动作数的描述性参照，不与 5% cap 政策冒充同预算。不给任何新方法额外隐形信息或拟合预算。 |
| G4：统计与可解释精度 | 两个主比较×EM/Damage 四端点，预定方向及严格联合门；20,000 个 dataset-stratified paired question-cluster draws，每次全批次 top-K 重分配，固定模型不重拟合；次要输出和多重性预定。明确区间不覆盖训练不确定性；20,000 draws 不是样本量或功效。 |
| G5：资源准入设计 | 在任何实际预检前固定 token 上限、精度、设备/offload 放置、迁移规则、联合 Mistral/BGE/必要评分阶段边界、最坏形状、留存 witness、独立重建和失败条件。静态估计只约束是否值得预检，不能填成实际通过。 |
| G6：预算与停止 | 在执行前给出全部调用/fit/token/存储的上界与成本账，包含开发、test、replay、likelihood、NLI 和审计；固定唯一 seed/reader，不因 OOM、验证失败或不显著自动重试/扩展。任何容差须由算术契约与结果盲合成规格推导，禁止从 real ledger 最大偏差反推。 |
| G7：封存与访问边界 | 模型/配置/源码/环境/输入 pin、逐调用 durable intent/completion、独立 validator、动作先封存后 Gold、失败保留规则。不得把 semantic 容差改变混入普通代码修复；正式 benchmark 启动前需完整 client gate。 |
| G8：成本效益和最终出口 | 对现有固定 6,000 题说明可预期的精度、稀少 Damage 限制及最低实际意义；只能利用此前已合法公开/接受的开发规划信息。聚合统计不足时写成缺口，不臆造 Mistral 方差、效应或功效。若成本无法承受或无法区分有意义效果，结论为 STOP。 |

Mistral 已有静态材料报告约 13.50 GiB BF16 权重，联合资源下界约设备容量的 92.37%，后三层 offload 的静态下界约 84.71%；这些数值仅引用当前 selection decision，没有新实测，不能决定吞吐、峰值或运行时长。预期 canonical 工作量至少 **94,500** 个逻辑 generation，另有 replay/likelihood/NLI/验证，不能因最终只切换 900 行缩减成本账。

本阶段可写出后续 invented-only throughput/memory witness 的测量合同，但**不执行测量**。协议审查若认为需要该有限 witness 才能决定总成本，下一次明确授权也只能开放那一个预检阶段，仍不得捆绑 benchmark 执行。实测超出预定资源门则停，不临时调 offload、截断上下文或换精度救场。

当下 G0–G8 不是全部已通过；尤其资源实证、精度规划和完整独立前驱链仍缺。本文既不签科学运行许可，也不签工程冻结 PASS。

## 8. 结果解释、优先级与终止条件

可用的当前 Claim：在已完成的指定 Qwen fresh study、固定三数据集/三检索、共享候选池及 5% 全批次动作预算下，HGB_GBV_R 相对 GBV_ONLY_R 提升 EM 并降低 Damage。对 HGB_ONLY_R 的联合优势、ROA 复杂性价值、reader 复制、普遍稳健性和新算法均未建立。

未来 Mistral 如获准并成功完成，结果仅增加该命名 reader 条件下的证据：两个 reader 对同一比较均通过，才可称该指定比较条件复现；Qwen 未通过的 HGB-only 比较不能被后者抹去。不同 p 值不构成 reader interaction；宽区间 null 不构成等效；各 reader 的完整失败/正负方向均报告，不能跨 reader 池化后救回主张。无论其效果如何，都不能成为方法创新证据。

| 级别 | 事项 | 当前动作 |
|---|---|---|
| P0 | 旧 Phi-dependent 投稿链已终止；无可冻结独立方法；新经验扩展尚缺科学必要性/前驱/精度与失败契约 | 仅完成 G0–G8 的一次外部文档审查，作 GO-for-preflight 或 STOP；不运行。 |
| P1 | Mistral reader/容量条件广度、完整独立部署成本、公开重放质量、历史 training provenance 与污染限制 | 先在文档中明确；后续执行须新的对应准入，不能作为补救 Phi 的理由。 |
| P2 | 新特征/新 head/新 reader/新 seed/预算扫描、装饰性扩展；期刊格式工作 | 不做科学搜索。CAS 年度、ISSN、大/小类及机构规则在投稿前核验，未决定不构成现在的技术借口。 |

终止当前 CAS Q2 扩展的条件：

1. 文档审查无法指出超出既有近邻、由强控制回答的新增经验问题，或只能把形式定义/第三 reader 当贡献。
2. 无法在固定数据、监督、动作与信息预算下形成公平控制，或者必须弱化 HGB-only/隐藏 ROA 或 Phi 历史。
3. 固定可用总体的精度无法支撑有意义判断；计划只依赖“多跑很可能显著”，且没有合法的规划依据。
4. 若另获预检许可，其一次性资源/数值/独立验证门失败；成本超出冻结上界。不得自动替换 reader、缩上下文、换精度或再开一次。
5. 若以后另获科学执行许可，唯一确认/条件复现完成后没有足够精度的新增结论；不能以增加样本、模型、seed 或结果后分层抢救。
6. 完整成本、来源或数据访问限制使主要结论无法成立；缩小 Claim 后仍无足够知识增量。

停止意味着保存 Qwen 已有效完成的受控结果、Phi 失败和全部局限，形成透明技术报告并关闭本轮 CAS Q2 提交推进；不是宣布所有 RAG 修复无效，也不证明未来研究无路可走。

## 9. 阅读快照及交接约束

以下哈希是本次读取快照，保留旧文件历史，不覆写它们。repo 中最新失败/选择决定决定当前权限，旧未来式不提供授权。

| 输入 | SHA-256 |
|---|---|
| P0_3_ASTRA_XHIGH_METHOD_DECISION.md | `49f5e7781518946018a4e94e1d505f9436695b7d0a665d6c8a72a4df43250dc5` |
| P0_3_ASTRA_XHIGH_METHOD_CANDIDATE_V2.md | `7ae12f677b5ab6681e122851af2b3b5e2a19ca42f68c110b516eee4b813fd6ea` |
| P0_3_ASTRA_XHIGH_COUNTERDESIGN.md | `0c956884e110e40ddf9df69f8be7270ba01dcdecb4b9d4f1401929a06b5aa1a7` |
| P0_3_ASTRA_XHIGH_FINAL_METHOD_ROUTE.md | `b3e2e3a5397afeb556867e23b7e2f0d92293628416eb0961ce59e47364d8467d` |
| NEXT_PAPER_RESEARCH_DIRECTION_ASTRA_XHIGH_2026-09-13.md | `bd092fc1fedd2dc67f2d9d7148548d0fa69e0974fb8c9f0aa7e4d28062afbd2e` |
| repo Phi V4 failure acceptance | `ebf7a49010e0752fa3a52bba3099fe5429bab6cd47e4faf779c86e1fd29a26b3` |
| repo THIRD_READER_SELECTION_DECISION.md | `ff9346902d957a2c49d46f5b1f52409f397b40dfd85138275d1bfd457e391802` |

**交接终态：原 Phi 路线失败保留，零个新方法清除；只允许一次经验扩展的外部文档设计审查。Mistral 未获执行，所有新模型/fit/Gold 门继续关闭。**
