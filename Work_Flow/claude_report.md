# Task: Visual redesign of style report (report.html)

Owner: Claude  
Reviewer: Codex  
Repo: `chess_report_page`  

## 0. Context

We already have:

- A full analysis pipeline in `style_report/scripts/run_full_report.py` that:
  - Builds `player_profile` from PGNs;
  - Calls the LLM using prompts in `style_report/prompts/overall_section.md` and `style_report/prompts/model_section.md`;
  - Writes `style_report/Test_players/<player_id>/analysis_text.json` and `report.html`.
- A basic HTML template in `style_report/report_base.html`.
- A FastAPI wrapper in `style_report/api.py` exposing `POST /report`.
- LLM outputs are **markdown** (including tables). Currently we mostly do a newline → `<br />` replacement, so tables do not render as HTML.

Goal of this task:  
Make the generated report **visually pleasant and readable**:

1. Left-side progress / section navigation bar.
2. Proper markdown → HTML rendering for tables and headings.
3. GM photo block (Top 3 similarity GMs).
4. Overall spacing / fonts / basic styling.

Focus on **static report HTML** first (what `run_full_report.py` writes).  
Future Next.js / full UI integration is **out of scope** for this task.

---

## 1. Markdown → HTML with real tables

### Objective

Replace the current “newline to `<br />`” hack with a proper markdown renderer so that:

- Tables with `|` and `---` are rendered as `<table>`.
- `#`, `##`, `###` become `<h1>`, `<h2>`, `<h3>` etc.
- Bullet lists render correctly.

We already installed `markdown` via pip.

### Requirements

- Use Python `markdown` library with at least the `tables` and `fenced_code` extensions.
- Do **not** strip or escape content; just convert markdown to safe HTML.
- Keep a small helper function so future code can reuse it.

### Implementation hints

File: `style_report/scripts/run_full_report.py`

1. Add:

   ```python
   import markdown
Create a helper:

python
Copy code
def _render_markdown(md_text: str) -> str:
    if not md_text:
        return ""
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"]
    )
In generate_report(...):

Right now we likely set:

python
Copy code
overall_html = some_string_replace(overall_md)
model_html = some_string_replace(model_md)
Replace with:

python
Copy code
overall_html = _render_markdown(overall_md)
model_html = _render_markdown(model_md)
When writing report.html, feed the rendered HTML into the template placeholders:

{{OVERALL_SECTION_HTML}} ← overall_html

{{MODEL_SECTION_HTML}} ← model_html

Keep _ensure_markdown_table safeguard if needed, but make sure the final HTML contains <table> instead of raw | lines.

2. Layout redesign: left navigation + main content
Objective
Give report.html a clean two-column layout:

Left column: narrow, sticky navigation / progress bar with section anchors.

Right column: main scrollable content (overall analysis + tag family analysis).

Layout must look good on a laptop (width ~1300px) and still readable on smaller width.

Requirements
No external CSS frameworks; use simple, self-contained CSS in <style> inside report_base.html.

Use flexbox for layout (no floats).

Left nav should contain links to main sections:

“Overview” (top)

“I. Personal Performance”

“II. Overall Synthesis”

“III. Tag Family Analysis”

“IV. Opening Choices”

“V. Strengths & Training”

“VI. How to Play Against This Player”

Clicking a nav item scrolls to the corresponding section (<a href="#section-overview"> etc.).

Left nav should visually highlight the current section (simple JS, no heavy library).

Implementation hints
File: style_report/report_base.html

Wrap the whole inner body in a container:

html
Copy code
<div class="page">
  <aside class="sidebar">
    <!-- nav -->
  </aside>
  <main class="content">
    <!-- title + sections -->
  </main>
</div>
Basic CSS (sketch):

css
Copy code
body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f5f5f7;
  color: #111827;
}

.page {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 240px;
  padding: 24px 16px;
  background: #111827;
  color: #e5e7eb;
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100vh;
  box-sizing: border-box;
}

.sidebar-title {
  font-weight: 700;
  font-size: 18px;
  margin-bottom: 16px;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  margin-bottom: 8px;
}

.nav-link {
  display: block;
  padding: 6px 10px;
  border-radius: 8px;
  text-decoration: none;
  color: inherit;
  font-size: 14px;
}

.nav-link.active {
  background: #2563eb;
  color: #f9fafb;
}

.content {
  flex: 1;
  padding: 32px 48px;
  max-width: 960px;
  margin: 0 auto;
}

h1, h2, h3 {
  color: #111827;
  line-height: 1.2;
}

h1 {
  font-size: 32px;
  margin-bottom: 12px;
}

h2 {
  font-size: 24px;
  margin-top: 32px;
  margin-bottom: 12px;
}

h3 {
  font-size: 18px;
  margin-top: 20px;
  margin-bottom: 8px;
}

p {
  line-height: 1.6;
  margin: 6px 0 10px;
}
Placeholders for content:

html
Copy code
<h1 id="section-overview">Style Report: {{PLAYER_ID}}</h1>

<section id="section-personal">
  {{OVERALL_SECTION_HTML}}
</section>

<section id="section-tag-families">
  {{MODEL_SECTION_HTML}}
</section>
(If needed, you can split OVERALL_SECTION_HTML into multiple <section> tags; for now we assume h2 IDs are enough.)

Add a small JS snippet at the bottom to highlight current section:

html
Copy code
<script>
const sections = document.querySelectorAll("section[id]");
const links = document.querySelectorAll(".nav-link");

const map = {};
links.forEach(link => {
  const target = link.getAttribute("href").slice(1);
  map[target] = link;
});

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.id;
      links.forEach(l => l.classList.remove("active"));
      if (map[id]) map[id].classList.add("active");
    }
  });
}, { rootMargin: "-40% 0px -50% 0px", threshold: 0.1 });

sections.forEach(sec => observer.observe(sec));
</script>
3. GM photo block
Objective
Add a visually nice GM portrait strip near the top of the report showing the “Top 3 similar GMs” from the analysis.

For now, we can hard-code a small mapping from GM names to image paths; later this can be wired to real assets.

Requirements
Display 3 circular avatar images with name + similarity score (e.g. Kasparov 71%).

If an image is missing, show a neutral placeholder (e.g. gray circle with initials).

This block should sit at the top of the main content, under the main title.

Implementation hints
Decide where similarity info comes from:

If player_profile.json already includes something like:

json
Copy code
"closest_gm_top3": [
  {"name": "Kasparov", "similarity": 0.71},
  {"name": "Aronian", "similarity": 0.74},
  {"name": "Petrosian", "similarity": 0.66}
]
then:

Extend generate_report(...) to pass this into the template context as GM_TOP3_JSON or render it directly into HTML.

If not present, for now we can leave placeholders in HTML (e.g. “GM #1, GM #2, GM #3”).

HTML snippet in report_base.html under <h1>:

html
Copy code
<div class="gm-strip">
  <!-- Example layout, actual names injected by generate_report -->
  <div class="gm-card">
    <div class="gm-avatar gm-kasparov"></div>
    <div class="gm-name">Kasparov</div>
    <div class="gm-score">71% similarity</div>
  </div>
  <div class="gm-card">
    <div class="gm-avatar gm-aronian"></div>
    <div class="gm-name">Aronian</div>
    <div class="gm-score">74% similarity</div>
  </div>
  <div class="gm-card">
    <div class="gm-avatar gm-petrosian"></div>
    <div class="gm-name">Petrosian</div>
    <div class="gm-score">66% similarity</div>
  </div>
</div>
CSS:

css
Copy code
.gm-strip {
  display: flex;
  gap: 16px;
  margin: 16px 0 24px;
  flex-wrap: wrap;
}

.gm-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 10px 14px;
  box-shadow: 0 8px 16px rgba(15, 23, 42, 0.08);
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 180px;
}

.gm-avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background-size: cover;
  background-position: center;
  background-color: #e5e7eb;
}

.gm-name {
  font-weight: 600;
  font-size: 14px;
}

.gm-score {
  font-size: 12px;
  color: #6b7280;
}

/* Example background-image mapping; these can be local files under /static */
.gm-kasparov {
  background-image: url("static/gm_kasparov.jpg");
}
.gm-aronian {
  background-image: url("static/gm_aronian.jpg");
}
.gm-petrosian {
  background-image: url("static/gm_petrosian.jpg");
}
Later we can replace the hard-coded cards with a small loop rendered in Python (string formatting) using actual JSON values.

4. Table styling
Objective
Make all <table> elements coming from markdown look clean and readable.

Requirements
Add borders and zebra-striping.

Ensure tables do not overflow horizontally (allow scroll on small screens).

Use a consistent small font size, but not too tiny.

Implementation hints
In report_base.html CSS:

css
Copy code
.table-wrapper {
  width: 100%;
  overflow-x: auto;
  margin: 12px 0 16px;
}

table {
  border-collapse: collapse;
  width: 100%;
  font-size: 13px;
  background: #ffffff;
}

th, td {
  padding: 6px 8px;
  border: 1px solid #e5e7eb;
  text-align: left;
}

th {
  background: #f3f4f6;
  font-weight: 600;
}

tr:nth-child(even) td {
  background: #f9fafb;
}
Since markdown will output <table> directly, we can wrap them post-processing if needed:

Simple option: let tables render naked and rely on the global table CSS.

Better option: after rendering markdown, surround all <table> with <div class="table-wrapper">. This can be done by a simple regex or by a small BeautifulSoup pass; not mandatory for v1.

5. Typography & spacing polish
Objective
Make the text blocks visually comfortable:

Add max line width.

Increase line height.

Ensure headings and paragraphs have consistent margins.

Requirements
Already partly covered in the CSS above (.content max-width, p line-height).

Also style ul, ol, and li.

Example:

css
Copy code
ul, ol {
  padding-left: 20px;
  margin: 8px 0 12px;
}

li {
  margin: 2px 0;
}
6. Acceptance criteria
The task is considered done when:

Running:

bash
Copy code
python3 -m style_report.scripts.run_full_report --player-id testYuYaochen --max-games 2
regenerates:

style_report/Test_players/testYuYaochen/report.html with:

Real HTML tables (no raw markdown pipes).

Sidebar nav present and working (clicking scrolls; active highlight changes while scrolling).

GM strip visible under the title (can be placeholder names/images if JSON data is not wired yet).

Opening report.html in a browser:

Left sidebar is fixed; main text scrolls smoothly.

Headings and paragraphs are clearly separated and easy to read.

Tables are readable, with borders and zebra rows.

All changes are limited to:

style_report/scripts/run_full_report.py

style_report/report_base.html

(Optionally) small CSS/JS additions only in this template.

Codex review passes (no obvious code smells; layout is simple and robust; no huge inline JS complexity).

