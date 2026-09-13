# ReliableRAG 正式转向 CAS 三区后的科研路线与 Submission Ready 审计

External independent audit receipt SHA-256:
`9d75c003ed9ea28206b7c75f376f188be98e93a9ecbe1b91eea68b1395925977`.

日期：2026-09-13（Asia/Shanghai）
决策模型：**GPT-6 Astra，xhigh**
证据快照：`E:\paper\ReliableRAG-cas-q2-p0-1`，HEAD `f1f353917bdac9630279fcbda075718ecb418ed8`，读取时 worktree clean
用户最新授权：**“转三区吧”**。最高投稿准备目标现为 **CAS Journal Ranking Q3 Submission Ready**；不是 JCR Q3。
**CAS Q3 STATUS: NOT READY。**

文件名保留最初 conditional audit 的任务约定；本文结论已按随后明确的目标转换授权形成。它是正式目标转换后的路线审计，不再把“是否转三区”留作待确认。本文没有修改 repo，没有写论文正文，也不签实际投稿、科学实验或新模型执行许可。

## 1. 唯一执行建议

**推进一篇以现有有效 Qwen study 为全部科学核心的受控经验论文，先完成证据—Claim—目标期刊适配验收；不追加 reader、独立算法或科学实验。**

唯一执行建议字符串：

**`PROCEED_Q3_QWEN_ONLY_EVIDENCE_AND_JOURNAL_FIT_GATE_NO_NEW_EXPERIMENTS`**

现有 Qwen 证据**足以作为经验稿件的科学核心**，已超出仅有设想或开发点估计的阶段；但尚不能据此认定某本 CAS 三区期刊会接收，也尚未达到 Submission Ready。贡献范围应固定为：在一个命名 reader、三个数据集、三个检索条件、共享原/修复候选与统一动作上限下，检验监督匹配后的信号增量及 Damage 权衡。

本次降低的是投稿定位与主张的外推范围。真实性、标签隔离、公平比较、统计标准、失败保留及可复核要求不降；旧主比较不会因转三区改判。CAS 分区是期刊层面信息，不能作为单篇论文质量、录用难度或方法新颖性的保证。

Phi 的 `FAIL_P0_1_PHI_DEVELOPMENT_AUTHENTICITY` 和 Mistral 的 `STOP_MISTRAL_EXTENSION_BEFORE_ENGINEERING` 保持终局。RECA/新算法搜索不恢复。既有 CAS Q2 实验扩展停止的历史事实不改写；新的 Q3 路线重用已有效完成的 Qwen 研究，不借目标转换重新打开被停止的实验。

## 2. 为什么现有证据能够形成科学核心

有效研究包含五个事前固定的监督匹配头、raw HGB/raw GbV/V2/Keep 的完整九政策背景，固定 development fit/cal、6,000 个 fresh question groups、18,000 条三检索 traces，统一 900 次动作 cap，动作先封存后映射 Gold，20,000 个按数据集分层的 question-cluster bootstrap，并在每次重采样中重分配全批次 top-K。

`EMPIRICAL_D_ACCEPTANCE.md` 接受完整冻结分析及独立计算验证：全部 20,000 draws、原始 multiplicity bytes、整数事件、全政策动作、六个主端点调整区间通过；validator 独立展开 row copies，不调用 analysis executor。它证明计算与冻结协议对应，科学解释仍以 `P0_3_FRESH_RESULT_DECISION.md` 为准。这些证据足以支持一篇具体、有边界的受控测量研究。

| 原冻结主比较 | EM差值，pp［六端点调整区间］ | Damage差值，pp［调整区间］ | 当前可用结论 |
|---|---:|---:|---|
| ROA-FULL − HGB_GBV_R | +0.0444［−0.1333, +0.2037］ | +0.0611［+0.0000, +0.1278］ | 联合门未过，更多复杂性未建立联合收益 |
| HGB_GBV_R − HGB_ONLY_R | +0.0556［−0.1556, +0.3167］ | −0.0833［−0.1833, −0.0056］ | EM区间跨零，联合门未过；原主分析的Damage降低可如实报告，但不能升级为联合优势 |
| HGB_GBV_R − GBV_ONLY_R | +0.2333［+0.0722, +0.4333］ | −0.0722［−0.1444, −0.0278］ | 联合门通过，固定条件下EM提高且Damage降低 |

以上保留原 Qwen **三比较×两端点的六端点 family** 与 `default_rng(20260926)`。不能移用未执行 Mistral 草案的四端点 family/20260930 seed，更不能只保留成功比较重算更窄区间。表中数字来自既有签署结果，不是本轮重新分析。

在18,000条trace分母上，fusion相对GbV-only的点差相当于约42个额外正确答案和13个更少Damage事件；这是读者评估实际量级的表达，不证明其收益足够抵消全部系统计算。ROA相对fusion仅多8个正确答案、同时多11个Damage，已由既有review记录。不得由最大EM点估计选择ROA为最终方法。

科学信息主要来自**对照对象改变后证据结论的差别**：加入HGB到GbV的信息组合有联合支持；加入GbV到HGB尚无联合支持。这两个比较检验不同增量，不是两组p值的正式差异检验，不能写成已经证明两个信号效应大小不同或存在显著交互。该结果也提醒读者：单看相对Keep的提升、raw verifier的比较或复杂模型点排名，不能回答监督匹配后的增量问题。

仍有实质拒稿风险：普通两特征融合缺算法新意；效应量有限；单一约3B Qwen reader的广度窄；benchmark-derived bounded pool不是全语料搜索；历史学习来源和部署成本有缺口。完成很多工程检查不会自动弥补这些问题。需要用直接近邻文献和清晰研究动机，证明这组控制回答了读者此前不能直接从已有结果得到的具体问题。若该知识增量无法建立，转三区也不能创造贡献。

## 3. 标题、贡献和 Claim 边界

建议唯一工作标题：

**Supervision-Matched Selection of Paired RAG Repairs: An Empirical Study of Accuracy and Damage**

中文工作标题：**配对 RAG 修复的监督匹配选择：准确率与损伤的经验研究**。

这是标题与贡献定位建议，不是论文正文。题目不承诺新算法、普遍可靠性、跨reader复制或正式风险保证。摘要和研究对象的首处说明必须点名Qwen条件及有限语料池。

可组织的贡献：

1. **具体的增量发现。** 在冻结Qwen fresh study中，监督匹配fusion相对GbV-only同时改善EM/Damage；对HGB-only的联合优势未建立。保留完整六端点，不用“验证器普遍有效”概括。
2. **复杂性与损伤的受控测量。** ROA-FULL未通过相对简单双信号融合的联合门；增加特征后的点EM收益伴随更多Damage。结论是本设置中未建立增量，不是“复杂方法永远无用”或与fusion等效。
3. **可追溯的测量协议与证据交付。** 提供固定候选、监督/动作匹配、按question分组重采样、完整失败/成本边界和对应可核对产物。它增强研究可信度与复用价值；不把日志量、内部验收流程或已有统计工具包装成独立方法创新。

明确允许的主 Claim 为：**在该独立于已开发问题的固定fresh cohort、指定Qwen reader、三数据集/三检索、共享候选池与全局5%动作预算下，HGB_GBV_R相对监督匹配的GBV_ONLY_R提高EM并降低Damage。** “fresh”只描述当时的冻结研究身份；当前这些结果已经公开，不是未来新方法的未见确认集。

以下表述不允许：SOTA、普遍优于两个单信号基线、GbV在HGB之上已有稳定增益、证明HGB比GbV更有因果价值、ROA获选、跨reader/域稳健、全系统零样本迁移、无污染、正式风险控制、全语料泛化、生产部署安全、5%算力、独立部署加速或全流程跨机神经重现。

HGB始终是上游估计器/比较器，HGB_GBV_R是既有监督校准政策。其训练目标Recovery与评估Net/Damage不同，不能通过转向修改学习目标、增加Damage head或新损失，再混为同一研究。

## 4. 第三 reader、独立算法与额外实验是否为硬前提

| 项目 | Q3本路线的裁决 | 原因与边界 |
|---|---|---|
| 第二/第三个有效reader | **不作为本稿科学核心的统一硬前提；当前不执行** | 单reader研究可以回答限定reader的问题；读者不能由此推断跨reader。如果选定期刊明确要求更广验证，属于该目标不匹配或另案研究需求，不能私自解除STOP |
| Phi成功验收 | **不是本Qwen经验稿前提，且继续禁止使用** | Phi独立获取失败不会自动推翻已验收Qwen链；也不提供正/负科学效果。不得修门限、V5或提取Phi指标 |
| Mistral预检/实验 | **不是硬前提，STOP有效** | 既有G0–G8审查失败是事实。改投Q3不补齐其资源/数值/价值契约，也不发执行许可 |
| 新的独立算法/RECA | **不需要且不恢复搜索** | 选择经验文章类型后，贡献必须来自新知识；普通fusion不应被改名为算法突破 |
| 新seed、budget curve、新题/新dataset、新head | **非机械必需，当前禁止** | 已有冻结研究有完整主分析；新增搜索会改变问题和选择偏差，不能作为“三区补一点实验”的默认动作 |
| 重新跑已完成Qwen/fit/Gold/统计分析 | **禁止** | 有效证据已封存；更换分区不产生重复或改进显著性的理由 |
| 真实standalone latency、新主机神经replay | **不是当前窄Claim的硬前提** | 对应claim不提出，缺失明确披露；若未来以效率或全面可复现性为核心才成为对应证据门 |
| 直接近邻文献、外部基线忠实性、证据映射 | **必须** | 能否形成有意义经验贡献需要回答，纯写作包装不能替代 |

不能由“CAS三区”推出一个统一的模型数量或新算法要求；要看具体期刊文章类型和实际主张。作为编辑标准的实证例子，PLOS ONE官方明确考虑负/零结果，同时要求适当控制、复现细节、数据支持的结论，并要求重复/衍生研究给出充分科学理由。这说明经验/负结果文章有正式发表路径，并不保证本稿符合任何具体期刊，更不证明PLOS ONE属于当前用户认可的CAS三区。[官方发表标准](https://journals.plos.org/plosone/s/criteria-for-publication)、[官方文章类型](https://journals.plos.org/plosone/s/what-we-publish)。

Qwen结果有有限精度，必须如实解释；但未执行Mistral的δ/H*未定，不是重判Qwen研究无效的依据。Mistral准入需要在新94,500次canonical generations之前论证支出价值；本路线已经有观察到的Qwen区间，目标是如实报告其有限信息。不能事后为Qwen补造“预定最低效应”、功效或等效margin；也不能据此宣称实际收益一定足够大。

## 5. Q3 Submission Ready 的 P0 必须验收清单

所有P0通过后才能签 **CAS Q3 STATUS: SUBMISSION READY**。目标转换本身不能通过其中任何一项。以下主要是既有证据组织、文献/许可审查和稿件验收，不要求重跑科学实验。

| P0门 | 必须交付与通过标准 | 当前状态 |
|---|---|---|
| P0-A 研究贡献与直接近邻 | 一页研究问题/比较方向/知识增量表；用论文原文、作者或会议/期刊官方来源逐项说明现有GbV/配对选择/监督融合工作已经回答什么，本研究额外回答什么。明确普通算法身份，不以名称或更多实验规模替代贡献 | 方向成立；尚缺针对最终经验稿的闭合文献—贡献验收 |
| P0-B 完整结果与Claim映射 | 原六端点主表、全部九policy背景、三数据集/三检索次要结果、同draw fixed-action sensitivity、Recovery/Damage/Neutral/Net/F1与样本/动作分母，均直接绑定已接受汇总产物；逐句Claim标明主/次/历史/不成立 | 有效结果已存在；最终面向稿件的映射待完成 |
| P0-C 方法与公平性可读说明 | 精确模型revision、prompt/池/retrieval、4,500开发及3,600/900fit/cal、6,000fresh身份角色、五head特征/配方、七固定upstream与V2来源、common eligibility/缺失、K=900/ties、Gold封存顺序；GbV明确为published component的paired adaptation，非原论文整系统原样比较 | 底层协议/验收已有；最终完整方法说明待审 |
| P0-D 统计与不确定性 | 20,000 grouped draws、dataset strata、三个siblings、draw-level topK重分配、固定models/pools、六端点多重性、计数和pp单位一致；没有独立18,000样本假设、训练不确定性/精确覆盖/等效保证 | 冻结计算已接受；最终图表文字需独立核对 |
| P0-E 来源、失败和数据边界 | 明示七原始fit-time receipts缺失、历史whole-manifest缺口、HGB原始/replay bytes差异与已证数值范围、旧NumPy/线程/IO适配限制；fresh与历史开发分离，Phi排除及Mistral停止可核查；没有新证据暗示影响Qwen链的泄漏/污染/篡改 | 限制已有；须在文章/补充材料中准确呈现，不能省略或编造闭合 |
| P0-F 成本与效率边界 | 采用接受的shared C1–C4调用/token/stage成本表；区分canonical/replay/preflight/历史拟合、动作与算力；明确缺失canonical C2/C3 peaks、per-generation/standalone latency和统一end-to-end/FLOPs | 成本对账已接受；最终可引用表与局限待整理 |
| P0-G 可交付复核材料 | 给审稿人可访问的代码/配置/模型参数或合法获取方式、冻结版本与哈希、data来源与许可、精确复现步骤、全部主结果与动作/统计产物、必要补充表和失败摘要；匿名化/个人路径/许可证/敏感信息检查。私有archive存在不能自动算公开可用 | 已有多项静态与CPU重放交付；面向目标期刊的开放/匿名交付尚未验收 |
| P0-H 目标期刊适配与资格 | 确定期刊全名/ISSN、官方scope/article type、用户认可的分区年度/大类或小类及机构规则，直接核验对应CAS分区；确认审稿所需材料、许可、费用/限制可满足。不得用JCR、第三方博客或最新网页排名替换认可年度 | 全部待定；当前不能签“Q3目标已落实” |
| P0-I 稿件与最终独立审查 | 获得论文正文撰写授权后完成完整稿件/补充材料/参考文献/作者与披露，逐数字/图表/Claim及投稿政策检查，由Astra xhigh做真实性/公平性/Claim/Reviewer/Submission Ready终审；不把内部PASS日志数量作为发表论证 | 未写正文；当前没有完整submission package |

P0-E不要求通过篡改记录“恢复”已不存在的旧receipts。当前可行路径是将科学主张严格限制在固定原始saved estimators与已验收fresh chain，提供可验证的真实来源及已知缺口。若进一步审查发现缺失来源使训练/测试隔离本身无法成立、关键结果无法独立核对，或者目标期刊的数据/代码政策无法满足，则是硬STOP，不能用“已披露”免除真实性问题。

P0-G要求可兑现的复核途径。当前通过的source/data relocation、saved-parameter replay、180-trace实际generation replay与full saved-witness检查要分别描述；没有全量另一主机神经重放就不承诺它。保持科学标准不等于无限增加审计，现有接受门不重复执行；交付物引用原验收及原sealed文件。

## 6. P1 可提升竞争力与 P2 不开展事项

**P1，优先用已有接受产物完成：** 更清晰的对照解释、固定次要dataset/retriever表与图、事件量级/成本分母并排呈现、可访问的精简补充材料、逐条回应“只是logistic fusion”“单reader”“未胜HGB-only”“缺少standalone成本”等预期质疑。可以改善可读性、材料组织和公开复核，不读新Gold、不计算新选择规则、不把已有次要结果升为主结果。

**P1的非默认未来研究选项：** 跨reader/新population、独立部署时延与新主机神经复现能扩大相应Claim，但它们当前没有许可且不是本稿P0。若编辑要求，先判断能否用现有证据与缩小Claim回应；否则记录该期刊适配失败，或另作明确的新前瞻科研治理。不能把reviewer要求当作自动启动被停止实验的授权。

**P2，当前不做：** 额外reader/model/seed/budget/head/特征/提示搜索、RECA重新命名、为新算法身份堆模块、扩大数据取得显著性、任意事后分层、新方法排行榜比较、无助于具体Claim的全环境重复审计。期刊模板美化在P0-A至H至少形成明确结论后进行，不先花时间包装尚未闭合的论文定位。

## 7. 必须披露的 negative results、provenance 与成本

主文/主结果表须清楚呈现：fusion对HGB-only未过联合门；ROA对fusion未过联合门；单一Qwen条件；原六端点统计；Damage全总体分母；fixed-action sensitivity不能救回两个失败比较；相对Keep的八个switching policy提升只是原固定次要点估计，没有新增显著性主张。

历史和补充材料须保留：V2主要优越性未成立、RG-HGB/dual-head/ROA相关已完成研发否决、先前2Wiki LODO floor失败及它们是development历史而非新的fresh验证。只需与论文研究选择有关的清晰时间线和完整可查附录，不把主文写成内部工具故障日记；未执行方法草稿不冒充实验负结果。

Phi须说明：曾计划reader-axis扩展；13,500 canonical与180 replay获取存在正面机械/forensic证据，但原validator和唯一corrected semantic validator均失败，frozen norm门未过，所有Phi行排除科学分析。它既不是reader效果为负，也不计作复制成功。Mistral须说明其在工程之前被资源/数值/价值契约审查停止，无Mistral科学结果。二者不参与任何跨reader平均或“两个模型一致”的措辞。

来源须说明：上游历史训练的原始逐fit证据缺口、原始HGB与reproduction的线程元数据byte差异及所有已检数值相同的范围；新receipts不等于旧receipts。来源同benchmark、共享语料池、上游训练历史及模型预训练污染不能完全排除。没有证据就不宣称训练数据独立；同retriever siblings的相关性不因样本数增加消失。

接受的canonical Qwen acquisition有54,000 generation receipts、51,901,556 prompt tokens、826,362 generated tokens/score-step forwards；另有540-receipt实际replay。C4有16,932 likelihood forwards、8,534 NLI forwards/42,946 pairs等shared工作。全部九policy共享这些候选与计算。900动作不是5%generation或5%verification计算，也不是某policy standalone成本。

保留stage timers各自边界，不把1,096.562s C2、45,216.887s C3、5,337.573s base、3,523.022s GbV、157.658s policy allocation相加冒充统一end-to-end measured latency。缺失canonical C2/C3 peak/per-generation/standalone latency、BGE token总量和FLOPs时写缺失，不填预检峰值或估算值。Q3路线不以再跑填这些非核心缺口为默认任务。

## 8. 三区、目标未知与 Submission Ready/acceptance 的区别

当前尚未确定目标期刊、分区年度、机构认大类还是小类及其他认可规则。因此现在可以判定稿件科学路线是否可信，不能判定某本期刊“已满足用户的三区要求”。CAS官方平台明确提供大、小类两套学科分区，具体查询存在登录入口；本轮没有登录受限账户或核验任何具体期刊的分区。[中国科学院文献情报中心期刊分区表官方入口](https://www.fenqubiao.com/)。

期刊页面接受经验/负结果文章，只说明其文章类型，不证明它是CAS三区。PLOS官方标准在本文仅作发表规则实例，不列为已核验候选或推荐目标。没有用非一手来源推测journal ranking；不以刊名、APC或影响因子猜分区，不承诺录用时/发表时仍有相同分区。

**Submission Ready**是我们可审计的准备状态：有匹配的真实目标期刊、完整真实材料、可核对数字、合理贡献及合规交付，所有P0已过，适合提交同行评审。它不是“实验运行结束”，不是“肯定值得任何三区接收”。

**Acceptance**由编辑/审稿人决定，涉及相关性、知识增量、外部方法选择、单reader限制、审稿意见及修回。即便本方签Submission Ready，仍可能desk reject、外审拒稿或被要求超出当前证据范围的新增实验。不能用内部成功率估计替代外部审稿。

若目标期刊只接受显著独立算法贡献或需要本文不拥有的泛化/独立原始训练证明，应认定适配失败；不得将真实局限抹去以符合期刊。确定目标后需按其官方scope、article type、数据/代码/匿名政策与所要求的CAS年度核验，不能声称“三区期刊都一样”。

## 9. 条件成功率：只作为主观资源规划

若需要一个粗略规划区间，我对**完成上述全部P0、选择真正接纳受控经验研究且已核验为用户认可CAS三区的一个合适目标、允许正常修回的一次投稿流程最终接收**，给出 **约30%–60%** 的主观判断。

这是未校准的专家式判断区间，不是计算的概率或置信区间；没有该目标的真实接受率、完整稿件或同类投稿样本支撑，不能作为对外承诺。范围之外的实际机会完全可能发生。不能把“约五成”视为已通过科学门，不能将其代入数学公式制造多次转投的虚假总成功率。

区间的关键假设：最终文章把增量方向讲清；完整报告未胜HGB-only与ROA否决；直接近邻尚未充分回答这个同监督/同候选/同动作预算问题；当前Qwen真实性和标签隔离验收无新的反证；目标接受有限单reader经验贡献；材料可依法交付；写作与图表达到审稿可读标准。所有假设均不是已证实的期刊录用条件。

主要向下因素是研究发现过窄、已被文献覆盖、目标要求新算法/更广reader、历史来源无法满足其政策，以及明显过度Claim。向上因素是匹配的经验文章定位、清楚的可用知识、强控制和可复核交付；不是省略负结果或重新跑出显著结果。

对“达到Submission Ready”的机会不另给虚假百分比：它是具体P0门的工作验收，不是随机彩票。当前存在可行的零新科学实验准备路径，但P0-A/G/H等仍可能揭示不可关闭的障碍。若障碍发生，必须报告NOT READY/STOP，而不是为了兑现预估降低标准。

## 10. 唯一下一阶段、停止条件与当前终态

唯一下一阶段为**Qwen经验稿的证据—Claim矩阵与目标期刊适配审查**：以现有accepted聚合产物整理完整主次结果、方法/统计/成本/来源边界；用直接一手文献检验知识增量；建立官方scope与CAS年度/类别核验清单。先通过这道门，再在正文撰写获得授权后进入完整稿件与补充材料准备。本文没有正文撰写或外部投稿执行授权。

停止Q3推进的条件：直接近邻已完全回答同一问题而本稿无额外经验信息；完整结果无法形成可信知识增量；发现使Qwen主结果不成立的重大数据/来源/公平性缺陷；可交付材料无法满足目标政策；没有与单reader经验范围匹配且符合机构CAS规则的目标；或者最终稿只能通过改写失败/夸大方法才能成立。停止后保存技术报告与全部历史，不自动转向更多模型或更宽搜索。

本次目标转换不修改任何历史统计门、模型文件、参数、cohort、actions、hash、validator容差或失败决定。科学fits仍为185；本轮新增实验、模型/tokenizer、fit、score/bootstrap、Gold、ID选择、repo修改均为0。联网只读官方期刊政策和官方CAS入口，没有新科学数据获取。

**结论：现有Qwen可作三区经验稿科学核心；Phi/Mistral/新算法不是本路线硬前提且继续停止。正式目标已转为CAS三区，当前仍未达到Submission Ready。**

**唯一执行建议：`PROCEED_Q3_QWEN_ONLY_EVIDENCE_AND_JOURNAL_FIT_GATE_NO_NEW_EXPERIMENTS`。**
**CAS Q3 STATUS: NOT READY。**

## 附录：读取快照

已阅读本次要求的全部文件。旧文档中的未来式由最新终局接受/STOP及用户目标转换指令约束；阅读后并发更新属于新快照，不能据此倒称原hash失败。以下是本轮read-only hash；本文未重做科学真实性运行。

| 输入（相对worktree） | SHA-256 |
|---|---|
| AGENTS.md | `1a53ad68633946f2500e5924249cf2b1acf53b51c4e76da7615bf38afed155cf` |
| docs/cas_q2/PROJECT_CHARTER.md | `ad9a5c723aa7f42eaf00bcc49df23ac4df1e023d7d377a67e19595618dcbe641` |
| docs/cas_q2/CURRENT_TASK.md | `c0ca8d6b2527827c3d59c7f064c2f3643b26a45b7df07982b6896a85e2d1a7bc` |
| docs/cas_q2/CURRENT_METHOD.md | `43d13af6e20926282ed38656c5838f3a31afdfde277010a4868c482b7ed3bafe` |
| docs/cas_q2/EVIDENCE_INDEX.json | `de87075cb5f296cf430f66b1b170fd359ebdebcab36276ba132010be674f7936` |
| docs/cas_q2/P0_3_FRESH_RESULT_DECISION.md | `7e3c450b83e373b5ab8e60cbc35a3342d9efbaf41e6c84885f512e95ebda8870` |
| docs/cas_q2/EMPIRICAL_D_ACCEPTANCE.md | `839989e744c74df5deb5b54a2cba8f4bf75e9ef11470d38901efd1ef29f30e85` |
| docs/cas_q2/EMPIRICAL_COST_ACCEPTANCE.md | `901775251f3dd2478cf11f65dea0fafb2d7557bc520ea10ef5c5e864e24819cb` |
| docs/cas_q2/PHI_READER_DEVELOPMENT_RUNTIME_V4_FAILURE_ACCEPTANCE.md | `ebf7a49010e0752fa3a52bba3099fe5429bab6cd47e4faf779c86e1fd29a26b3` |
| docs/cas_q2/MISTRAL_EMPIRICAL_EXTENSION_PROTOCOL_GO_STOP_REVIEW.md | `2fbef9e52ad2ed7dd32c708f8d3ed46cb5069259175e780a12ce39d00b36bf4a` |
| docs/cas_q2/POST_PHI_FAILURE_RESEARCH_GOVERNANCE.md | `ecaf663edd3e5ffdb7a15569bf6c2932a0168865a90305377ee418ed5fcd9fb4` |
