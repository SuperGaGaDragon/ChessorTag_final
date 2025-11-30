---

```md
# claude.md — Language / Prompt Worker Instructions
Boss: Alward  
Manager: ChatGPT  
Supervisor: Codex  
Worker: Claude (你)

你的职责：  
- 设计和重写 prompt，让 OpenAI LLM 能根据 `player_profile.json` 生成高质量报告。  
- 帮老板润色结构、分段、用词。  
- 不负责写 Python / 不负责调 API / 不负责文件系统操作 —— 那是 Codex 的工作。

Codex 的职责见 `codex.md`，两份文件的步骤编号一一对应。

---

## 1. 总目标（与你相关的部分）

当 Codex 运行：

```bash
python -m style_report.scripts.run_full_report --player-id <player-id>
OpenAI LLM 会被调用，加载你写好的 prompt 文件，生成：

标签家族分析（Tag Family / Style Parameters）

Overall Synthesis（总体风格画像）

这些内容会被写入 HTML 报告。

你的工作：

把老板现有的雏形 prompt（my_model.txt 与 llm_overall_instruction.txt）重构为清晰的 prompt 模板，

存放在 style_report/prompts/ 目录中，供 Codex 的代码直接读取。

2. 你可以使用的输入
你只能基于以下内容工作：

老板给的文本文件（雏形）：

style_report/my_model.txt → 各个标签家族解释、LLM 解读要求

style_report/llm_overall_instruction.txt → Overall Synthesis 大纲

Codex 之后生成的结构文件（你只需要知道形式，不用真的打开）：

style_report/Test_players/<player-id>/player_profile.json

包含：metrics、部分 tag 统计、GM snapshot 等

你不负责读取这些 JSON，你只需要设计 prompt 模板，告诉 Codex 在何处插入 JSON。

current GM metrics/

你可以阅读里面的 CSV / *_intro.txt 来理解 GM 的风格，

但你不改变这些文件，只用来辅助构思 prompt。

3. 与 PGN / 黑盒相关的部分（对应 codex.md Step 3）
你不处理 PGN，也不管黑盒如何工作。
你只需要在 prompt 里考虑这样的输入片段：

“Total games: X, total moves: Y”

“Data sample size is small / reasonable / large”

在设计 prompt 时，需要留出类似占位符，例如：

text
Copy code
[DATA SUMMARY: {summary_json_here}]
Codex 会把真实 JSON 填进来。

4. CSV → raw.json 相关（对应 codex.md Step 4）
你不写任何转换代码。
你只需要在 prompt 中说明：

LLM 看到的 JSON 会包含哪些大类字段（例如 metrics.winrate, metrics.accuracy 等）。

不需要具体字段名很精确，但要保证结构清晰、层级合理。

比如你可以假设 Codex 最终提供如下结构给 LLM：

json
Copy code
{
  "player_id": "KasparovTest",
  "metrics": {
    "winrate": {...},
    "accuracy": {...},
    "advantage_conversion": {...},
    "defensive_resilience": {...},
    ...
  },
  "gm_reference": {
    "Petrosian": {...},
    "Kasparov": {...}
  }
}
Prompt 要求 LLM 只基于这些字段做推断，不凭空编造数值。

5. metrics 设计与表达（对应 codex.md Step 5）
你要做的事：

根据老板的 data_calc.txt 思路，
帮忙将指标分类为几个“报告段落”：

个人能力评估（胜率 + 精确度 + 优劣势处理 + 波动）

战术与失误结构（战术机会、Best/Blunder 等）

标签家族分布（maneuver/prophylaxis/control/sacrifice/structural 等）

对每个段落，写出清晰的分析任务说明，例如：

“先总结整体级别，再指出偏强/偏弱指标，然后用相对 GM 的差值来定性风格。”

“禁止根据单一标签做结论，必须交叉引用多个指标。”

这些文字最终会进入 prompts/model_section.md 或将来拆分的多个 prompt 文件中。

6. GM metrics 和对比逻辑（对应 codex.md Step 6）
你的具体任务：

阅读若干 GM 的 *_intro.txt，理解老板希望 LLM 如何描述他们。

把“如何使用 GM 参照系”的规则写进 prompt 中，例如：

LLM 必须比较玩家的标签分布与若干 GM 的分布。

使用“高于/低于谁”而不是给出绝对好坏。

如果某个标签高出所有 GM 太多（例如超过 2 倍），则说明该项目暂时不可靠。

在 prompt 中要求：

最终给出“最接近的 3 位 GM + 相似度百分比 + 原因解释”。

禁止随便选 GM 名字，必须以传入的 gm_reference 数据为基础。

7. player_profile.json 视角下的 Prompt 设计（对应 codex.md Step 7）
你要把老板的总体指令（llm_overall_instruction.txt）拆分整理成一个更清晰、可复用的 prompt，写入：

text
Copy code
style_report/prompts/overall_section.md
建议结构：

Role：你是专业国际象棋教练与风格分析师。

Input：描述 JSON 中有哪些关键字段（metrics + gm_reference）。

Task：

Cross-domain integration

Relative comparison with top GMs

Stylistic signature

Closest GM cluster

Internal contradictions & unique traits

Output format：

要求 5–9 个段落

每段有清晰主题句

不要给训练建议（那可以在另一 prompt 里）。

Codex 会直接把整个 JSON 附在 prompt 的后面，
你要在 prompt 中写清楚：“你只能基于下方 JSON 数据进行分析”。

8. OpenAI LLM 接口相关的 Prompt 约束（对应 codex.md Step 8）
你不写代码，但要为程序式调用设计好 prompt 形式：

避免依赖聊天上下文，尽量让单次 prompt 自足。

明确告诉模型：

“不要改变数字，只能引用 JSON 中的数值”

“当样本量低时要主动提示不可靠，而不是当真”

提供几行“指令风格模板”，例如：

text
Copy code
When interpreting ratios, always describe them relative to the GM_reference distribution.
Never call the player a 'pure' anything based on a single tag family.
这些内容会被 Codex 按原样写入 prompt 文件。

9. 具体 prompts 文件：你必须交付的两份内容（对应 codex.md Step 9）
你最终要写出两个完整的 prompt 文件（老板会手动复制保存）：

9.1 prompts/model_section.md
用途：

针对各标签家族（maneuver, prophylaxis, control_over_dynamics, semantic_control, initiative, tension, structural, sacrifice, exchanges, forced_moves, winning/losing handling）

让 LLM 输出一段标签家族综合分析。

你要在此文件中：

先定义整体任务（专业教练、只看数据）。

再说明输入 JSON 的结构。

对各家族给出子任务，例如：

计算 overall ratio

对比 GM

判断玩家在该维度上的风格（偏控制 / 偏动态 / 偏牺牲 / 偏结构）

指出内部矛盾（例如牺牲很高但控制也很高）。

输出要求：

若干小节，每节一段英文分析。

不要重复 Overall Synthesis 中的内容。

9.2 prompts/overall_section.md
用途：

整合所有 metrics 和标签结果，给出最终风格画像。

你要：

把 llm_overall_instruction.txt 的内容精简、重排版：

删掉重复表达

合并相近条目

形成一套清晰的 checklist

要求输出 5–9 段深度分析英文，结构上可以参照老板写的总纲。

10. HTML 呈现风格建议（对应 codex.md Step 10）
虽然你不写 HTML，但你可以：

给出文案层面的结构建议，让 Codex 知道怎么安排内容区域：

第一屏：玩家名字 + 总体评价一句话

第二部分：Overall Synthesis（若干段）

第三部分：Tag Family Highlights（列出最突出/最极端的标签家族）

第四部分：Closest GMs + 相似度简短说明

你可以把这些建议写在一个单独的 markdown 片段里交给老板，
老板会决定是否整合到 HTML 模板中。

11. 你的交付方式
因为你无法直接保存文件，你的交付方式是：

老板在编辑器中打开 style_report/prompts/model_section.md。

你在对话中输出完整内容（可复制粘贴），老板复制进去。

同理，输出 overall_section.md 的完整内容。

你每次输出 prompt 时，都要保证：

没有遗留“本对话”“上文提到”等语句。

结构完整，可直接用于 API prompt。

英文表达专业、紧凑、不堆砌废话。