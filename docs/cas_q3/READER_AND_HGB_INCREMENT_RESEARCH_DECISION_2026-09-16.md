# Reader 扩展与强 HGB-only 对照的贡献判断

日期：2026-09-16。**CAS Q3 STATUS: NOT READY。** 目标期刊仍为 JIIS。

状态：`REOPEN_READER_DESIGN_AND_DESCRIPTIVE_DIAGNOSIS`。
这是针对用户“现在需要一个 reader，然后组合方案相对较强的 HGB-only
贡献强度也不太行”的研究决策与已执行诊断，不是已冻结执行协议、独立最终审计或
新 reader 的实验结果。作者最新 PDF 保持不变。

后续用户授权“如果实验结果不符合预期，请调参”。已增加
`READER_DEVELOPMENT_TUNING_POLICY_2026-09-16.md`：在开发 fit 分组内开展三折、
三个主要方案等预算的参数搜索，保留独立校准集，并在正式测试前冻结选择。下文的
原固定参数配置继续作为参考；主分析采用哪一配置及其多重比较范围须在新协议中明确，
不能看完测试结果再择优。当前没有执行任何调参 fit。

## 1. 决策

增加一个有效 reader 条件有研究价值，但它解决的是证据范围；强对照上的贡献需要
单独检验。保持经验研究定位，将新增问题明确为：

> 在候选对、下游监督和动作数量匹配时，额外验证信号会如何改变相对 HGB-only
> 的替换选择？减少损伤和保留恢复机会之间的关系，在另一个 reader 条件下是否重现？

不把“融合普遍更准”设为必须得到的结果，也不把增加 reader 视为算法创新。
已有 ROA、RECA/双头方向的失败或不足不得通过更名恢复为最终方法。
当前没有已经建立独立创新性且战胜 HGB-only 的新算法。

本次用户指令重新打开 reader 研究设计和有界可行性准备的任务范围，取代“永远只做
Qwen 稿件收尾”的工作优先级。它不把历史 STOP 或 Phi 验证失败改为 PASS。
正式神经实验仍须先形成科学与工程均可执行的前瞻协议；无需等待网页端再次批准常规工作。

## 2. 已有强对照证据与本次实际完成的诊断

数据来自公开代码库提交 `038d769e96d092a2eec3bbc5df9f45f3c2a17ff0` 的
`outputs/reproduction_v1/TRACE_NUMERIC.jsonl.gz`，SHA-256：
`a930286d62bddf9f4837cb1beb4b863f0f94c1bc697b2311977a9b0eb18f09f7`。
比较中 HGB-only 精确指监督匹配的 `HGB_ONLY_R`，不是原始 `HGB` 排序器。

| 策略 | 替换数 | Recovery | Damage | Net |
|---|---:|---:|---:|---:|
| HGB_ONLY_R | 900 | 357 | 26 | 331 |
| HGB_GBV_R | 900 | 352 | 11 | 341 |
| 融合减去 HGB-only | 0 | -5 | -15 | +10 |

既有主分析 EM 差异为 +0.0556 个百分点，六端点校正区间
[-0.1556, +0.3167]；Damage 差异为 -0.0833 个百分点，区间
[-0.1833, -0.0056]。联合规则未通过。固定动作的次要敏感性分析中，Damage
区间上端到 0。来源为 `P0_B_RESULT_CLAIM_MAP.md`；本次没有重跑 bootstrap。
不能由 EM 不显著推出等效、非劣或“准确率不损失”。

本次用 `scripts/describe_hgb_fusion_disagreement.py` 完整读取已公开的 18,000
条数值记录，按实际 `REPLACE` 动作交集分解，并与上述封存总数核对：

| 冻结动作成员关系 | 条数 | Recovery | Damage | Neutral |
|---|---:|---:|---:|---:|
| 两策略共同替换 | 506 | 243 | 1 | 262 |
| 仅融合替换 | 394 | 109 | 10 | 275 |
| 仅 HGB-only 替换 | 394 | 114 | 25 | 255 |

融合将 HGB-only 的 394 个选择换成另外 394 个选择；这一交换少恢复 5 条、少损伤
15 条，净增正确 10 条。两组独选集合不是随机分组，不能作因果机制证明。
“少损伤”可支持后续问题的形成，不能事后改写原主假设。未被任一策略替换的行只构成
潜在候选对结果，不能计入实际 Recovery/Damage。完整报告保留全部九个 dataset ×
retriever 单元，禁止只挑有利单元。

复算命令（输出必须为新路径，不覆盖旧报告）：

```powershell
python scripts/describe_hgb_fusion_disagreement.py --input E:/paper/ReliableRAG-Code/outputs/reproduction_v1/TRACE_NUMERIC.jsonl.gz --output docs/cas_q3/HGB_FUSION_DISAGREEMENT_2026-09-16.json
```

这项工作是事后描述性诊断，使用已经公开的 EM 标签；没有新增 fit、模型推理、
bootstrap、问题筛选或测试集调参。它不会替代冻结分析。

## 3. Reader 选择与资源路线

保持在任何 Mistral 实验结果产生前已选定的
`mistralai/Mistral-7B-Instruct-v0.3@c170c708c41dac9275d15a8fff4eca08d52bab71`。
理由是它提供不同于 Qwen 的模型家族和约 7B 的容量条件，且官方权重为 Apache 2.0。
不主张这是当前最强 reader，也不因性能未知而不断换 reader。官方模型卡：
<https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3>。

这是第二个可望取得有效结果的 reader；Phi 是失败的 reader 尝试，不能算作第三个
有效验证条件。Mistral 之前停在协议和资源设计阶段，没有取得负面科学结果。

本机 RTX 5060 Ti 总显存 16,311 MiB；本次检查时已用约 1,215 MiB，系统总 RAM
约 31.1 GiB、可用约 6.1 GiB，E 盘可用约 216.8 GiB。这些只是当时资源快照，
不是最大负载通过的证明。旧 BF16 权重约 13.50 GiB，直接沿用旧 CPU offload
方案尚未证明可承受。

本轮优先设计独立的新部署条件：从上述原始权重做 bitsandbytes 4-bit NF4，BF16
compute，batch size 1；量化配置、是否 double quant、版本和 kernel 均须在预检前
唯一确定。官方实现提供 NF4 和 BF16 compute 配置，但不能据此声称本机已经兼容：
<https://huggingface.co/docs/transformers/quantization/bitsandbytes>。
如该条件不能通过资源与数值验证，记录失败并停止，不临时改变量化或 reader 搜寻胜者。

4-bit 条件尚未执行或冻结，不能当作旧 BF16 协议的等价复现。所有策略在同一
Mistral 条件下共用相同候选对与分数；跨 reader 的差别同时含模型家族、容量和部署
精度，因此只能支持两个完整 reader 条件下的实证结果，不能因果归因于家族或容量。

## 4. 实验应当增加什么知识

保留原 4,500 development question 的 fit/calibration 分组与 6,000 test question
及检索输入，重新生成 Mistral 答案对和该 reader 的分数，在 development 上按冻结
配置重拟合各监督头。不能用 Qwen 的头假装已经适配，也不能将 Qwen 的有效训练样本数
照搬。新 reader 的 eligible 数、正负例数、fit/calibration 数和全部参数必须实报。
原始 HGB、GbV 及其余既有策略保留完整上下文，不能仅呈现有利的两个对照。

建议保留两个方向的主比较：融合减 HGB_ONLY_R，以及融合减 GBV_ONLY_R；各报告 EM
与 Damage。若采用此四端点新 reader 家族，仍用按 dataset 分层、question-cluster
成组、每 draw 重分配全局 top-K 的 20,000 次 bootstrap；四端点校正分位数为
0.00625/0.99375。原 Qwen 的六端点结果不改为四端点以缩窄区间。K=900/18,000
为主条件；不依测试标签选择 K。

本次动作交集诊断在 Mistral 上预先指定为完整报告项，包括共同、各自独选、两者不选
四组及所有 dataset/retriever 单元。它解释数字从何而来，不增加新的显著性主张。
结果应分别说明：能否复现较低 Damage、Recovery 如何改变、Net/EM 的区间有多宽。
一边显著而另一边不显著，不等于 reader 交互显著。

如需考察动作比例依赖，可在读取 Mistral 结果前规定完整次要网格
1%、2.5%、5%、10%，但必须先验证每个比例的 eligibility 与固定 tie 处理。
这是待设计的次要分析，不是现在授权重算 Qwen 以选择“最优 K”，也不能成为替代主终点。

这些 test 问题的 Qwen 结果已经被看到。使用同题新 reader 能控制题目变化，但不是
全新问题总体的独立确认；新研究问题也受到 Qwen 结果启发，须明确披露。当前剩余
HotpotQA 未打开问题只有 105 个，不能假装现有文件支持另一个均衡 6,000-question
独立确认集。若转向新算法，必须另做独立数据来源与有效验证设计。

## 5. 价值、精度和停止规则

第二 reader 的价值是检验条件依赖与损伤/恢复分解，而非承诺证明 +0.0556 pp
这样的小增益。旧协议审查的假设性精度预算给出 EM 校正区间半宽约 0.226--0.339 pp；
这些来自旧开发统计的敏感性估算，不是 Mistral 的功效保证。当前样本规模很可能仍难以
判断微小准确率差异。不能因区间跨零便不断增加种子、题目或 reader，直到显著。

旧 STOP 所列资源和数值缺口仍是真实缺口。下一版协议必须在正式生成前关闭：

1. 从已接受 Qwen/历史输入绑定开发、测试、检索、标签隔离和 replay 身份；不能借用
   Phi 失败产物作已认证前驱。
2. 固定量化/tokenizer/chat template/EOS/padding/attention、组件加载顺序、
   likelihood 与 GbV/NLI 接口、异常及 eligibility 的明确处理。
3. 完整规定可复验 witness。区分答案 target token 和 prompt token，给出词表 logits
   保存的有限字节上界；不能沿用旧草案 124 TiB 级的极端未决存储分支，也不能悄悄
   将完整 softmax 验证降为不可独立还原的摘要核对。
4. 在新运行前确定归一化/量化/scoring/replay 的数学数值契约与人工 fixture，
   禁止从 Phi 的已知偏差倒推容差或将新容差追溯赋予 Phi。
5. 明确预检与正式运行的 RAM、显存、磁盘双份归档、wall-clock 上界和停止行为，
   实测最坏长度与实际吞吐。当前低空闲 RAM 尚不支持宣布 GO。
6. 对“估计条件差异”而非“保证融合获胜”的目标重新完成成本/精度取舍；既不捏造
   最小有用效应，也不把没有新结果当作通过价值审查。旧 STOP 不因本文件自动关闭。

只有通过这些前瞻检查，才执行固定的一次完整 reader 条件。无论得到正面、负面或
不确定结果均保留并报告；资源或语义验证失败也保留。若强对照仍无可信增量，论文的
贡献就应是一个可复现、明确限定条件的经验研究，不能声称新方法已优于 HGB-only。
如果读者条件之间也没有可解释且精度足够的新认识，不能仅凭多一个模型宣布稿件变强。

## 6. 当前工作清单

- **P0 已完成**：公开 18,000 条数值的动作交集分解，与封存 Recovery/Damage/Net
  对账；reader 和贡献问题的研究决策；最新用户指令同步到当前任务入口。
- **P0 未完成**：关闭上述前瞻协议缺口并完成科研设计/真实性与公平性验收，随后才能
  运行 Mistral。当前没有新 reader 结果，没有相对 HGB-only 的联合优势。
- **P1**：执行并复验 reader 扩展；完整报告有效样本/正例、参数、成本和交集诊断；
  若结果允许，再决定正文贡献表述及公开复现包更新。
- **P2**：稿件与公开代码同步、JIIS 终审。用户暂停的合规收尾不在本轮推进。

主要拒稿风险：较强对照增量小且不确定、单一有效 reader、单一修复操作、题目已被查看、
稀有 Damage 事件与训练不确定性不足、公开端到端神经复现范围仍有限。
新增 reader 可以缩小其中一个缺口；不能提前宣称全部解决或达到 Submission Ready。
