# P0-I final source and compiled-artifact rebind — Astra xhigh

Signed: 2026-09-13, Asia/Shanghai. Auditor: GPT-6 Astra, xhigh.

**DECISION: PASS_SOURCE_AND_COMPILED_ARTIFACT_WITH_OWNER_LICENSE_CAS_BLOCKERS**

**CAS Q3 STATUS: NOT READY.** 修订源码及最终编译 PDF 足以承载已经通过 source-level 审计的有限 Qwen-only 科学陈述。本文关闭最终稿件的 source-to-compiled-content 复核与本次哈希重绑定，不签发 Submission Ready，不证明目标期刊接收、最终字体合规或公开端到端复现。作者、许可/发布安排、具体期刊及其适用 CAS 年度/类别/机构资格仍未关闭。

## 1. 对象与不变性证据

工作树：`E:\paper\ReliableRAG-cas-q2-p0-1`；分支：`work/cas-q2-p0-1`；本次检查 HEAD：`d5ea8b2d695343e958fdc800554758f4d7c501cc`。稿件及编译文件尚为未提交文件，不能以 `git diff` 无稿件输出代替无变更证明。已检查完整 tracked diff、untracked inventory、最终 main/supplement/BibTeX、asset/static/compile receipts、两份 PDF、TeX/BibTeX logs、build script、两个 verifier、BUILD_STATUS、COMPILED_ARTIFACT_ACCEPTANCE、CURRENT_TASK 和 EVIDENCE_INDEX。

本次承继的独立 source audit 为 `P0_I_ASTRA_XHIGH_MANUSCRIPT_AUDIT.md`，SHA-256 `f91b72f6ba8827cfd650a31091d28d837e78fbf1e0903532b86edcda22dc5152`。其“当时无 TeX/未编译”是历史事实；本报告记录后来真实完成的构建，不改写先前审计。

通过字节逆变换核验以下差异，而非仅接受主代理的文字描述：

- main 两段共六个 `\allowbreak `，全部去除后精确恢复 prior SHA `e1e74ea00877eee6f96f2f73c9ee50a1bbff37bc8172676be902045f0acd384f`；因此两段以外内容及其中科学文字未变。
- supplement 去除一行 `\raggedbottom` 后精确恢复 prior SHA `b11f614e311a750cc73f4a280ed0f9792ff5d1775cef25b0cfbce34571def752`。
- bibliography、六张表、两个原始 figure PDF、asset builder 和 ASSET_RECEIPT 与 prior 审计哈希一致。
- static verifier 逆换两个 limitation 状态字符串后精确恢复 prior SHA `e70bbd29581cbdb7d648be6b55f5292357744db872450c699b482a9eeec0bf71`；126 项校验逻辑未改变。
- 阅读时 EVIDENCE_INDEX 的 P0-I 文件/哈希对逐项与磁盘相符。CURRENT_TASK 与 BUILD_STATUS 的 pending rebind 是本报告签署前的正确快照，交接后应更新指向本报告，不能因此追改本报告所绑定的源码/PDF。

未发现数值、protocol、统计 family、Claim、negative result 或科学来源披露被排版变更改变。本轮没有修改科学文字、实验结果或封存文件，没有读 Gold、answer/reference payload、逐题结局、模型权重或 bootstrap draws，没有科学实验、fit/model/tokenizer/score/bootstrap 调用。

## 2. 实际检查与编译证据边界

重新执行 `verify_cas_q3_manuscript.py` 与 `verify_cas_q3_compiled_pdfs.py` 的完整 `main()` 检查逻辑，但在此次只读 harness 中拦截唯一 receipt `Path.write_text`，要求拟写内容逐字等于现有 receipt 并抑制写入。结果分别为 126 项 static/Claim PASS 与 compiled PDF mechanical PASS，两个 receipt 均完全相同。另直接调用 PDF/page/font/log 读取函数核对实际文件；没有靠 receipt 中的常量证明事实。

重新从本次绑定的最终 PDF 渲染全部页面：

```powershell
pdftoppm -r 108 -png output/pdf/manuscript.pdf tmp/pdfs/astra_rebind_main
pdftoppm -r 108 -png output/pdf/supplement.pdf tmp/pdfs/astra_rebind_supp
pdffonts output/pdf/manuscript.pdf
```

审计员实际逐页查看全部 11 页 main、3 页 supplement。未发现 clipping、重叠、空白内容页、丢失表格行、未解析引用或影响意义的缺字。main 第 6 页完整九策略表和三比较表；supplement 第 1–2 页跨页 dataset longtable 及 retriever 表内容完整，续页表头存在；第 3 页指标、历史来源、Phi/Mistral 与 cost/reproduction 限制完整。`pdftotext` 亦未出现 `[?]` 或 `??`。

TeX logs 实际记录 pdfTeX 1.40.28（MiKTeX 25.12）、LaTeX2e 2025-11-01、L3 2025-12-24，main 11 pages / 242,410 bytes，supplement 3 pages / 134,220 bytes。BibTeX log 为 0.99e、plainnat、22 entries，`warning$` 计数为零。最终 logs 无 fatal error、undefined citation/reference、overfull/underfull box。输出均为 PDF 1.5、letter 612×792 points。

构建脚本声明 main 为 pdflatex → bibtex → pdflatex → pdflatex，supplement 为两次 pdflatex；最终 logs、aux/bbl 与 PDF 相互相容。本次未重编译，也不把最终一份 log 冒称保留了每一历史 pass 的独立完整 transcript。COMPILE_RECEIPT 的 engine 和 project-lead visual-review 字段是编码记录的声明，不是自动 verifier 从零推导的视觉事实；本次自行读 logs 并查看全部 14 页，补足本次独立验收。当前普通 TeX 构建允许 MiKTeX installer 且未形成全环境字节锁，不是跨环境 bitwise-deterministic build 的证明。

## 3. 必须保留的构建提示与工程限制

1. main 的 Helvetica/Helvetica-Bold 来自两个向量 figure，未嵌入，分别出现于两幅图；supplement 无未嵌入字体。**另外实际字体清单有一个已嵌入的 Type 3 字体 `F127`。** 这不损害本次所见可读性，但最终 journal PDF profile 的 font embedding/Type 3 限制需一并核对；不能仅以“其他 TeX 字体已嵌入”暗示全部字体形式已合规。
2. supplement log 实际保留 `ignored error: Infinite glue shrinkage found in box being split`。它是非致命 longtable page-split 提示，最终内容完整；不得写成完全零错误/零提示日志。目标期刊排版阶段仍需复核。
3. 项目构建记录保留 MiKTeX installation 尚未检查更新的提示，位于 LaTeX log 外。本审计不重跑更新或安装来消除历史提示。最终日志说明所用版本，不证明已更新到任何最新版本。
4. 本轮 Poppler 渲染/字体检查仍产生 Symbol/ArialUnicode display-font stderr 提示，exit code 为零，逐页未见相应缺字。保留该事实，不将成功渲染写成零 warning。
5. `paper/build_pdfs.ps1` 有一个**非科学、可复现构建的可移植性问题**：`Get-Command` 分支返回 `ApplicationInfo`，脚本后续读取 `.FullName`；该类型实际提供 `.Path`/`.Source`，`.FullName` 为空。当前 TeX 不在此会话 PATH，fallback `Get-Item` 返回 `FileInfo.FullName`，与此次成功构建相容。若 TeX 在 PATH，该分支会失败。已先报告主代理；本次未改脚本。下一普通工程收口应统一取得 executable path 后验证两个解析分支，再更新脚本哈希。此问题不推翻已绑定 PDF 的内容真实性，但现脚本不能被宣称对两种发现方式都验证通过。

以上均不需要新科学实验。目标期刊尚未知，不能预先宣称 font/page/length/anonymity profile 全部合规。

## 4. 最终公平性、统计与 Claim 裁决

Source audit 的实质裁决不变，且最终 PDF 完整呈现：

- 唯一通过的 ordered joint comparison 是 **HGB_GBV_R − GBV_ONLY_R**：ΔEM +0.2333 pp，adjusted range [+0.0722,+0.4333]；ΔDamage −0.0722 pp，range [−0.1444,−0.0278]。不是 fusion 对每个 baseline 的优势。
- 对 **HGB_ONLY_R** 的 ΔEM +0.0556 [−0.1556,+0.3167] 跨零，联合门未通过；对其 Damage 单端点的负方向不能升级为联合胜出。fixed-action sensitivity 上端点触零仍披露。
- **ROA-FULL 未前进**。最高 point EM/F1 不是 advancement；不把其不通过说成等价或已证实无效。
- 五个 current fitted heads 的 fit/calibration recipe 匹配，不是各上游信号总历史 label budget 相等。HGB 是上游输入，fusion 是普通 logistic head；没有新算法、未与完整外部系统做 SOTA 比较。
- 一个 Qwen2.5-3B-Instruct、固定三数据集/三 retriever conditions、6,000 questions/18,000 traces、预先取得的 paired candidates，不能推广 reader/规模/领域。GbV 属局部 paired adaptation，EM/Damage 不是 faithfulness metric。
- 20,000 grouped/bootstrap family 与 conditional uncertainty 边界保持；所有 vs Keep 和 subgroup breakdown 为 descriptive；K=900 的 5% 是动作数，非 compute/retrieval/generation/latency 比例。
- 原始七个 estimator 的 fit-time ID/matrix receipts、独立原始 fit witness、更早完整 historical manifest pin 缺口未被“PDF 已编译”弥补。Phi 终局门失败、Mistral pre-engineering STOP 均排除 effect evidence，不是第二 reader 确认。

编译产物可支持当前有限经验 Claim。重大拒稿风险原样保留：知识增量窄、未对 HGB-only 联合胜出、单一 3B reader、外部 baseline 范围有限、历史 fit provenance 不完整、条件推断、未测独立部署成本，以及具体期刊可能不接受这样的 empirical/negative-boundary contribution。CAS Q3 不是质量或接收保证，不因本签署降低任何科学标准。

## 5. 尚未关闭的 Submission Ready 门

真实作者/机构/贡献/资助/COI/ethics/acknowledgements/writing-assistance 声明仍需负责人提供。Project license、第三方权利与目标刊 release/data/code 安排未定，匿名 aggregate candidate 仍不是公开端到端复现包。具体 title/ISSN、适用 CAS 年度、大类/小类、机构规则未获认证。最终 journal-specific formatting、字体 profile、submission forms 和上述 build-path 可移植性收口仍需完成。

本报告只允许继续现有证据之下的普通投稿材料收口和治理索引同步，不授权 Phi V5、Mistral、新 reader/method/seed/budget/benchmark、重开 Gold 或补做效果实验。若外部门无法真实关闭，或只能靠删除负结果/夸大 Claim 才能满足期刊，不得签 Submission Ready。

## 6. 最终关键文件哈希绑定

| 文件 | SHA-256 |
|---|---|
| paper/manuscript.tex | `cc948aa6955517060d0ab9c034baa9a6f2595db3f1bdf4218126611590d86d68` |
| paper/supplement.tex | `d7f58b3697a92362eee2cb35b4c935e6a420995e8d71d596eef4f1903d994c83` |
| paper/references.bib | `caa1ba0653f050c03445e1b100efb635dd17f813239e5a47822afc276247978e` |
| paper/ASSET_RECEIPT.json | `0d3590ffcd25a92a81c2ae638f87a3ded3141574bca80377b179d9f57df5d228` |
| paper/MANUSCRIPT_VERIFICATION.json | `3a81249a080ae48fc5c298bd7978dcdeb1aed76a86d134210f3140be8110c060` |
| paper/COMPILE_RECEIPT.json | `c65e362c749e3389f0f1deccb7a618b9279f51651176759f3f5e4d05d0ead768` |
| output/pdf/manuscript.pdf | `793413b738fb4073f13b31fbc5f4aad1ab7700c466beb719a0131f2af7619e1a` |
| output/pdf/supplement.pdf | `8b2e7f1c3bb33ba7f1abd60e388bd88e0c6a0a01cd9bde167a4bf701f1a84ee0` |
| output/pdf/manuscript.log | `9db270313748b6817f43e51da8f579cb69c153afd942743bdb05743195237316` |
| output/pdf/supplement.log | `742d0103b7c4b4ae1b7416da1473dc58904f2e608fe212fa62b38d98a32d72db` |
| output/pdf/manuscript.blg | `74ca116d67db787c18bb8dc8f3222beec385c6bd2b109c465c7390f790df54b2` |
| output/pdf/manuscript.bbl | `e60708bdd5305964430665f083f45258f7339d8dc09d079cda5ac416de747a3c` |
| paper/build_pdfs.ps1 | `4e1c768313740f48ca955cad3c574e4aecbb9ed8fcf74982f984aac33b284704` |
| scripts/verify_cas_q3_manuscript.py | `fe9e4ba245ef45395ba9d898a01a9ff89fbc03e5062d822ec18f7c103e35a96c` |
| scripts/verify_cas_q3_compiled_pdfs.py | `88894b3d0268ec6caf3896d5129569ce9a4dc36b3acc33f6dde86ff7b40e217f` |

ASSET_RECEIPT 继续绑定六张表、两幅 figure 与两份封存 aggregate，均与 source audit 一致。以下治理文档为**签署前阅读快照**；后续只将 pending rebind 更新为本报告并同步已知工程事项，不构成科学文件变更：

| 治理文件快照 | SHA-256 |
|---|---|
| P0_I_MANUSCRIPT_BUILD_STATUS.md | `80f772a79e4fa50fa8a434add93a1b5df2868a40d9b9a4493e8782f755151023` |
| P0_I_COMPILED_ARTIFACT_ACCEPTANCE.md | `72f0e8ad55f8fc3431781eddebabd898c0d5f8d89262c808f06323d4f446f1ee` |
| CURRENT_TASK.md | `93c52c71fa4d29bf50b8ad0186ddece9dabd18a71216b381e7dcaa37390d9f16` |
| EVIDENCE_INDEX.json | `2abaf45b98b1c2200891180e33b5cb483a2a14fcb6ec681f90c950a506920876` |

本轮仅新增此报告及 `tmp/pdfs/astra_rebind_*` 审阅渲染图；未改稿件、receipt、build script、日志或最终 PDF。本报告哈希在交接消息提供。任何后续源码/PDF/科学 Claim 变更须相应更新验证和重绑定；普通 build-path 修正也须保留变更与校验记录，不能继续把旧脚本哈希称为最新。

Signed: GPT-6 Astra / xhigh. **Source and compiled content accepted within the disclosed evidence boundary; CAS Q3 NOT READY.**
