# codex_report_fix.md

## Goal

Restore and upgrade the **full chess-player research report** so that:

1. The HTML report has **exactly six top-level sections**, with a left-side navigation that matches them 1:1 and in the *exact* order specified below.
2. Every section is **rich, detailed, and entirely in English**.
3. All narrative text is written by the LLM **only from the tag data and numeric metrics that the pipeline already computes** (no external knowledge, no PGN re-parsing).
4. The LLM **always compares the player’s data against top-GM reference profiles** (Petrosian, Karpov, Kramnik, Kasparov, Tal, Shirov, Topalov, Carlsen, Aronian, etc.).
5. The current simplified / placeholder outputs are removed; the report returns to a long, dense, coach-level explanation.

Do **not** change the tagging pipeline itself. Only adjust code that:

- Aggregates metrics for the report,
- Calls the LLM with prompts,
- Builds the HTML, navigation, and section layout.

---

## Required section layout (HTML & navigation)

The report must have these **six sections**, in this **exact order**:

1. **I. Performance Profile**  
2. **II. Style Parameters (Tag Families)**  
3. **III. Overall Synthesis**  
4. **IV. Opening Repertoire**  
5. **V. Training Recommendations**  
6. **VI. Opponent Preparation**

Tasks:

- Update the report-builder script (e.g. `pipeline.py` or `run_full_report.py`) so the left-hand navigation and top-level `<h2>` headings match these six titles and this order.
- Make sure each section has a stable HTML anchor ID (e.g. `#performance-profile`, `#style-parameters`, etc.) so links and future extensions are easy.
- Remove or rename any old sections like “Tag Family Analysis”, “Overall Synthesis” etc. that conflict with this exact structure.

---

## Section I – Performance Profile (metrics + LLM)

This section corresponds to “个人能力评估”.

### Tables / metrics

You probably already compute most of these; ensure the HTML tables exist and are passed into the prompt:

1. **Win–loss–draw by color + opponent rating**
   - White: win %, loss %, draw %, average opponent Elo  
   - Black: win %, loss %, draw %, average opponent Elo  

2. **Accuracy system**
   - For player / same-age peers / top GMs:  
     - Overall accuracy  
     - Opening accuracy  
     - Middlegame accuracy  
     - Endgame accuracy  
     - Accuracy in queenless positions  
     - Accuracy in positions with queens  

3. **Advantage conversion (handling better positions)**
   - For White and Black separately:  
     - For games where eval reached +1, final W/L/D percentages  
     - For games where eval reached +3, final W/L/D  
     - For games where eval reached +5, final W/L/D  
     - For games where eval reached +7, final W/L/D  

4. **Defensive resilience (handling worse positions)**
   - Same structure as above, but for eval −1, −3, −5, −7.  

5. **Game volatility / game flow**
   - For White and Black: percentages of games that are  
     - Fast crushing wins (one-sided from early on)  
     - Fast collapses (one-sided losses)  
     - Low-swing games (a couple of swings between ±1)  
     - Swingy games (a couple of swings between ±2)  
     - Very high-volatility games (multiple swings beyond ±2)  
     - High-precision draws (no swing beyond about ±0.8)  

6. **Engine decision quality by color**
   - For White and Black: counts / ratios of  
     - Best moves (engine top-2)  
     - Inaccuracies (drop ≥ 0.5 pawns)  
     - Mistakes (drop ≥ 1 pawn)  
     - Blunders (drop ≥ 3 pawns)  

7. **Tactical conversion**
   - For White and Black:  
     - Fraction of tactical chances converted  
     - Fraction of tactical chances missed  

8. **Special parameters: exchanges, forced moves, winning/losing positions**
   - Knight/Bishop exchange quality:  
     - Accurate exchange, inaccurate exchange, bad exchange (counts + ratios + top GM ratios).  
   - Forced moves: count + ratio compared to top GMs.  
   - Winning / losing position handling tags (if available):  
     - “Winning position handling”, “Losing position handling” counts + ratios + top GM ratios.

### New LLM prompt for Performance Profile

Create or update a prompt template for this section (e.g. `prompts/performance_profile.md`) with text at least as detailed as the following (you can adapt variable names):

> You are a professional international chess coach.  
> You are given a player’s **performance metrics** and **accuracy statistics**, plus comparable data for same-age peers and for top grandmasters.
>
> Use **only these tables and numbers**; do not invent new data or refer to external games.
>
> Your tasks:
>
> 1. **Win–loss–draw by color**  
>    - Describe how the player’s results with White and with Black compare to peers and top GMs.  
>    - Comment on color imbalances (e.g. “performs much better with White than Black”).  
>    - Relate the result pattern to style (e.g. sharp vs solid).
>
> 2. **Accuracy system**  
>    - Interpret overall accuracy and phase-specific accuracy (opening, middlegame, endgame, queenless vs queen positions).  
>    - Explicitly compare each value with same-age peers and top GMs (“higher than peers but lower than top GMs”, etc.).  
>    - Identify which phases are clear strengths and which are liabilities.
>
> 3. **Advantage conversion and defensive resilience**  
>    - Use the +1/+3/+5/+7 and −1/−3/−5/−7 tables to evaluate how well the player converts better positions and defends worse ones.  
>    - Highlight asymmetries (e.g. “excellent at converting +3 positions but shaky at +1; resilient at −1 but collapses quickly at −3 and beyond”).  
>    - Always compare to top-GM patterns from the reference dataset.
>
> 4. **Game volatility**  
>    - Characterize the typical volatility of the player’s games: controlled, swingy, chaotic, etc.  
>    - Connect volatility with risk attitude and time-management style (where possible).
>
> 5. **Engine move quality and tactics**  
>    - Interpret the ratios of best moves, inaccuracies, mistakes, and blunders for each color.  
>    - Combine them with tactical conversion / missed-tactic rates to assess calculation and alertness.  
>    - Explain how these numbers differ from both peers and top GMs.
>
> 6. **Special parameters**  
>    - Use exchange-quality metrics to explain how well the player judges bishop–knight exchanges.  
>    - Use forced-move frequency to comment on how often the player steers games into forcing sequences vs. allowing the opponent more freedom.  
>    - If winning/losing position tags exist, interpret them as an additional check on advantage conversion and defensive resilience.
>
> 7. **Summary of strengths and weaknesses**  
>    - Synthesize all the above into a concise list of **performance strengths** and **performance weaknesses**.  
>    - This summary must be factual and grounded in comparisons with top-GM reference distributions.  
>    - Do not give training advice here; just describe what is strong and what is weak.
>
> Write in dense, professional English (2–4 paragraphs plus a bullet list of strengths/weaknesses).  
> Do **not** use generic clichés; always tie claims to the specific numbers and comparisons.

Wire the generated markdown into the Performance Profile section of the HTML.

---

## Section II – Style Parameters (Tag Families)

This is “风格参数 / 标签详细分析”.  
You already have tag families such as maneuver, prophylaxis, semantic control, control-over-dynamics, initiative, tension, structural play, sacrifices, exchanges, forced moves, etc.

### Data requirements

For each family, you should already have tables like:

- `Tag name | Player count | Player ratio | Top GM ratio | Interpretation`
- Possibly pre-written “Interpretation” strings in code or config.

Ensure the LLM gets **all** of these tables plus any aggregate ratios you compute (e.g. overall maneuver ratio, overall sacrifice ratio).

### LLM prompts for major families

Create separate prompt templates per family (e.g. `prompts/style_maneuver.md`, `prompts/style_prophylaxis.md`, etc.).  
Each template must be **at least as detailed** as the Chinese specification, and it must always:

- Compute and interpret **overall ratio** (“how often does this family occur?”),
- Analyze **internal structure** (“how are tags distributed inside the family?”),
- Compare the player to **closest top GMs** in that family profile,
- Extract as many **fine-grained style traits** as possible.

Below are example instructions you can embed/expand in each template (you can keep them almost verbatim):

#### Maneuver family

> You are a professional chess coach.  
> You receive maneuver-tag tables with counts and ratios for:
> - constructive_maneuver  
> - constructive_maneuver_prepare  
> - neutral_maneuver  
> - misplaced_maneuver  
> - opening_maneuver  
> plus an **overall maneuver ratio** and top-GM reference ratios.
>
> Tasks:
> 1. Compute the overall maneuver ratio (constructive + prepare + neutral + misplaced over total moves). Explain what this says about how maneuver-oriented the player is compared with top GMs.  
> 2. Analyze the distribution of constructive / prepare / neutral / misplaced. Describe the player’s maneuver style: conservative, precise, slow-improvement, mechanical, improvisational, etc.  
> 3. Use misplaced_maneuver ratio to evaluate maneuver quality. Compare it with peers and top GMs.  
> 4. Identify the two top grandmasters whose maneuver profiles are closest; compare similarities and differences in plain language.  
> 5. Summarize what these maneuver patterns imply for the player’s positional understanding, patience, and long-term planning.
>
> Do not draw conclusions from a single tag alone; always interpret the full distribution and its comparison to top GMs.

#### Prophylaxis family

Do the same for direct / latent / meaningless / failed prophylaxis with explicit instructions:

- Compute overall prophylaxis ratio.
- Interpret direct vs latent balance (active vs subtle prevention).
- Use meaningless and failed rates as proxies for “over-prophylaxis” and misjudged threats.
- Compare with Petrosian, Carlsen, Kramnik, Aronian, etc.

#### Semantic control (`control_*`) family

Use the English spec you already have (simplify / plan_kill / freeze_bind / blockade / file_seal / king_safety_shell / space_clamp / regroup / slowdown, plus overall semantic control ratio).  
Prompt must emphasize:

- How often the player chooses slow control vs sharp dynamics.  
- Which types of control they prefer (simplifications, binds, space clamps, safety shells, etc.).  
- Comparison with Karpov / Petrosian / Kramnik / Carlsen / Aronian.

#### Control-Over-Dynamics (`cod_*`) family

Use your Chinese spec: emphasize that these tags arise **when the player chooses control over a concrete dynamic alternative**.

Prompt must:

- Compute overall `control_over_dynamics` ratio.  
- Interpret sub-tags (cod_file_seal, cod_freeze_bind, cod_king_safety, cod_regroup, cod_plan_kill, cod_blockade_passed, cod_simplify, cod_space_clamp, cod_slow_down).  
- Compare with at least two reference GMs; explicitly avoid labeling the player “control-style” purely from high ratios—always compare with others.

#### Initiative / tension / structure / sacrifice

For each:

- Initiative: balance of initiative_attempt vs deferred_initiative vs premature_attack etc.  
- Tension: how often and how accurately the player maintains or resolves pawn tension.  
- Structural: structural_integrity vs structural_compromise_dynamic vs structural_compromise_static.  
- Sacrifice: overall sacrifice ratio + breakdown (tactical vs positional vs speculative vs desperate, etc.).

Each template must:

- Quantify overall willingness to take risk / enter complications.  
- Connect distributions to recognizable style types (risk-averse controller, practical gambler, sacrificial attacker, etc.).  
- Always compare with at least two top GMs whose distributions are numerically closest.

#### Exchanges / forced moves / winning vs losing position tags

Add a small prompt that:

- Explains what high/low frequencies of knight-bishop exchanges say about judgment of minor pieces.  
- Uses forced-move frequency to infer how often the player drives the opponent into narrow choices.  
- Uses winning/losing handling tags as a *style* signal, not just a performance metric.

### HTML structure for Section II

- Keep Section II as a **collection of subsections** (Maneuver, Prophylaxis, Control, Control-Over-Dynamics, Initiative, Tension, Structure, Sacrifices, Exchanges & Forced Moves).  
- Each subsection: one or more tables + LLM narrative block.

---

## Section III – Overall Synthesis (after Style, before Opening)

This is the **integrated style portrait**.  
It must appear **after** Section II (Style Parameters) and **before** Section IV (Opening Repertoire) in both HTML and navigation.

Use (or extend) the detailed English spec you already have:

- Cross-domain integration (tempos, risk, structure, initiative, tension, prophylaxis, control, sacrifice, advantage conversion, defense, volatility).  
- Relative comparison with top-GM clusters.  
- Identify **closest GM cluster** and **top 3 most similar GMs with similarity scores**.  
- Highlight internal contradictions and unique traits.  
- 5–9 dense paragraphs in professional English.  
- No training advice here.

Make sure the report-builder passes **all tag-family summaries and key ratios** into this prompt.

---

## Section IV – Opening Repertoire

Tasks:

- Use the Lichess ECO / opening database that you already wired in to map each game’s opening to:  
  - ECO code,  
  - Opening name,  
  - Possibly sub-variation.
- Build separate tables for White and Black:

  - **White:** `First moves / repertoires | Opening name | Win rate | Average accuracy | Number of games`  
  - **Black:** same.

- If an opening is not found in the database, label it as “Unknown” and group these under a single “Unknown / offbeat systems” line.

LLM prompt for this section must:

- Identify main White repertoires and Black repertoires.  
- Comment on **result performance** and **average accuracy** for each repertoire.  
- Comment on **depth of theoretical knowledge** (approximate) based on accuracy and stability of early moves.  
- Highlight **secondary weapons** and **experimental sidelines**.  
- Always relate openings back to style themes from Section II.

---

## Section V – Training Recommendations

This section uses **all the metrics and all the style analysis** to propose a **personal training plan** for the player.

Prompt requirements:

- Use weaknesses from Performance Profile + Style Parameters.  
- Suggest concrete topics: e.g. “conversion of +1 edges”, “defense of −2 positions”, “improving structural judgment in dynamic sacrifices”, “reducing meaningless prophylaxis”, etc.  
- Structure output (for example) into:
  - 3–5 key priorities  
  - Suggested study methods (model games, specific types of exercises)  
  - Practical habits during games (time management, risk management, move-selection discipline)  
- Must be **fully grounded in the previously mentioned data**; no generic advice not traceable to a metric.

---

## Section VI – Opponent Preparation

This is the mirror of Section V but from an opponent’s point of view.

Prompt:

- Use the same data to answer: *“If I am preparing to play against this player, what should I try to get on the board?”*  
- Cover:
  - Opening choices that statistically give them trouble (low win rate or low accuracy).  
  - Types of positions they handle poorly (e.g. high-tension, sharp tactical, static structural squeezes, etc.).  
  - Phases / score ranges (e.g. they overpress equal positions, they defend badly at −2, etc.).  
  - Psychological tendencies inferred from stats (risk avoidance, time trouble patterns if available, etc.).  
- Output should be structured (e.g. “1. Opening choices vs White”, “2. Opening choices vs Black”, “3. Middlegame strategies”, “4. Endgame strategies”).

---

## Implementation notes

1. **Prompt templates**  
   - Store the long prompts above as markdown files under a clear directory (e.g. `prompts/performance_profile.md`, `prompts/style_maneuver.md`, `prompts/overall_synthesis.md`, etc.).  
   - Ensure the LLM client reads from these files and passes the relevant tables/metrics as context.

2. **No placeholders**  
   - Remove any logic that auto-wraps non-table text in a tiny placeholder table when the LLM call fails.  
   - Instead, surface a clear error message in the HTML (e.g. “LLM analysis unavailable; check API key”) so we can see when something broke.

3. **Comparisons with top GMs**  
   - Make sure each prompt explicitly receives access to top-GM reference ratios by tag family, plus a list of reference GM clusters, so the LLM can fulfill the “higher than X, lower than Y” requirement.

4. **Language**  
   - All user-facing HTML must be in **English**.  
   - Internal comments in code can stay in any language, but prompts should be fully English.

Once these changes are done, running the existing report command (e.g.):

```bash
python3 pipeline.py sample.pgn \
  --stockfish /usr/local/bin/stockfish \
  --depth 6 \
  --out reports/sample_report.html \
  --llm
