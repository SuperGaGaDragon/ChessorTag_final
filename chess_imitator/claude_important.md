# control_* 体系落地计划

目标：在保留 `cod_*`（决策标签，带动态 gating）的同时，引入正交的 `control_*` 语义标签，复用统一的行为检测函数，避免复制/分叉 `cod.py` 逻辑。最终需要有回归测试覆盖 lichessbot golden cases，确保新增标签稳态运行。

## 步骤拆解
- 0）梳理现状与入口
  - 主要行为逻辑集中在 `rule_tagger_lichessbot/rule_tagger2/legacy/cod_detectors.py`（调用 `_cod_gate`、phase_bonus 等）和 `cod_v2/detector.py`。决策入口由 `legacy/core.py` / `core/tagging.py` 汇总，tag schema/weights 位于 `core/tag_catalog.yml`、`models.py`、`metrics_thresholds.yml`。
- 1）抽取纯语义模式层（新增 `rule_tagger_lichessbot/rule_tagger2/detectors/shared/control_patterns.py`）
  - 为每个子类型写独立的 `is_file_seal(ctx, cfg) -> SemanticResult` 等函数：仅做“动作/局面”判定，返回 {passed, metrics, why, severity/score}，不涉及 dynamic 选择、cooldown、互斥。
  - 记录依赖的 ctx 字段（如 volatility_drop_cp、opp_mobility_drop、break_candidates_delta、passed_pawn_targets 等），并在 docstring 中保证接口稳定，便于 cod 与 control 复用。
- 2）整理 fallback / 顺序依赖
  - 在 shared 层明确耦合关系：例如 file_seal → freeze_bind 的兜底、blockade_passed 对 passed pawn 的要求、king_safety_shell 对 king_safety 与 space clamps 的交互。用小型 helper 复用（如 `build_recapture_window`、`phase_bonus` 调用），避免在 wrapper 里重新计算。
- 3）重写 cod 包装层（保留 gating，只重定向到 shared）
  - `legacy/cod_detectors.py` 和 `cod_v2/detector.py` 中，将现有判定主体替换为对 shared 函数的调用，再附加 `_cod_gate`/cooldown/priority 选择；确保 gate_log、suppressed_subtypes、score 计算保持行为兼容。
  - 维持当前 fallback 顺序（例如 freeze_bind 触发后不重复 file_seal），但把“是否允许”与“动作成立”分离：先 shared 判定通过，再由 gating 决定 cod 标签是否成立。
- 4）新增 control_* 语义层（不做 gating）
  - 新建 `rule_tagger_lichessbot/rule_tagger2/detectors/control.py`：为每个子类型调用 shared 判定，任何 passed=真 即直接落地 tag（如 `control_file_seal`），容许与 `cod_*` 并存。
  - 在 `core/tag_catalog.yml`、`models.py`、`versioning/tag_aliases.py` 注册新标签与 schema；在 `core/tagging.py`（或等效入口）插入 control 检测调用点，放在 CoD 之后/之前均可，但需保证两者互不覆盖。
  - 配置：如需边权，可在 `metrics_thresholds.yml` 添加默认 weight；若权重暂缺，可设为与 cod 同阶或留空默认 1。
- 5）流水线与遥测
  - 让 `ctx.metadata["last_cod_state"]` 等记录继续服务于决策层，同时为 control_* 暴露相同的 metrics/why，方便日志对齐。
  - 在 `cod_v2/config.py` 或全局 env flag 增加 `ENABLE_CONTROL_TAGS`（默认 on），便于灰度。
- 6）兼容与清理
  - 移除（或标记弃用）任何直接 copy 的 cod 分叉；检查 `tag_aliases`、API payload、`models.TagFeatures` 结构是否需要新增字段以便下游消费。
  - 更新文档：`cod_v2/README.md`、`docs` 内添加“决策标签 vs 语义标签”解释与字段表。
- 7）测试与回归（必须包含 golden cases 检测模块）
  - 单元层：为 shared/control_patterns.py 写纯函数测试（构造 ctx fixture 覆盖 simplify/plan_kill/freeze_bind/... 的通过与拒绝边界）。
  - 决策层：复用现有 `cod_v2/test_detector.py` / legacy tests，确认 gating 行为未回退。
  - 语义层：新增 `rule_tagger_lichessbot/tests/test_control_tags.py`，读取 `tests/golden_cases/*.json`（含 `cases_highest_priority.json` 等）或 player 批次样本，跑管线，断言对应 `control_*` 与 `cod_*` 均可同时命中或独立命中；确保 lichessbot/playerbatch/golden cases 覆盖新增标签。



## 本轮排查与修复（control_* 未出现原因）

- 问题现象：跑 `test_all_highest_priority.py` 时，新增的 `control_*` 标签完全不出现在 tag 列表里（只有 cod_* 或其他 legacy 标签）。
- 根因梳理：
  1) 语义判定层已有 `detectors/shared/control_patterns.py` 与 `detectors/control.py`，但 legacy pipeline (`rule_tagger_lichessbot/rule_tagger2/legacy/core.py` 与 `core_v8.py`) 未调用 `detect_control_patterns`，也未把布尔结果写入 `tag_flags`/`TagResult`，导致标签永远为 False。
  2) `TagResult` 构造参数中的 control_* 字段此前全部硬编码为 False，进一步锁死输出。
  3) `tag_flags` 未包含 control_*，即使判定通过也不会进入 raw_tags → gated_tags。
- 采取的修复：
  - 在 `legacy/core.py` 与 `legacy/core_v8.py`：
    - 引入 `detect_control_patterns`（复用 shared 语义）。
    - 增加 `CONTROL_TAGS` 与 `control_flags` 初始化。
    - 调用 `detect_control_patterns(ctx, control_cfg)` 填充 `control_flags`，并写入 `analysis_meta["control_semantics"]`。
    - 将 control_* 写入 `tag_flags`，在 `TagResult` 里用真实 `control_flags` 替代 False。
  - 路径修正：shared 模块对 legacy helper 的导入改为 `...legacy`，消除 ImportError。
- 验证（仅观察 control_* 是否出现，不比对 expected）：
  - 运行 `python3 test_all_highest_priority.py`，Case7 输出包含 `control_file_seal`、`control_regroup_consolidate`，且保留 `cod_file_seal` 与 `control_over_dynamics`，证明 control_* 已进入管线且与 cod_* 共存。其他用例未触发 control_*，符合语义未命中的直觉。
- 后续建议：
  1) 补最小集成测试：构造能命中各子类型的 ctx fixture，断言 control_* 写入 tag_flags/raw_tags，同时不影响 cod_* gating。
  2) 给 `tag_schema_validator.VALID_DETECTORS` 添加 ControlDetector（或放宽校验），避免未来严格模式 warning。
  3) 在 pipeline/facade 层确认 `ENABLE_CONTROL_TAGS` 默认开启，同时保留开关用于灰度。
