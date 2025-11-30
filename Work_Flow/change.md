# change.md — Phase 2: 从"LLM写整页"改为"前端模板 + LLM填空"方案

## 0. 背景 / Problem

当前部分 prompts 仍然假设：

- LLM 会 **输出整段 HTML / 整个 section 的结构**
- LLM 自己生成标题、编号、表格等

这与 Phase 2 的目标冲突：

- 报告的 **HTML 结构应完全由前端控制**（`report_base.html` + `report.css`）
- LLM 只负责在指定位置输出 **解释性文字或短 block**，而不是随意改版面
- 将来要保证不同棋手的报告在视觉结构上 **100% 一致**

因此需要一次性改造：
从 **"LLM = 报告作者"** → **"LLM = 报告模板里的填空机"**。

---

## 1. 目标 / Target Design

### 核心原则

1. **所有表格、标题、布局均在 HTML 中预先写死**
   - 包括列名、行结构、heading 层级等
   - LLM 不再负责任何 `<table>` / `<h3>` / `<h4>` 的生成

2. **LLM 只在预定义的插槽（slots）中写内容**
   - 例如：分析段落、简短总结、教练评语
   - 通过 `<div id="xxx-llm-slot">` 注入

3. **数据型内容由程序计算，不交给 LLM**
   - 胜率、accuracy、tag 次数等
   - 后端算完，通过 JSON → 前端填表格

4. Prompt 从 "写整节" 改为 "写一个 slot 的文字"
   - 不再要求完整 1.1 / 2.3 等 section
   - 每条 prompt 精确对应一个 slot 或一个小 group

---

## 2. 前端改动（HTML / CSS）

### 2.1 固定表格结构

在 `report_base.html` 中：

- 为每个 **数据型 section** 写固定表格：
  - 列名固定
  - 行数固定
  - `id` 用于填充数据

示例（1.1 Win rate）：

```html
<table class="report-table">
  <thead>
    <tr>
      <th></th>
      <th>Win</th>
      <th>Loss</th>
      <th>Draw</th>
      <th>Avg Opponent Elo</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>As White</td>
      <td id="white-win-rate"></td>
      <td id="white-loss-rate"></td>
      <td id="white-draw-rate"></td>
      <td id="white-elo"></td>
    </tr>
    <tr>
      <td>As Black</td>
      <td id="black-win-rate"></td>
      <td id="black-loss-rate"></td>
      <td id="black-draw-rate"></td>
      <td id="black-elo"></td>
    </tr>
  </tbody>
</table>
```

### 2.2 为 LLM 输出预留固定插槽

在表格或标题后面定义：

```html
<div id="winrate-llm-comment" class="llm-slot"></div>
```

**规范：**

- 所有 LLM 插槽 class 使用统一命名：`.llm-slot`
- id 采用 `section-X-Y-[topic]-llm` 或类似规范，便于后端映射
- 例：`section-1-1-winrate-llm`, `section-2-4-cod-llm-main`, etc.

---

## 3. 后端 / Orchestrator 改动

### 3.1 输出结构：固定数据 + LLM slots

后端对每一位棋手生成一个统一 JSON，例如：

```json
{
  "fixed_data": {
    "winrate": {
      "white": { "win": 58, "loss": 22, "draw": 20, "elo": 2130 },
      "black": { "win": 51, "loss": 27, "draw": 22, "elo": 2155 }
    },
    "accuracy": {
      "overall": 0.89,
      "opening": 0.92,
      "middlegame": 0.87,
      "endgame": 0.90
    }
    // ...
  },
  "llm_slots": {
    "section-1-1-winrate-llm": "<p>…</p>",
    "section-1-2-accuracy-llm": "<p>…</p>",
    "section-2-1-maneuver-llm": "<p>…</p>"
    // ...
  }
}
```

**前端逻辑：**

- `fixed_data` → 直接用 JS 填进已有表格
- `llm_slots` → 按 id 写入对应 `.innerHTML`

### 3.2 LLM 调用逻辑

一次报告生成可以：

1. **串行依次请求各 slot**（简单但慢）
2. **或批量请求，让 LLM 返回多个 slot 文本**（推荐）

调用结束后，将 LLM 输出 map 为 `llm_slots` 字典，以 `slot_id` 为 key。

---

## 4. LLM Prompt 改造方案

### 4.1 核心思想

每个 prompt 对应一个或一组 slots，而不是整节

**Prompt 输入包括：**

- 原始统计数据 / 比较数据（玩家 vs 同龄 vs GM）
- 上下文描述（你在写哪一节的哪一个插槽）
- 输出风格 & 长度要求

**Prompt 输出：**

- 纯文本 / 轻量 HTML snippet
- 禁止输出标题、表格、编号

---

## 5. Codex 执行说明（给 Codex 的工作指令）

下面这段文字可以直接作为 Codex/Claude 的"system + user 指令"，用于改代码和 prompts。

```text
You are Codex, acting as the implementation engineer for the Phase 2 chess report system.

GOAL:
- Refactor the report generation pipeline from "LLM writes entire sections (HTML + headings + tables)" into a "template-first, slot-filling" architecture.
- The front-end (report_base.html + report.css) owns ALL layout, headings, and table structures.
- The LLM is only responsible for generating text snippets that fill predefined slots.

CONSTRAINTS:
1. Do NOT let the LLM generate headings (no <h1>, <h2>, <h3>, etc.) or tables in the new prompts.
2. All tables, columns, headings, and section numbers belong to the HTML templates, NOT the LLM.
3. Each LLM call must be scoped to a clearly defined slot (or a small group of slots).
4. Output should be plain text or very light HTML (e.g., <p>, <strong>, <em>, <ul>/<li> when explicitly allowed).
5. The Phase 2 numbering (1.1–1.10, 2.1–2.9, 3, 4.1–4.8, 5.1–5.3, 6.1–6.6) must be respected by structure:
   - HTML controls titles and IDs.
   - LLM never invents its own "1., 2., 3." numbered substructure.

TASKS:

(1) FRONT-END TEMPLATE ALIGNMENT
- For each report subsection that currently expects LLM to output full HTML:
  - Create static HTML structures in report_base.html:
    - Tables with fixed rows/columns.
    - Section titles using existing Phase 2 hierarchy (h3 for 2.X, h4 for internal grouping).
  - Immediately after each data block, define a <div> that will be filled by LLM, e.g.:
    <div id="section-1-1-winrate-llm" class="llm-slot"></div>
- Ensure all slot IDs follow a consistent pattern like:
  section-[major]-[minor]-[topic]-llm

(2) DATA VS LLM BOUNDARY
- For each subsection, categorize content into:
  (A) Pure data (win rates, accuracy numbers, tag counts, etc.).
  (B) Interpretive commentary (coach-style explanation/summary).
- Implement logic so that:
  - (A) is computed fully in Python and returned in a "fixed_data" JSON object.
  - (B) is produced via LLM and stored in a "llm_slots" mapping keyed by slot ID.

(3) API / JSON SCHEMA
- Define / standardize a JSON response structure for the report endpoint:
  {
    "fixed_data": {...},
    "llm_slots": {
      "section-1-1-winrate-llm": "<p>...</p>",
      "section-2-4-cod-llm": "<p>...</p>"
    }
  }
- Update the front-end script to:
  - Fill tables and numeric spans from fixed_data.
  - Insert LLM snippets into the corresponding slot <div> by ID.

(4) PROMPT REFACTORING
- For each main report section file:
  - performance_profile.md
  - model_section.md (style parameters)
  - overall_synthesis.md
  - opening_repertoire.md
  - training_recommendations.md
  - opponent_preparation.md
  and each style_* prompt (style_maneuver, style_prophylaxis, style_cod, etc.):

  Replace "write the entire section as HTML" instructions with slot-based instructions.

  Example transformation for 1.1 Win Rate:

  OLD (conceptual):
    "You are writing Section 1.1 Win Rate.
     Generate a full section with headings, tables, and explanations."

  NEW:
    System/context:
      "You are writing the commentary snippet for Section 1.1 Win Rate in the Phase 2 chess report.
       The HTML template already contains all headings and tables.
       You MUST NOT generate any headings or tables.
       Your output will be injected into a <div id='section-1-1-winrate-llm'>."

    User content:
      - Provide all relevant stats (white/black win/loss/draw, average opponent rating, small GM comparison).
      - Ask for a 120–180 word analytic paragraph that:
        * Explains what this win rate profile implies about the player.
        * Highlights major contrasts (e.g., as White vs as Black, vs peers, vs GM baseline).
        * Uses a professional coach tone.

    Explicit output constraints:
      - "Output a single <p>...</p> block.
       Do not include any headings, tables, bullet lists, or numbering."

- Apply the same pattern to all other subsections:
  - Each slot has:
    * Clear context: which section and what slot.
    * Data payload: stats/tag frequencies/GM references.
    * Output spec: length, tone, HTML allowed or not.

(5) VALIDATION
- After refactoring, ensure:
  - The report renders correctly even if LLM is disabled (only fixed_data is shown).
  - With LLM enabled, all text appears only inside .llm-slot containers.
  - No duplicated headings, no extra section numbers, and no tables from LLM output.
- Add quick checks (e.g., simple string search or test) to fail if LLM output contains:
  "<h1", "<h2", "<h3", "<table", "<thead", "<tbody".

END OF INSTRUCTIONS.
```

---

## 6. 迁移顺序建议（给你自己看的）

1. **选一个子节做样板**（建议：1.1 Win rate）

2. **在 `report_base.html` 固定：**
   - 表格结构
   - 一个 `llm-slot` div

3. **在后端：**
   - 为 1.1 生成 `fixed_data.winrate`
   - 为 1.1 生成 `llm_slots["section-1-1-winrate-llm"]`

4. **修改 `performance_profile.md` 中关于 1.1 的 prompt** → 使用 slot 型写法

5. **跑通一个棋手完整的 1.1 渲染**

6. **把这套 pattern 复制到其他子节**（1.2, 1.3… 2.X…）

这样整套 Phase 2 从"LLM 改版面"升级为"LLM 填空式解释引擎"，安全、可控、UI 可长期维护。
