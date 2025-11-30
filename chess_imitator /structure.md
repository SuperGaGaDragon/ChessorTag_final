# chess_imitator repository structure

- Root utilities
  - `build_golden_from_logs.py`, `check_piece_count.py`, `style_scorer.py`, `move_logger.py`, `imitator_uci_engine.py` — one-off scripts and helpers used during style tagging and golden case generation.
  - `tagger_bridge.py` — CLI bridge that tags engine candidate payloads (delegates to `players/tagger_bridge.py`).
  - Debug scripts (`debug_*`, `test_all_highest_priority.py`, `test_candidate_check.py`) for ad-hoc validation.
- `players/`
  - Player style profiles (`Kasparov.json`, `Petrosian.json`, `YuYaochen.json`) and sample candidate payloads.
  - `api_single_move.py` placeholder API for tagging one move; `tagger_bridge.py` batches payload tagging via rule_tagger2.
- `rule_tagger2/`
  - Placeholder package marker (legacy compatibility).
- `rule_tagger_lichessbot/` — main rule tagger engine
  - Config: `config/` (tag weights, style templates), `metrics_thresholds.yml`.
  - Docs: `docs/` explaining rule system versions, algorithms, and naming conventions.
  - Core engines: `core/` (scoring, tag utilities, predictor), `engine_utils/` (prophylaxis helpers), `chess_evaluator/` (king safety, mobility, pawn structure, tactics), `rule_tagger/` legacy components.
  - Refactor path: `rule_tagger2/` (detectors, legacy core, orchestration pipeline, COD v2, models, tagging prep).
  - Orchestration: `pipeline.py`, `pipeline_mode.py`, `orchestration/` (prompts, pipeline facade).
  - Scripts: `scripts/` for diagnostics, regression, threshold calibration, tag reports.
  - Tests: `tests/` golden cases, unit tests, regression utilities; `tests/golden_cases/*.json` reference tag outputs.
  - Reports & data: `reports/`, `analysis_summary*.json`, `random_test/`, `positions.json`, `style_logs/`.
  - Meta notes: README/quick start docs, migration guides, daily summaries (`P2_DAY*.md`, `TODAY_LIST_COMPLETE.md`).
- Other
  - `style_logs/` move logs for style scoring experiments.
  - `参数合集/` and `输出/` — localized parameter and output folders (Chinese).

Use `rule_tagger_lichessbot/rule_tagger2/legacy/core.py` as the primary legacy tagging entry, wrapped by `rule_tagger2/orchestration/pipeline.py` for mixed legacy/new detector execution.
