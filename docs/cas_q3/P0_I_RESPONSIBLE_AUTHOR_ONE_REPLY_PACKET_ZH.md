# P0-I 负责人一次回复确认单

**CAS Q3 STATUS: NOT READY.**

生成时本地负责人输入还缺 **5** 项，且已有字段没有校验错误。本文件只列出缺失字段路径和静态填写说明；生成器不会把本地文件中已经填写的姓名、邮箱、地址或声明文本写入仓库。已核验并写入本地文件的学校所在城市和邮编无需重复提供。

## 当前缺失字段

1. `declarations.ai_assistance_statement_approved=true`
2. `declarations.competing_interests_statement`
3. `declarations.institutional_manuscript_approval_evidence`
4. `declarations.institutional_manuscript_approval_status=APPROVED`
5. `project_license.release_review_status=APPROVED`

## 可直接审核的候选措辞与证据位置

- AI assistance statement 候选：

  > Generative AI tools were used under author supervision for project planning and coordination; literature discovery and comparison; research-design and methodological option review; code scaffolding, implementation, debugging, and review; evidence, reproducibility, statistical, and numerical-result checking; interpretation stress-testing; and manuscript structuring, drafting, formatting, and language revision. Prompts instructed the tools to inspect retained artifacts, preserve failed runs and frozen protocols, compare methodological or editorial options, implement and test code, audit evidence and claims, and draft or revise text within author-specified boundaries. The tools did not fabricate or autonomously select data, references, results, claims, interpretations, or conclusions. Computational outputs were generated only by versioned code and frozen protocols and were independently checked against retained artifacts. The author independently reviewed the AI-assisted outputs, reran the documented verification procedures, checked references, analyses, claims, and the final text, made all final research and submission decisions, and accepts full responsibility. No AI tool was listed as an author.

  该候选按 2026-09-15 核验的 Springer Nature 新政策补充了方法选项、统计/数值复核、解释压力测试和提示词类别。见 [政策对齐审计](P0_I_SPRINGER_NATURE_AI_POLICY_ALIGNMENT.md)。请明确回答是否完整准确并批准；如不准确，请给出替代措辞。
- 如果确实不存在利益冲突，可确认：`The author declares no competing interests.`；否则请如实列出实际关系。
- 论文审批证据请存入 Git 忽略目录 `evidence/private/institutional_manuscript_approval/`，并按 `docs/cas_q3/INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD_TEMPLATE.json` 填写 Git 忽略的 `docs/cas_q3/INSTITUTIONAL_MANUSCRIPT_APPROVAL_RECORD.local.json`；记录须绑定获批稿件的实际 SHA-256、审批日期和经办单位。
- 代码发布审查证据请存入 Git 忽略目录 `evidence/private/institutional_release_record/`，并提供文件名、审批日期和经办单位。

## 一次回复模板

请复制下面代码块并一次填写。这里只列出当前仍缺的项目；已经验收的院系、正式署名和通讯邮箱不会再次索取。不能确认的项目写“待核实”，不要猜测。个人事实和作者声明由负责人确认；中科院分区、机构审批及代码发布审查仍须保留独立证据。

```text
1. `declarations.ai_assistance_statement_approved=true`：是否批准当前 AI assistance statement 候选措辞（是/否；否时给出真实替代措辞）。
2. `declarations.competing_interests_statement`：Competing interests statement。
3. `declarations.institutional_manuscript_approval_evidence`：若要求投稿前审批，给出审批状态与留存证据；若不要求，给出负责人确认记录。
4. `declarations.institutional_manuscript_approval_status=APPROVED`：学校要求投稿前审批；请在实际获批后确认状态为 APPROVED，并保留书面证据。
5. `project_license.release_review_status=APPROVED`：学校要求代码公开发布前审查；请在实际获批后确认状态为 APPROVED，并保留书面证据。
```

可选：ORCID（官方指南为 if available/recommended）；单独邮寄地址仅在不同于已填写单位地址时提供；没有致谢对象时可以不设置 Acknowledgements 段。

## 验收边界

填完上述模板后，项目组仍需把事实写入 Git 忽略的 `OWNER_INPUTS.local.json`，运行结构校验，生成新的私有 Applied Intelligence 投稿包，并完成机构分区证据、模板适配及最终 GPT-6 Astra xhigh 真实性和 claim 审计。本确认单本身不授权公开发布或投稿。
