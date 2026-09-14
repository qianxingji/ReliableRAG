# P0-I 负责人一次回复确认单

**CAS Q3 STATUS: NOT READY.**

生成时本地负责人输入还缺 **9** 项，且已有字段没有校验错误。本文件只列出缺失字段路径和静态填写说明；生成器不会把本地文件中已经填写的姓名、邮箱、地址或声明文本写入仓库。已核验并写入本地文件的学校所在城市和邮编无需重复提供。

## 当前缺失字段

1. `declarations.ai_assistance_statement_approved=true`
2. `declarations.ai_tool_version_and_use_dates`
3. `declarations.all_authors_approved_final_manuscript_and_order=true`
4. `declarations.competing_interests_statement`
5. `declarations.institutional_manuscript_approval_evidence`
6. `declarations.institutional_manuscript_approval_required`
7. `project_license.institutional_release_review_required`
8. `project_license.legal_copyright_holder`
9. `target_journal.institution_recognized_cas_edition_year`

## 一次回复模板

请复制下面代码块并一次填写。这里只列出当前仍缺的项目；已经验收的院系、正式署名和通讯邮箱不会再次索取。不能确认的项目写“待核实”，不要猜测。个人事实和作者声明由负责人确认；中科院分区、机构审批及代码发布审查仍须保留独立证据。

```text
1. `declarations.ai_assistance_statement_approved=true`：是否批准当前 AI assistance statement 候选措辞（是/否；否时给出真实替代措辞）。
2. `declarations.ai_tool_version_and_use_dates`：实际使用的 AI 工具、版本及使用日期范围。
3. `declarations.all_authors_approved_final_manuscript_and_order=true`：全部作者是否批准最终稿和作者顺序（是/否；单作者也需确认）。
4. `declarations.competing_interests_statement`：Competing interests statement。
5. `declarations.institutional_manuscript_approval_evidence`：若要求投稿前审批，给出审批状态与留存证据；若不要求，给出负责人确认记录。
6. `declarations.institutional_manuscript_approval_required`：学校是否要求投稿前论文审批（是/否/待核实）。
7. `project_license.institutional_release_review_required`：学校是否要求代码公开发布前审查（是/否/待核实）；若要求，请给出审批状态与留存证据。
8. `project_license.legal_copyright_holder`：ReliableRAG 原创代码的法律版权人（个人/学校/其他，写法须经确认）。
9. `target_journal.institution_recognized_cas_edition_year`：湖北工业大学采用的中科院《期刊分区表》升级版年份/版本，以及 Applied Intelligence 在计算机科学大类三区及以上的留存记录路径或经办部门。
```

可选：ORCID（官方指南为 if available/recommended）；单独邮寄地址仅在不同于已填写单位地址时提供；没有致谢对象时可以不设置 Acknowledgements 段。

## 验收边界

填完上述模板后，项目组仍需把事实写入 Git 忽略的 `OWNER_INPUTS.local.json`，运行结构校验，生成新的私有 Applied Intelligence 投稿包，并完成机构分区证据、模板适配及最终 GPT-6 Astra xhigh 真实性和 claim 审计。本确认单本身不授权公开发布或投稿。
