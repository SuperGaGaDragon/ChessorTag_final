用户上传棋局 → imitator/player_batch 运行

（你已经有命令行例子）
imitator 会产出：

chess_imitator/.../reports/<player>.csv

② 拷贝 CSV → style_report/Test_players/<player>/raw.csv

目的：保留数据快照

③ metrics 层跑 data_calc.txt 里的指标，输出 metrics.json

（你提供指标列表）


④ 使用 GM reference 做对比 → gm_comparison.json

例如从：

style_report/current GM metrics/Petrosian/Petrosian.csv
tigran_intro.txt


读取出一个统一格式：

gm_comparison = {
   "closest": ["Petrosian", "Kramnik", "Carlsen"],
   "distance": {...},
   "tag_diff": {...},
}

⑤ LLM 解析（my_model + overall_instruction）

my_model.txt：逐标签解释

llm_overall_instruction.txt：给你最终风格画像、对比分析、独特性

GM intro.txt：辅助判断相似度

所有这些文字最后写进一个：

player_profile.json

⑥ UI：生成 HTML 模板 → build to static report

## Phase 2 — 让表格和新版报告真正跑起来（Codex）

请严格按 codex.md 的步骤继续，从 Step 8 开始：

1. **改用新 prompts 文件**
   - 所有 LLM 调用必须只读：
     - `style_report/prompts/model_section.md`
     - `style_report/prompts/overall_section.md`
   - 不再使用 `my_model.txt` 和 `llm_overall_instruction.txt` 作为直接 prompt，只能当备份参考。
   - 确认 `run_full_report.py` 里读的就是这两个 `.md` 文件。

2. **生成分析文本（确保有 Markdown 表格）**
   - 在 `run_full_report.py` 里，把 `player_profile.json` 做成一小段 JSON 字符串，按 codex.md 的要求拼在 prompt 末尾。
   - 用 `llm_client.call_llm()` 分别调用：
     - `model_section.md` → `model_section` 文本（必须包含 markdown 表格）
     - `overall_section.md` → `overall_section` 文本（也要包含 markdown 表格）
   - 把结果写入：
     - `style_report/Test_players/<player-id>/analysis_text.json`
     - 结构保持：`{"model_section": "...", "overall_section": "..."}`

3. **HTML 渲染层：让表格显示出来**
   - 在 `style_report/templates/report_base.html` 中，继续使用占位符：
     - `{{PLAYER_ID}}`
     - `{{OVERALL_SECTION_HTML}}`
     - `{{MODEL_SECTION_HTML}}`
   - 在 `run_full_report.py` 里：
     - 从 `analysis_text.json` 读取字符串。
     - **暂时可以接受 Markdown 直接塞进 HTML**：只做简单的 `\n\n` → `<p>` 或 `<br>` 替换，不要破坏 `|` 和 `---`，保证 markdown 表格语法原样保留。
     - 把处理后的文本替换两个占位符，输出到：
       - `style_report/Test_players/<player-id>/report.html`

4. **回归测试（必须完成）**
   - 在项目根目录运行：
     - `python3 -m style_report.scripts.run_full_report --player-id testYuYaochen --max-games 2`
   - 检查：
     - `style_report/Test_players/testYuYaochen/analysis_text.json` 中是否出现 markdown 表格（带 `|` 和 `---`）。
     - `report.html` 中是否包含这些表格（即使还是 markdown 形式也没关系，先保证结构正确）。
   - 如果表格没有生成，优先检查：
     - 是否正确读了新的 `.md` 文件；
     - 是否在 LLM 调用前把 `player_profile` JSON 拼接到 prompt 末尾；
     - 环境变量 `OPENAI_API_KEY` / `STYLE_REPORT_MODEL` 是否OK。

> 约束：
> - 不改现有目录名和文件名，不动 `current GM metrics/`。
> - 任意单个 `.py` 文件保持在 400 行以下，必要时拆成多个模块。
> - 不做前端页面，只做命令行一键生成报告（Phase 1）。
