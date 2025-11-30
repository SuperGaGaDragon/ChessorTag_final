claude_report_fix.md

## Goal

Refine the **visual layout and table rendering** of the chess-player report so that:

1. The HTML report shows **exactly six main sections** in this order:
   1. Personal Performance Evaluation  
   2. Skill Metrics  
   3. Style Parameters (Tag Analysis)  
   4. Overall Synthesis  
   5. Opening Choices  
   6. Training Advice & Opponent Preparation  

2. The **left sidebar navigation** uses these six section titles and scrolls smoothly to each section.

3. All LLM-generated content (including tables) is **already provided by Codex** — you must **not** change prompts, metrics, or data, only how they are rendered and laid out.

4. All **Markdown tables** in the LLM output are properly rendered as HTML `<table>` elements (with borders, header row, zebra striping, etc.), not as plain text.

5. The whole page looks like a **professional analytic report**: clear hierarchy, good spacing, readable typography, responsive on mobile.

> Important: Do **NOT** change tag definitions, data pipelines, or LLM prompts. Only adjust HTML templates, CSS, and minimal JS for scrolling / active section.

---

## Global Layout

### 1. Overall page structure

Use a two-column layout:

- **Left sidebar** (fixed, ~240px width)
  - Dark background (e.g. `#111827`)
  - Contains report title and the six section links (see below)
  - Stays fixed while the right content scrolls
- **Right content area**
  - Max-width ~960px, centered
  - Scrollable
  - Contains everything the user reads: GM cards, charts, all six sections, tables, etc.

A rough HTML structure:

```html
<div class="report-root">
  <aside class="report-sidebar">
    <!-- logo / title -->
    <!-- navigation links -->
  </aside>
  <main class="report-main">
    <!-- header + GM cards -->
    <!-- sections 1–6 -->
  </main>
</div>
### 2. Sidebar navigation

In the sidebar, create a vertical navigation list:

- **Title at top:** e.g. "Chess Style Report"

Below that six links, in this exact order and text:

1. I. Personal Performance
2. II. Skill Metrics
3. III. Style Parameters
4. IV. Overall Synthesis
5. V. Opening Choices
6. VI. Training & Opponent Prep

Each link should scroll smoothly to a section with a matching id, for example:

```html
<a href="#section1-performance">I. Personal Performance</a>
<a href="#section2-skills">II. Skill Metrics</a>
<a href="#section3-style">III. Style Parameters</a>
<a href="#section4-overall">IV. Overall Synthesis</a>
<a href="#section5-openings">V. Opening Choices</a>
<a href="#section6-training">VI. Training & Opponent Prep</a>
```

Use `IntersectionObserver` (or similar) so that the active section gets a highlight class in the sidebar when the user scrolls.

---

## Header & GM Similarity Block

At the top of `<main>` (before Section 1), add a compact header area:

### 1. Report title + player name

- Large heading, e.g. `h1`: "Chess Style Report: [Player Name]"
- Subheading line with basic info: rating range, time control, number of games, etc. (data is already provided by Codex – just show it cleanly)

### 2. GM similarity cards

- A horizontal row of 3 cards showing the top-3 similar GMs
- Each card shows:
  - GM avatar (placeholder if real image not yet wired)
  - GM name (e.g. "Tigran Petrosian")
  - Similarity score (e.g. "Similarity: 82%")
- Use white cards, rounded corners, subtle shadow, good padding

Example structure:

```html
<section class="gm-strip">
  <div class="gm-card">
    <div class="gm-avatar"></div>
    <div class="gm-name">Tigran Petrosian</div>
    <div class="gm-score">Similarity: 82%</div>
  </div>
  <!-- two more cards -->
</section>
```

---

## Section Layout (1–6)

Each section should be visually separated as a "card" with:

- `h2` section heading (Roman numeral + title)
- Optional `h3` sub-headings
- Content block (text + tables + charts)

---

### Section 1: Personal Performance Evaluation

`<section id="section1-performance">`

**Content:**

- High-level win/draw/loss statistics, split by White / Black
- Average opponent rating

**Display these via:**

- A short explanatory paragraph
- One or two tables (White / Black rows, columns like Win%, Loss%, Draw%, Avg Opponent Elo)
- Consider a small inline chart (if Codex already generates an image path) — otherwise, keep as tables

**Visual:**

- Present White and Black side-by-side tables or stacked with clear labels.

---

### Section 2: Skill Metrics

`<section id="section2-skills">`

**Content:**

Accuracy system table(s):

- Overall accuracy
- Opening / middlegame / endgame accuracy
- With-queen / without-queen accuracy
- Advantage conversion / defense success statistics
- Game volatility metrics (e.g. stable vs swingy games)

**Visual:**

- Show a primary metrics table at the top.
- Below, place the six-dimension radar chart image (if available) with a caption like "Skill Radar (accuracy / advantage handling / defense / volatility / …)".
- Brief paragraph explaining how to read the radar.

---

### Section 3: Style Parameters (Tag Analysis)

`<section id="section3-style">`

This is the longest and most detailed section. It is fed by tag-based LLM analysis from Codex; your job is to make it readable.

**Layout suggestion:**

1. Start with a short intro paragraph: "This section analyzes the player's style using maneuver, prophylaxis, control, initiative, tension, structural and sacrifice tags, plus exchanges and forced moves."

2. Then create clear sub-blocks (cards) for each tag family, for example:
   - Maneuvering
   - Prophylaxis
   - Semantic control
   - Control over dynamics
   - Initiative
   - Tension management
   - Structural play
   - Sacrificial play
   - Exchanges / forced moves

**Each sub-block:**

- Title as `h3` (e.g. 3.1 Maneuvering)
- Immediately below: a table with at least columns:
  - Tag name
  - Player count / ratio
  - Top GM ratio
  - Interpretation (from Codex)
- Below the table: 1–3 paragraphs of dense LLM analysis text.

**Important:** Codex will already output these tables in Markdown. You MUST ensure Markdown tables render correctly (see "Table Rendering" section).

---

### Section 4: Overall Synthesis

`<section id="section4-overall">`

**Position in layout:** it MUST appear after Section 3 and before Section 5.

**Content:**

- An integrated GM-style psychological portrait, 5–9 paragraphs
- Cross-domain analysis combining:
  - Skill Metrics
  - Style Parameters
  - Accuracy / advantage conversion / defense
- Identification of:
  - Central style identity
  - Closest GM cluster and top-3 similar GMs (with similarity percentages)
  - Internal contradictions and unique traits

**Visual:**

- Full-width text, no tables here
- Use subsections with `h3` like:
  - 4.1 Central Style Identity
  - 4.2 Closest GM Cluster
  - 4.3 Internal Contradictions & Unique Traits

---

### Section 5: Opening Choices

`<section id="section5-openings">`

**Content:**

Opening stats split by White and Black

For each:

- Opening move sequence (e.g. 1.e4 e5 2.Nf3 Nc6 3.Bb5)
- ECO name or "Unknown"
- Win rate
- Average accuracy in that opening

**Visual:**

Two tables:

1. "When playing White"
2. "When playing Black"

Each table with columns:

- Opening line
- Opening name (from Lichess ECO)
- Win rate
- Average accuracy

---

### Section 6: Training Advice & Opponent Preparation

`<section id="section6-training">`

**Content (two sub-parts, both are LLM text):**

1. **Training Plan for the Player**
   - Summarizes strengths & weaknesses
   - Suggests what to practice and how (e.g. specific structures, typical mistakes, decision patterns)

2. **How to Prepare Against This Player**
   - Advice for an opponent: which openings to aim for or avoid, which types of positions are uncomfortable for the player, typical mistakes to target, game-plan recommendations

**Visual:**

Two sub-blocks with `h3` headings:

- 6.1 Training Plan
- 6.2 Opponent Preparation

Each is a well-formatted multi-paragraph text block.

---

## Table Rendering (Very Important)

### Problem

Currently, some Markdown tables in the LLM output are not rendered as proper HTML tables – they appear as plain text with `|` characters.

### Requirements

Every Markdown table generated by Codex (including LLM sections) must appear as:

```html
<table class="report-table">
  <thead>...</thead>
  <tbody>...</tbody>
</table>
```

The visual style for `.report-table` should include:

- 1px border on table and cells
- Header row with slightly darker background
- Zebra striping on body rows
- Small but readable font (13px)
- Padding inside cells
- Horizontal scroll wrapper for narrow screens

**Do not modify Codex LLM prompts or data; fix the rendering pipeline / template only.**

### Implementation hints (what you may change)

If `run_full_report.py` already converts markdown to HTML, make sure the template uses it as:

```html
<div class="section-body markdown-body">
  {{ section_html | safe }}
</div>
```

i.e. do not escape the HTML again.

If the template currently prints raw markdown, you may:

- Call the Python `markdown` library in the template or earlier stage with the tables extension enabled.
- Ensure no extra escaping is added.

In any case, you must end up with actual `<table>` elements in the final HTML so CSS can style them.

Add a CSS block such as:

```css
.report-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.report-table th,
.report-table td {
  border: 1px solid #e5e7eb;
  padding: 6px 8px;
  text-align: left;
}
.report-table thead {
  background-color: #f3f4f6;
}
.report-table tbody tr:nth-child(odd) {
  background-color: #fafafa;
}
```

Wrap tables inside a scroll container on mobile:

```html
<div class="table-wrapper">
  <!-- table here -->
</div>
```

with CSS

```css
.table-wrapper {
  width: 100%;
  overflow-x: auto;
}
```

---

## Typography & Spacing

Use a modern system font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

- **h1:** 32px, bold
- **h2:** 24px, semibold, margin-top ~40px
- **h3:** 18px, medium, margin-top ~24px
- **Paragraphs:** 15–16px, line-height 1.6
- **Section cards:** white background, soft shadow, 16–24px padding, 16px border-radius

---

## Constraints Recap

### Claude MUST NOT:

- Change Codex prompts, section content, or tag logic
- Reorder the six main sections (only the defined order is allowed)
- Alter the metrics or data
- Remove or simplify any LLM content

### Claude MUST:

- Implement the layout and styling described above
- Fix Markdown table rendering
- Keep everything in English for the user-facing text
- Ensure the report looks professional and consistent across all players

---

## Summary

This document provides comprehensive instructions for refining the visual layout and table rendering of the chess player report. The focus is entirely on front-end presentation—HTML templates, CSS styling, and minimal JavaScript for smooth scrolling and active section highlighting.

**Key deliverables:**

1. A professional two-column layout with fixed sidebar navigation
2. Six well-structured sections in the specified order
3. Proper rendering of all Markdown tables as styled HTML tables
4. Clean, readable typography and spacing
5. Responsive design that works on mobile devices

**Remember:** Do not modify any Codex prompts, tag definitions, metrics calculations, or LLM-generated content. Only adjust how the existing data is displayed and styled.