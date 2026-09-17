# P0-I Springer Nature AI 政策对齐审计

**CAS Q3 STATUS: NOT READY.**

Decision: `PARTIAL_PASS_CURRENT_SPRINGER_NATURE_AI_POLICY_MAPPED_AUTHOR_APPROVAL_FINAL_DATE_AND_ARTIFACT_OPEN`

## 当前政策与适用判断

- [Springer Nature policy-update announcement](https://group.springernature.com/gp/group/media/press-releases/sn-policy-responsible-ai-use/53209516)（访问日期：2026-09-15）
- [Springer Nature journal-specific author guidance](https://link.springer.com/journal/10489/submission-guidelines)（访问日期：2026-09-15）
- [Springer Nature editorial policy](https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation)（访问日期：2026-09-15）
- [Springer Nature editorial policy](https://www.springernature.com/gp/policies/editorial-policies/using-ai-in-research)（访问日期：2026-09-15）
- [Springer Nature researcher guidance and FAQ](https://group.springernature.com/gp/group/ai/ai-guidance-for-our-researchers-and-communities)（访问日期：2026-09-15）

Applied Intelligence 的期刊级指南要求将超出纯 copy editing 的 LLM 使用写入 Methods 或合适的替代部分。Springer Nature 当前总政策进一步要求披露工具版本、使用日期、提示词和贡献范围，并要求分析、解释和结论保持作者主导。因本项目包含生成式研究设计、代码、分析复核和起草支持，纯 copy-editing 例外不适用。

本项目的低风险用途包括：project planning and coordination；literature discovery and comparison；code scaffolding and review；formatting and language revision。需要谨慎并明确记录人工复核的用途包括：research-design and methodological option review；code implementation and debugging；statistical and numerical-result checking；interpretation stress-testing；manuscript structuring and drafting。本审计没有把任何无监督生成的假设、数据、结果或结论认定为可接受用途。

## 待负责人批准的替代声明

旧候选只覆盖协调、代码/证据审查和写作，遗漏方法选项、统计/数值复核、解释压力测试和提示词范围，不能作为当前政策下的完整声明。新的候选是：

> Generative AI tools were used under author supervision for project planning and coordination; literature discovery and comparison; research-design and methodological option review; code scaffolding, implementation, debugging, and review; evidence, reproducibility, statistical, and numerical-result checking; interpretation stress-testing; and manuscript structuring, drafting, formatting, and language revision. Prompts instructed the tools to inspect retained artifacts, preserve failed runs and frozen protocols, compare methodological or editorial options, implement and test code, audit evidence and claims, and draft or revise text within author-specified boundaries. The tools did not fabricate or autonomously select data, references, results, claims, interpretations, or conclusions. Computational outputs were generated only by versioned code and frozen protocols and were independently checked against retained artifacts. The author independently reviewed the AI-assisted outputs, reran the documented verification procedures, checked references, analyses, claims, and the final text, made all final research and submission decisions, and accepts full responsibility. No AI tool was listed as an author.

具体工具、模型、推理等级和最终日期范围仍由单独字段记录。该候选描述提示词类别，不声称公开了逐字完整会话；负责人仍须确认类别是否完整、是否需要向编辑提供更细的私有记录，以及最终结束日期。

私有 Applied Intelligence 构建器现将获批声明写入 Study design 内的 Methods 等价小节，并保留匿名公共源中的占位状态。新的合成身份端到端构建生成 13 页 PDF，编译、字体和全部页面视觉检查通过；它不包含真实负责人身份，也不是实名投稿包。

## 尚未关闭

- responsible-author confirmation that the revised scope and prompt categories are complete and accurate
- final AI use end date after project work ends
- author-populated Applied Intelligence build using the approved disclosure
- final artifact-bound GPT-6 Astra xhigh policy, authenticity, fairness, claim, and reviewer audit

本审计不批准声明，不关闭 P0-I，不授权发布或投稿。
