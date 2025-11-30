# codex.md — Engineering Supervisor Instructions
Boss: Alward  
Manager: ChatGPT  
Supervisor: Codex (you)  
Worker: Claude

你的职责：  
- 写代码、搭脚本、连黑盒、接 OpenAI API、生成 HTML 文件。  
- 不负责写长篇分析、不负责润色 prompt、不负责文学表达。

Claude 的职责在 `claude.md` 中，你和他按同样的步骤编号协作。

---

## 0. 硬性约束（不能违反）

1. 目录结构（已存在的部分不可改名、不可删除）：

   ```text
   chess_report_page/
     chess_imitator/                # 黑盒，只允许极少量必要改动
     style_report/
       metrics/
       Test_players/
       current GM metrics/          # 只读，只能读取，不准写入修改
       llm_overall_instruction.txt
       my_model.txt
       codex.md
       claude.md

current GM metrics/ 只读：你只能读 CSV / txt / jpg，不能生成/覆盖文件。

Phase 1 的目标是：命令行一键生成报告，暂时不做网站前端。

1. Phase 1 总目标（你要实现的最终效果）

实现脚本：

cd chess_report_page
python -m style_report.scripts.run_full_report --player-id Kasparov


完成后，自动得到：

style_report/Test_players/Kasparov/report.html
style_report/Test_players/Kasparov/player_profile.json
style_report/Test_players/Kasparov/analysis_log.json (可选)


数据来源：

输入 PGN：style_report/Test_players/Kasparov/*.pgn

黑盒分析：chess_imitator 的 player_batch 脚本

OpenAI LLM：由你写的 llm_client.py 调用

2. 目录和模块搭建（不动现有文件夹）

在 style_report/ 下，如果不存在则新建：

style_report/
  prompts/
  templates/
  scripts/
  metrics/__init__.py


约定文件（你负责创建）：

prompts/model_section.md（Claude 负责写内容）

prompts/overall_section.md（Claude 负责写内容）

templates/report_base.html

scripts/run_full_report.py

metrics/calc.py

llm_client.py

不要移动或改名已有的 metrics/、Test_players/、current GM metrics/。

新规矩：任何目录名、文件名禁止出现首尾空格；如发现视为 bug，需重构或更名修正。

3. 从 PGN → 黑盒 CSV（Step 3 对应 claude.md 的 Step 3）
3.1 PGN 输入约定

每个测试棋手一个文件夹：

style_report/Test_players/<player-id>/
  games.pgn              # 你或老板放进去的 pgn（可能是多盘）

3.2 调用 chess_imitator 的 player_batch

在 scripts/run_full_report.py 中：

从命令行参数 --player-id 读取 <player-id>。

复制 style_report/Test_players/<player-id>/games.pgn 到：

chess_imitator/rule_tagger_lichessbot/Test_players/<player-id>.pgn


如有必要可创建 Test_players 子目录。

不改动黑盒脚本，只是准备它需要的 input-dir / 文件名。

使用 subprocess 调用 player_batch，例如（示意）：

cmd = [
    "python3",
    "rule_tagger_lichessbot/scripts/player_batch.py",
    "--player", player_id,
    "--input-dir", "rule_tagger_lichessbot/Test_players",
    "--output-prefix", f"{player_id}_report"
]


player_batch 会在 chess_imitator/rule_tagger_lichessbot/reports/ 下生成一个 CSV，
你要确定命名规则（例如 <player-id>_report.csv），并返回其路径。

4. CSV → raw.json（Step 4 对应 claude.md Step 4）

在 style_report/scripts/run_full_report.py 中：

将黑盒生成的 CSV 复制到：

style_report/Test_players/<player-id>/analysis.csv


调用一个工具函数（你在 metrics/csv_to_raw.py 内实现），将 analysis.csv 转为结构化 JSON：

style_report/Test_players/<player-id>/raw.json


建议结构：

{
  "player_id": "<player-id>",
  "games": [
    {
      "game_id": "...",
      "color": "white",
      "result": "win",
      "moves": [
        {
          "ply": 1,
          "uci": "g1f3",
          "cp_eval": 12.0,
          "best_cp_eval": 25.0,
          "tags": ["neutral_maneuver", "opening_maneuver"]
        }
      ]
    }
  ]
}


保留足够信息给 metrics 使用：eval、best eval、tags、result、对手等级分等。

5. metrics 计算（Step 5 对应 claude.md Step 5）

参考 data_calc.txt 中已有的指标说明（老板会维护，通过 Claude 重构成文档）：

你在 metrics/calc.py 中实现：

def compute_metrics(raw_data: dict) -> dict:
    """
    输入 raw.json 的内容，输出 metrics 字典。
    """


metrics 至少包含：

胜率（白/黑/总）

精确度（overall / opening / middlegame / endgame / queenless / queenful）

优势处理（+1/+3/+5/+7：出现局面数 + 最终胜/和/负比例）

劣势防守（-1/-3/-5/-7）

对局波动类型（smooth crush / smooth crushed / small swings / big swings / high-precision draws）

Best / inaccuracy / mistake / blunder 比例

Tactical：机会总数 / 抓住数 / 错过数

Exchanges & forced moves 的基本统计（数量 + 比例）

Winning / Losing position handling 的次数与比例

你将结果写入：

style_report/Test_players/<player-id>/metrics.json


结构示例：

{
  "winrate": {...},
  "accuracy": {...},
  "advantage_conversion": {...},
  "defensive_resilience": {...},
  "volatility": {...},
  "move_quality": {...},
  "tactics": {...},
  "exchange_family": {...},
  "forced_moves": {...},
  "winning_losing_handling": {...}
}

6. GM metrics 读取（只读）（Step 6 对应 claude.md Step 6）

你只能“读取”，不能“修改”：

style_report/current GM metrics/<GM name>/
  <GM>.csv
  <GM>_intro.txt
  <GM>.jpg


在 run_full_report.py 中：

读取几个核心 GM（例如 Petrosian、Kasparov、Karpov、Carlsen、Tal ……）的 CSV。

将它们简单归一化为一个结构：

gm_reference = {
  "Petrosian": {...},
  "Kasparov": {...},
  ...
}


可将 gm_reference 写入：

style_report/Test_players/<player-id>/gm_snapshot.json


仅用于给 LLM 做对比，不做任何写回 GM 文件的动作。

7. player_profile.json 整合（Step 7 对应 claude.md Step 7）

在 run_full_report.py 中，合并：

raw.json（可以只保留摘要信息，如总局数、总步数）

metrics.json

gm_snapshot.json（如果你生成了）

生成：

style_report/Test_players/<player-id>/player_profile.json


建议结构：

{
  "player_id": "<player-id>",
  "meta": {
    "games_count": 26,
    "moves_count": 1071
  },
  "metrics": { ... },
  "gm_reference": { ... }
}


这份 JSON 是 Claude 和 OpenAI LLM 的唯一主要输入。

8. OpenAI LLM 接口（Step 8 对应 claude.md Step 8）

你在 style_report/llm_client.py 中实现：

import os
from openai import OpenAI

MODEL_NAME = os.getenv("STYLE_REPORT_MODEL", "gpt-5.1")

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(prompt: str) -> str:
    resp = _client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a professional chess coach and style analyst."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()


注意：

API key 从 OPENAI_API_KEY 环境变量读取。

模型名从 STYLE_REPORT_MODEL 环境变量读取，可自定义。

你不会在运行时“找 Claude”；Claude 的作用是帮老板写 prompt 文件（见 claude.md）。

9. 调用 prompts 生成文本（Step 9 对应 claude.md Step 9）

Claude 会根据老板的原始 txt（my_model.txt 和 llm_overall_instruction.txt）重写成：

style_report/prompts/model_section.md
style_report/prompts/overall_section.md


你在 run_full_report.py 中：

读取 player_profile.json。

将其中需要的字段（metrics + gm_reference）转成一小块 JSON 字符串，拼接到 prompt 后面。

分别调用：

model_section.md → 生成标签家族分析文本

overall_section.md → 生成 Overall Synthesis 文本

将 LLM 输出先写入一个中间文件，方便调试：

style_report/Test_players/<player-id>/analysis_text.json


示例结构：

{
  "model_section": "...",
  "overall_section": "..."
}

10. HTML 模板渲染（Step 10 对应 claude.md Step 10）

在 templates/report_base.html 中定义一个简单模板，例如：

<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>Chess Style Report - {{PLAYER_ID}}</title>
</head>
<body>
  <h1>Style Report: {{PLAYER_ID}}</h1>

  <h2>Overall Synthesis</h2>
  <div>{{OVERALL_SECTION_HTML}}</div>

  <h2>Tag Family Analysis</h2>
  <div>{{MODEL_SECTION_HTML}}</div>

  <!-- 之后可以继续扩展：metrics 表格、GM 对比、图片等 -->
</body>
</html>


在 run_full_report.py 中：

读取 report_base.html。

把 analysis_text.json 中的字符串进行最简单的 HTML 处理（例如 \n\n 换成 <p>），

替换占位符 {{PLAYER_ID}}、{{OVERALL_SECTION_HTML}}、{{MODEL_SECTION_HTML}}。

输出到：

style_report/Test_players/<player-id>/report.html

11. 一键脚本总流程（你必须严格遵守）

run_full_report.py 主流程伪代码：

def main(player_id: str):
    # 1. 准备路径
    # 2. 从 Test_players 拷贝 games.pgn → chess_imitator/Test_players
    # 3. subprocess 调用 player_batch，得到 CSV
    # 4. 复制 CSV 到 style_report/Test_players/<player-id>/analysis.csv
    # 5. CSV → raw.json
    raw_data = load_raw(...)
    # 6. 计算 metrics → metrics.json
    metrics = compute_metrics(raw_data)
    # 7. 读取 GM metrics → gm_snapshot.json
    gm_snapshot = load_gm_reference(...)
    # 8. 组装 player_profile.json
    player_profile = build_profile(...)
    # 9. 调用 OpenAI LLM 读 prompts → analysis_text.json
    analysis_text = generate_text(player_profile)
    # 10. 渲染 HTML → report.html
    render_html(player_id, player_profile, analysis_text)
    
## 12. Code size constraint

- No single Python file in style_report/ is allowed to exceed **400 lines** (including blank lines and comments).
- If any file grows close to 400 lines, you MUST:
  - Extract helper functions into a new module (e.g. metrics/helpers_accuracy.py, scripts/utils_io.py, etc.), or
  - Split the logic into smaller, focused files instead of adding more code to the same file.
- Long text (prompts, HTML templates, etc.) must live in separate resource files (under style_report/prompts/ and style_report/templates/) rather than as giant multi-line strings inside .py files.
- During any future refactor, you are responsible for keeping all existing files under 400 lines.


Phase 1 完成后再谈网站前端集成。
在你完成每一步之前，不要提前做后面的事。
所有与 prompt 内容相关的工作交给 Claude，见 claude.md。
