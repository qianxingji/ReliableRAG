# 本地 Codex 执行任务：ROA 原始复现与审查包

2026-09-11 接续说明：本任务卡的原始认证、重放和两个监督对照已完成；随后按新冻结设计补做 HGB_ONLY_R。两项贡献晋级规则均失败，没有获准进入最终确认的候选。最新入口为 CURRENT_TASK.md 与 P0_3_RESEARCH_DECISION.md。下文保留原始交接合同，不应再次执行封存实验。

当前目标为中科院二区 Submission Ready；不是 JCR Q2。
本任务依据 Work 已冻结的科研设计实施，不自行改变科研方向。
当前候选为 ROA-FULL，开发支持标签为 GBV_AUGMENTED_ONLY。

## 任务一：接续分支并认证原始产物

原始工程根目录：`E:/paper/ReliableRAG`。
新代码来自 `origin/work/cas-q2-p0-1`（草稿 PR #1）。先记录原工作区
的分支、commit 与未提交改动。在新 worktree 中运行工具，保留原目录、
未提交改动和所有封存产物。不要 reset、clean 或覆盖原实验目录。

以下是 PowerShell 示例；如果原项目路径不同，按实际位置调整变量。
不用重新安装 GPU 环境；认证和打包工具只使用 Python 标准库。

```powershell
$experimentRoot = "E:/paper/ReliableRAG"
$taskStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$auditWorktree = "E:/paper/ReliableRAG-cas-q2-$taskStamp"
$integrityReport = "E:/paper/roa-integrity-$taskStamp.json"
$reviewBundle = "E:/paper/roa-review-$taskStamp.zip"

git -C $experimentRoot status --short
git -C $experimentRoot fetch origin work/cas-q2-p0-1
if ($LASTEXITCODE -ne 0) { throw "获取审查分支失败" }
git -C $experimentRoot worktree add --detach $auditWorktree origin/work/cas-q2-p0-1
if ($LASTEXITCODE -ne 0) { throw "创建隔离工作区失败" }
Set-Location $auditWorktree
git rev-parse HEAD

python -m scripts.verify_roa_artifacts --project-root $experimentRoot --output $integrityReport
if ($LASTEXITCODE -ne 0) { throw "产物认证未通过：保留报告，停止后续步骤" }

python -m scripts.package_roa_review_bundle --project-root $experimentRoot --output $reviewBundle
if ($LASTEXITCODE -ne 0) { throw "打包未通过：保留报错，不替换原始文件" }
```

认证清单覆盖 216 个 payload，共 54,435,934 字节；ZIP 另含原始 manifest。
工具在写入和回读 ZIP 时均检查内容哈希。它只生成本地文件，不上传任何
内容，也不改变科学状态。压缩后的大小取决于原始内容。

该 ZIP 是给 Work 私下审查的原始材料，**不要提交到公开 Git 仓库**。
它只包含 ROA namespace，上游 score/outcome 产物还需按下面要求追溯。
本任务卡不表示 Work 已经启动了本机 Codex 会话。

## 任务二：实际数值重放

读取 CURRENT_TASK.md、CURRENT_METHOD.md、EVIDENCE_INDEX.json。
在认证后的原目录中读取 design.py、learning.py、metrics.py、prepare.py、
execute.py、independent.py 及其 import；不要直接运行可能重新拟合的旧脚本。

1. 跟踪 INPUT_VERIFICATION.json 和 EXECUTABLE_CONFIG_FREEZE.json 中的
   上游输入、环境和 commit。验证 parent manifests，追溯所有学习型输入分数
   的训练 ID 与 cohort 角色；未知重叠不能标记为已排除泄漏。
2. 从真实实现提取必要代码进入可审查的工程分支，保留原始算法和特征顺序。
   如需编辑，先在新 worktree 创建自己的工程分支，避免修改原实验分支。
3. 用已保存系数、预处理参数和校准器重放 28 个 context、56 个模型及原验证器
   覆盖的全部行；不以少量抽样通过替代全量验收，不做科学 refit。
4. 独立核对分组、概率、动作集合和指标。数值容差沿用 1e-10；动作成员与
   tie-break 必须完全一致。记录任何失败与平台差异，不改阈值以制造 PASS。
5. 输出写入全新目录，绑定源码 commit、配置、seed、环境、命令、输入/模型
   哈希及输出哈希；原封存目录保持不变。

## 回传给 Work 的最小验收材料

| 材料 | 必须包含 |
|---|---|
| 工程 PR / commit | 真正的重放实现、执行命令、环境与变更说明 |
| 产物认证 JSON | 216 个 payload 的哈希与覆盖核验结果 |
| REPLAY_VALIDATION.json | 全量覆盖计数、最大数值误差、动作差异、指标差异、失败记录 |
| UPSTREAM_PROVENANCE.json | 每个学习型输入分数的训练范围与父产物哈希；未知项明示 |
| 原始 ROA 审查 ZIP | 本工具生成的字节匹配材料及其 SHA-256，用于 Work 独立复核 |
| 简短阶段报告 | 做了什么、没能完成什么、科学拟合/检索/生成调用次数、CAS Q2 状态 |

如果当前机器没有原始产物，回传具体路径和缺失列表即可；不要创建替代
数据、重新导出后修改 manifest，或宣称重放通过。

## 后续边界

本任务的认证/打包/重放要求科学拟合、检索和生成调用均为 0。
Work 验收重放后，再按 CONTROLS_PROTOCOL.md 运行 GBV_ONLY_R 和 HGB_GBV_R。
两个对照使用相同划分、拟合/校准规则和 5% 动作预算；没有新的特征搜索。
当前不拟合最终部署模型，不选择新确认 ID，不恢复风险头或 MILP 搜索。

阶段末明确输出：**CAS Q2 STATUS: NOT READY**，直到项目整体验收条件满足。
