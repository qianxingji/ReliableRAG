# P0-I 负责人一次回复确认单

**CAS Q3 STATUS: NOT READY.**

生成时本地负责人输入还缺 **30** 项，且已有字段没有校验错误。本文件只列出缺失字段路径和静态填写说明；生成器不会把本地文件中已经填写的姓名、邮箱、地址或声明文本写入仓库。已核验并写入本地文件的学校所在城市和邮编无需重复提供。

## 当前缺失字段

1. `authorship.affiliations[0].department`
2. `authorship.authors_in_order[0].orcid`
3. `authorship.corresponding_author_email`
4. `authorship.corresponding_author_name`
5. `authorship.corresponding_author_postal_address`
6. `authorship.credit_role_mapping.Conceptualization`
7. `authorship.credit_role_mapping.Formal analysis`
8. `authorship.credit_role_mapping.Methodology`
9. `authorship.credit_role_mapping.Project administration`
10. `authorship.credit_role_mapping.Software`
11. `authorship.credit_role_mapping.Supervision`
12. `authorship.credit_role_mapping.Validation`
13. `authorship.credit_role_mapping.Writing - original draft`
14. `authorship.credit_role_mapping.Writing - review and editing`
15. `declarations.acknowledgements`
16. `declarations.ai_assistance_statement_approved=true`
17. `declarations.ai_tool_version_and_use_dates`
18. `declarations.all_authors_approved_final_manuscript_and_order=true`
19. `declarations.competing_interests_statement`
20. `declarations.ethics_statement_or_approval`
21. `declarations.exclusive_submission_confirmed=true`
22. `declarations.funding_statement`
23. `declarations.institutional_manuscript_approval_evidence`
24. `declarations.institutional_manuscript_approval_required`
25. `declarations.originality_confirmed=true`
26. `declarations.overlapping_work_or_preprint_disclosure`
27. `project_license.copyright_year_or_range`
28. `project_license.institutional_release_review_required`
29. `project_license.legal_copyright_holder`
30. `target_journal.institution_recognized_cas_edition_year`

## 一次回复模板

请复制下面代码块并一次填写。方括号内容是说明，不能确认的项目写“待核实”，不要猜测。个人事实和作者声明由负责人确认；中科院分区、机构审批及代码发布审查仍须保留独立证据。

```text
【单位与作者】
1. 院系/部门的正式中英文署名：
2. 第一作者的 ORCID（没有或不提供请写 NONE_NOT_SUPPLIED）：
3. 通讯作者正式署名：
4. 通讯作者邮箱：
5. 通讯作者完整邮寄地址（含院系、学校、城市、邮编、国家）：

【CRediT 贡献】
以下每项填写实际承担该角色的作者正式署名；当前只有一位作者时可填该作者正式署名，但必须据实确认。
6. Conceptualization：
7. Formal analysis：
8. Methodology：
9. Project administration：
10. Software：
11. Supervision：
12. Validation：
13. Writing - original draft：
14. Writing - review and editing：

【论文声明】
15. Funding statement（无外部资助也请明确写出）：
16. Competing interests statement：
17. Ethics statement / approval（请依据学校规则确认公开 benchmark 计算实验是否不涉及人或动物伦理审批）：
18. Acknowledgements（无则写 NONE）：
19. AI assistance statement 是否批准当前候选措辞（是/否；否时给出真实替代措辞）：
20. 实际使用的 AI 工具、版本及使用日期范围：
21. Overlapping work / preprint disclosure（无则写 NONE_DISCLOSED）：
22. 是否确认论文原创且没有一稿多投（是/否）：
23. 是否确认 Applied Intelligence 为当前唯一投稿目标（是/否）：
24. 全部作者是否批准最终稿和作者顺序（是/否；单作者也需确认）：
25. 学校是否要求投稿前论文审批（是/否/待核实）：
26. 若要求，审批状态与留存证据；若不要求，给出负责人确认记录：

【代码版权与发布】
27. ReliableRAG 原创代码的法律版权人（个人/学校/其他，写法须经确认）：
28. 版权年份或年份范围：
29. 学校是否要求代码公开发布前审查（是/否/待核实）；若要求，请给出审批状态与留存证据：

【中科院分区独立证据】
30. 湖北工业大学采用的中科院《期刊分区表》升级版年份/版本，以及 Applied Intelligence 在计算机科学大类三区及以上的留存记录路径或经办部门：
```

## 验收边界

填完上述模板后，项目组仍需把事实写入 Git 忽略的 `OWNER_INPUTS.local.json`，运行结构校验，生成新的私有 Applied Intelligence 投稿包，并完成机构分区证据、模板适配及最终 GPT-6 Astra xhigh 真实性和 claim 审计。本确认单本身不授权公开发布或投稿。
