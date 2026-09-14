# P0-I 负责人一次回复确认单

**CAS Q3 STATUS: NOT READY.**

生成时本地负责人输入还缺 **6** 项，且已有字段没有校验错误。本文件只列出缺失字段路径和静态填写说明；生成器不会把本地文件中已经填写的姓名、邮箱、地址或声明文本写入仓库。已核验并写入本地文件的学校所在城市和邮编无需重复提供。

## 当前缺失字段

1. `declarations.ai_assistance_statement_approved=true`
2. `declarations.ai_tool_version_and_use_dates`
3. `declarations.competing_interests_statement`
4. `declarations.institutional_manuscript_approval_evidence`
5. `declarations.institutional_manuscript_approval_status=APPROVED`
6. `project_license.release_review_status=APPROVED`

## 一次回复模板

请复制下面代码块并一次填写。这里只列出当前仍缺的项目；已经验收的院系、正式署名和通讯邮箱不会再次索取。不能确认的项目写“待核实”，不要猜测。个人事实和作者声明由负责人确认；中科院分区、机构审批及代码发布审查仍须保留独立证据。

```text
1. `declarations.ai_assistance_statement_approved=true`：是否批准当前 AI assistance statement 候选措辞（是/否；否时给出真实替代措辞）。
2. `declarations.ai_tool_version_and_use_dates`：实际使用的 AI 工具、版本及使用日期范围。
3. `declarations.competing_interests_statement`：Competing interests statement。
4. `declarations.institutional_manuscript_approval_evidence`：若要求投稿前审批，给出审批状态与留存证据；若不要求，给出负责人确认记录。
5. `declarations.institutional_manuscript_approval_status=APPROVED`：学校要求投稿前审批；请在实际获批后确认状态为 APPROVED，并保留书面证据。
6. `project_license.release_review_status=APPROVED`：学校要求代码公开发布前审查；请在实际获批后确认状态为 APPROVED，并保留书面证据。
```

可选：ORCID（官方指南为 if available/recommended）；单独邮寄地址仅在不同于已填写单位地址时提供；没有致谢对象时可以不设置 Acknowledgements 段。

## 验收边界

填完上述模板后，项目组仍需把事实写入 Git 忽略的 `OWNER_INPUTS.local.json`，运行结构校验，生成新的私有 Applied Intelligence 投稿包，并完成机构分区证据、模板适配及最终 GPT-6 Astra xhigh 真实性和 claim 审计。本确认单本身不授权公开发布或投稿。
