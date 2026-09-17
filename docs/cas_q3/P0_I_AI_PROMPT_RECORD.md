# P0-I 私有 AI 提示词记录快照

**CAS Q3 STATUS: NOT READY.**

Decision: `PASS_PRIVATE_REDACTED_ROOT_USER_PROMPT_LEDGER_SNAPSHOT_FINAL_RANGE_AND_AUTHOR_RELEASE_OPEN`

本审计固定到 `2026-09-15T04:18:53.028Z`，只选择当前 ReliableRAG 根任务的
root-user session。它排除子代理、system/developer、assistant、工具输入输出，以及
Codex 自动注入的 goal、plugin 和 environment context 块。

共观察 333 条 user message 记录和
340 个 input-text 块；排除自动上下文后保留
47 个用户提示块，其中
37 个精确内容哈希唯一，总计
9785 个字符。私有 JSONL 仅保存脱敏文本、时间、长度和原始
提示哈希；执行了 1 次负责人值或邮箱替换。
没有命中敏感值的提示块可以逐字保留，因此该私有账本是身份最小化记录而不是匿名记录，
也不声称已经清除全部可识别项目线索。公开记录不含提示正文、会话标识或绝对 session 路径。

私有账本 SHA-256 为 `b5d424fddcfbd7c17b4432bdb9fb2937e1279ebd618202dc44c3f6883224b1dc`，大小
22771 bytes；它保存在 Git 忽略目录
`evidence/private/ai_prompt_record/`。原始未脱敏文本仍只存在于本机 Codex 会话，未另行
复制或准备发布。

该快照补强 Springer Nature 要求的 prompt-scope 可追溯性，但项目仍在继续。负责人
尚未逐条审核或批准披露，编辑也没有指定访问路径；最终结束日期仍为空。因此它不关闭
P0-I，不授权公开提示词、发布代码或投稿。
