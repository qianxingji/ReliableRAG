# P0-I 本地 Codex 会话元数据审计

**Decision: `PASS_LOCAL_CODEX_TURN_CONTEXT_METADATA_START_BOUND_END_DATE_PENDING`**

**CAS Q3 STATUS: NOT READY.**

固定截止时间为 `2026-09-15T03:32:41.264Z`。审计扫描本机 Codex session JSONL，
只解析 `session_meta` 与 `turn_context` 行，并以当前 ReliableRAG 项目任务目录名选择
会话；不解析消息、response 或工具内容，也不输出绝对路径或会话标识。

## 结果

- 扫描 115 个 session 文件，选中 6 个项目会话，共 379 条目标模型 `turn_context`。
- `gpt-6-astra`：62 条；effort 计数 `{"high": 3, "xhigh": 59}`；首个本地日期 2026-09-10，末次观察日期 2026-09-14。
- `gpt-5.6-sol`：317 条；effort 计数 `{"high": 317}`；首个本地日期 2026-09-11，末次观察日期 2026-09-15。
- 选中元数据规范化 SHA-256：`72347ee7b80c6ea3322e4c5467d5875e312e3c6a4e09452d83f3f7a1dc6593fd`。

## 声明边界

该本机记录支持把 ReliableRAG 项目任务的 AI 使用开始日期写为 **2026-09-10**，并支持精确工具 ID `gpt-6-astra` 与 `gpt-5.6-sol`。截止快照的末次观察日期为 **2026-09-15**，但项目仍在继续，所以该日期不是最终结束日。最终投稿前必须重新冻结末次使用日期并由作者批准完整 AI assistance statement。

本审计不关闭 P0-I，不授权公开发布或投稿。

## 工程验收

首次基础-Python 调用在生成结果前因系统没有 IANA `tzdata` 失败。实现随后改用协议时区 `Asia/Shanghai` 在 2026 年固定对应的 UTC+08:00 偏移，不新增依赖；三个合成回归测试、129 项 CAS Q3 专用发现和项目环境 403 项完整仓库发现全部通过，完整发现另有两项 Windows 平台条件跳过。该工程失败不涉及消息内容、模型调用、科学数据或实验结果。
