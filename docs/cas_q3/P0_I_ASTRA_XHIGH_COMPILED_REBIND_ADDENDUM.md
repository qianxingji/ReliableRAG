# P0-I post-audit engineering addendum — Astra xhigh

Signed: 2026-09-13, Asia/Shanghai. Auditor: GPT-6 Astra, xhigh.

**DECISION: PASS_SOURCE_AND_COMPILED_ARTIFACT_WITH_OWNER_LICENSE_CAS_BLOCKERS — REAFFIRMED.**

**CAS Q3 STATUS: NOT READY.** 本附录重绑定普通工程修订后的文件。原 `P0_I_ASTRA_XHIGH_COMPILED_REBIND.md`（SHA-256 `d6b3dab290122b992cce1615a9025e55e7aef2c78b88cbaffbe6013c76b3d131`）保留为历史审计；以下当前文件哈希取代其对应旧条目。科学、公平性、Claim 和主要拒稿风险裁决全部维持。

## 核对结果

1. 完整阅读修订后的 `build_pdfs.ps1`、compiled verifier、COMPILE_RECEIPT、BUILD_STATUS、COMPILED_ARTIFACT_ACCEPTANCE。Executable resolver 现返回统一字符串路径：ApplicationInfo 分支使用 `.Path`，fallback FileInfo 分支使用 `.FullName`，调用方直接使用该字符串。原 PATH 分支缺陷已修复。
2. 本审计从实际脚本 AST 只提取 `Resolve-Executable`，分别在不含 local MiKTeX 的 PATH 和显式添加该目录的 PATH 下，检查 pdflatex/bibtex，共四项 resolver 校验通过；随后恢复进程 PATH。主代理记录两个解析分支均完成 full build；本轮独立复核的是解析分支、最终日志和产物，未再次执行 TeX build。
3. Compiled verifier 增加 Type 3 字体检测和机器字段，实际记录 main `F127`、supplement 空列表，且 BUILD_STATUS/COMPILED_ARTIFACT_ACCEPTANCE 同步披露。已有 fatal/undefined/box 检查与字体/longtable 允许范围没有为求 PASS 而放宽。
4. 主稿、补充、bibliography、ASSET_RECEIPT 和 MANUSCRIPT_VERIFICATION 的 SHA-256 与前次 rebind 完全一致。没有科学内容、数值、原始结果或 Claim 变更。
5. 再次从**当前最终 PDF** 独立以 108 dpi 渲染 11+3 页至 `tmp/pdfs/astra_engineering_*`，与本审计员上次实际逐页查看的 `astra_rebind_*` PNG 按页逐字节比较，14/14 完全相同。旧视觉审查继续覆盖当前可见页面内容。按 main 1–11、supp 1–3 顺序生成 `[kind,page,PNG_SHA256]` 数组，采用无空格 JSON 序列化，其 SHA-256 为 `3308112ce3d546660937a4b249d350dcf1cf2963747ddfaf36941a7937b7b80b`。
6. 两个 verifier 的完整检查逻辑再次运行，以写入拦截要求拟写 receipt 与现有文件逐字一致且抑制写入：static 126 项 PASS；compiled mechanical PASS；两份 receipt 内容完全相同。当前 PDF/log 实际哈希均与 COMPILE_RECEIPT 一致。

本轮只生成审阅 PNG、解析/校验并新增此附录；没有修改稿件、PDF、receipt 或脚本，没有 Gold/answer/reference payload 读取、fit/model/tokenizer/score/bootstrap 或其他科学实验。

## 保留提示与门

Main 仍有未嵌入 Base-14 Helvetica/Helvetica-Bold 和已嵌入 Type 3 F127；supplement 仍保留非致命 longtable `ignored error: Infinite glue shrinkage found in box being split`，页面内容完整。MiKTeX installation 未检查更新的历史提示与本轮 Poppler Symbol/ArialUnicode display-font 提示保留。不能签目标期刊 PDF/font profile 全面合规。

唯一联合阳性仍是 HGB_GBV_R 对 GBV_ONLY_R，未对 HGB_ONLY_R 联合胜出，ROA-FULL 未前进。单个 Qwen 3B、普通校准融合、GbV adaptation、历史 fit 证据缺口、条件推断、5% 动作非 compute、Phi/Mistral 无 effect evidence 和缺失独立部署成本均维持。正文和补充的可见内容完全相同，故此次工程修订不扩大任何 Claim。

原 rebind 的 executable-path 普通工程待办现可关闭。作者/机构/声明、权利人许可与发布安排、具体目标刊与适用 CAS 年度/大类小类/机构规则、期刊专属格式及最终提交材料门仍开放；不得据本附录签 Submission Ready。治理文档中 pending rebind 可同步为原报告及本附录，但须继续保留这些外部门和科学拒稿风险。

## 最新哈希

| 文件 | SHA-256 |
|---|---|
| paper/build_pdfs.ps1 | `d1289ef78cecef64d7c80c63e4e737c727ea052997c058a1dd8acffdb3c96ae3` |
| scripts/verify_cas_q3_compiled_pdfs.py | `fd88d77491a28b51348792e446b1597efd3e4df326e2e2c43418edea44cfd83d` |
| paper/COMPILE_RECEIPT.json | `5736b6c9bf266dd8595bcf12ce7d2c1c7148a976ce306a0aa954e6aefa0b50ee` |
| output/pdf/manuscript.pdf | `c9150d15ae9023160c07437735333754a897a3331450d1e57388eed7703aa641` |
| output/pdf/supplement.pdf | `fcf134c7695f9c706db376996856240e4980332ef5b4843a7d2095f6c4788d61` |
| output/pdf/manuscript.log | `b6f5232891128c3be4327afd7b79c60446599db1b0ab562fe2e8ad929b9b0e82` |
| output/pdf/supplement.log | `67a7875570018f0f70e6cca77ab54a5c56f65d62bbf598f9acbe26cce1fa033f` |
| output/pdf/manuscript.blg | `74ca116d67db787c18bb8dc8f3222beec385c6bd2b109c465c7390f790df54b2` |
| output/pdf/manuscript.bbl | `e60708bdd5305964430665f083f45258f7339d8dc09d079cda5ac416de747a3c` |

以下内容未变，继续受绑定：

| 文件 | SHA-256 |
|---|---|
| paper/manuscript.tex | `cc948aa6955517060d0ab9c034baa9a6f2595db3f1bdf4218126611590d86d68` |
| paper/supplement.tex | `d7f58b3697a92362eee2cb35b4c935e6a420995e8d71d596eef4f1903d994c83` |
| paper/references.bib | `caa1ba0653f050c03445e1b100efb635dd17f813239e5a47822afc276247978e` |
| paper/ASSET_RECEIPT.json | `0d3590ffcd25a92a81c2ae638f87a3ded3141574bca80377b179d9f57df5d228` |
| paper/MANUSCRIPT_VERIFICATION.json | `3a81249a080ae48fc5c298bd7978dcdeb1aed76a86d134210f3140be8110c060` |

已读治理快照：BUILD_STATUS SHA `a423e890a660b71cc743cc80b0fcdb334b10032186ac50e4621ea9227e14d572`；COMPILED_ARTIFACT_ACCEPTANCE SHA `9eb96b7ebee158b26de0d9af793a9624171a093a5b0ef0ae762a21bc43ed131d`。后续状态同步视为快照更新，不改变本附录绑定的稿件/PDF。附录自身 SHA-256 在交接消息提供。

Signed: GPT-6 Astra / xhigh. **Prior source-and-compiled-artifact PASS reaffirmed; CAS Q3 NOT READY.**

## Final governance-state rebind

Signed again: 2026-09-13, GPT-6 Astra / xhigh. Static verifier 中的一条 limitation 从 `final_Astra_xhigh_compiled_artifact_rebind_pending` 改为 `final_Astra_xhigh_compiled_artifact_rebind_recorded_separately`；MANUSCRIPT_VERIFICATION 同步该状态。对两个当前文件分别逆换这一处字符串，精确恢复此前已绑定哈希 `fe9e4ba245ef45395ba9d898a01a9ff89fbc03e5062d822ec18f7c103e35a96c` 与 `3a81249a080ae48fc5c298bd7978dcdeb1aed76a86d134210f3140be8110c060`。因此校验逻辑和其他内容均未改变。完整 static verifier 在 receipt 写入抑制/逐字一致模式下再次通过 126 项检查。

本节取代前述两个文件的旧哈希，其余绑定与裁决不变：

| 文件 | 最终 SHA-256 |
|---|---|
| scripts/verify_cas_q3_manuscript.py | `91628fd2008fcf92e2163bc6235a613d51b8659baa326bb8d26f9bbc7727d906` |
| paper/MANUSCRIPT_VERIFICATION.json | `d065d3599efef5680bcb1cc701bb62489a866fe953859fc0e70d817e2bb76eb6` |

**Final decision remains PASS_SOURCE_AND_COMPILED_ARTIFACT_WITH_OWNER_LICENSE_CAS_BLOCKERS. CAS Q3 NOT READY.** 本次只追加本节；未修改其他文件或开展科学实验。已记录独立审计不能消除作者、许可、CAS 资格及目标期刊格式门。本附录追加后的最终 SHA-256 在交接消息提供。
