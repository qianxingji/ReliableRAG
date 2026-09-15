# P0-I AI 工具日期证据边界

**Decision: `PASS_EVIDENCE_BOUNDED_AI_TOOL_USE_CONFIRMED_BY_DATE_EXACT_RANGE_PENDING`**

**CAS Q3 STATUS: NOT READY.**

## 可证明的事实

- `MODEL_ROUTING.md` 于 2026-09-11 留存，定义 Sol 为 `gpt-5.6-sol`、Astra 为 `gpt-6-astra`；该文件自己明确说明它不能证明正在进行的 turn 已发生模型切换，因此 **2026-09-11 不是经认证的实际使用起始日**。
- 一条留存 Sol 专属执行记录是 `docs/cas_q2/C4_JINJA_EXECUTION_BINDING_V2_ACCEPTANCE.md`，记录日期为 **2026-09-12**。
- 一条留存 Astra 专属审计记录是 `docs/cas_q2/C3_VALIDATION_V1_FAILURE_REVIEW.md`；结合此前生效的路由文件，它对应 `gpt-6-astra` / `xhigh`，日期为 **2026-09-12**。
- 所以当前仓库证据只能证明：截至 **2026-09-12**，GPT-Sol 与 GPT-Astra 两个模型族都已经留下实际使用记录。

## 不能推出的事实

这不是任一模型的真实首次使用日期，也不是完整使用区间；仓库证据不能确定实际开始日或结束日。负责人仍须依据真实记录确认 `declarations.ai_tool_version_and_use_dates` 的完整起止日期。系统不得把 2026-09-11 或 2026-09-12 自动填成首次使用日，也不得用当前日期猜测结束日。

本证据只缩小待确认范围，不批准 AI assistance statement，不关闭 P0-I，不授权公开发布或投稿。

## 工程验收

- CAS Q3 专用发现：126/126 通过。
- 项目既有 `E:\paper\ReliableRAG\.venv` 完整仓库发现：400 项通过，2 项因 Windows 符号链接权限和大小写不敏感文件系统跳过。
- 系统基础 Python 的先行完整发现加载了 370 项，因缺少 `torch`、`scipy`、`scikit-learn` 和 `threadpoolctl` 出现 2 个失败与 8 个导入错误；切换到项目已认证依赖环境后全部可执行项通过。因此该先行结果属于解释器依赖缺失，不是本次实现或科学实验失败。
