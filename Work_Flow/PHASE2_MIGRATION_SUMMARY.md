# Phase2 Migration Summary

## 已完成的修改

### 1. HTML 模板和导航 ✅
文件: `style_report/templates/report_base.html`

- 更新section编号从罗马数字(I-VI)改为阿拉伯数字(1-6)
- 添加可折叠导航，包含所有子章节
- 实现展开/折叠功能，带有箭头指示器
- 导航结构：
  - **1. Performance Profile**: 1.1-1.10 子节
  - **2. Style Parameters**: 2.1-2.9 子节
  - **3. Overall Synthesis**: 无子节
  - **4. Opening Repertoire**: 4.1-4.8 子节
  - **5. Training Recommendations**: 5.1-5.3 子节
  - **6. Opponent Preparation**: 6.1-6.6 子节

### 2. CSS 样式 ✅
文件: `style_report/assets/report.css`

- 添加`.nav-section`, `.parent-link`, `.nav-subsections`, `.sidebar-sublink`样式
- 添加箭头指示器(▶)，展开时旋转
- 平滑过渡效果
- 子节链接独特样式

### 3. LLM Prompts 重构

#### 已完成 ✅:
1. **performance_profile.md** (Section 1) - 1.1-1.10结构
2. **model_section.md** (Section 2) - 2.1-2.9结构，添加2.9 Style Synthesis
3. **overall_synthesis.md** (Section 3) - 整合section 1和2
4. **opening_repertoire.md** (Section 4) - 4.1-4.8结构，包括4.3.1/4.3.2子节
5. **training_recommendations.md** (Section 5) - 5.1-5.3结构，带有5.x.x子编号
6. **opponent_preparation.md** (Section 6) - 6.1-6.6结构

#### Style Parameters子prompts (2.1-2.9) 需要统一更新:

**已更新** ✅:
- `style_maneuver.md` → 2.1 Maneuver
- `style_initiative.md` → 2.5 Initiative
- `style_structural.md` → 2.7 Structural Play

**需要更新的文件**（使用相同模式）:
- `style_prophylaxis.md` → 需要改为 **2.2 Prophylaxis**
- `style_semantic_control.md` → 需要改为 **2.3 Semantic Control**
- `style_cod.md` → 需要改为 **2.4 Control Over Dynamics**
- `style_tension.md` → 需要改为 **2.6 Tension Management**
- `style_sacrifice.md` → 需要改为 **2.8 Sacrificial Play**
- `style_exchanges_forced.md` → 需要改为 **2.9 Style Synthesis**（这个特殊，需要整合所有tag families）

## 每个Style Prompt需要的标准结构

每个style子prompt文件都必须包含：

### 1. 标题和上下文声明
```markdown
# 2.X [Topic Name]

**CONTEXT**: You are writing subsection **2.X [Topic]** within the larger Section 2 (Style Parameters) of a comprehensive chess report. This is NOT a standalone report.

**CRITICAL STRUCTURAL REQUIREMENTS**:
- You MUST start with heading: `### 2.X [Topic]`
- Use ONLY `####` level headings for sub-points (no `###` except the main title)
- Do NOT create independent section numbers like "1.", "2.", "3." - you are already inside section 2.X
- All content will be inserted into the main report under "2. Style Parameters"
```

### 2. 输出结构模板
```markdown
## Output Structure

Your output MUST follow this exact structure:

\```markdown
### 2.X [Topic]

[Brief introduction paragraph]

**Table:**

| Tag name | Count | Ratio | Top GM Avg | Interpretation |
|---|---|---|---|---|
| ... |

#### [Subsection 1 Name]

[Analysis content]

#### [Subsection 2 Name]

[Analysis content]

#### Style Implications

[Connect to broader patterns]
\```
```

### 3. 分析指南
```markdown
## Analysis Guidelines

- Write in a professional, coaching tone
- Focus on **what the [topic] patterns reveal about playing style**
- Always compare with GM reference data from the JSON
- Do NOT invent section numbers or create mini 1-X structure
- This is a subsection of Section 2, not a standalone report
```

## 导航锚点链接对应关系

### Performance Profile (Section 1)
- `#perf-winrate` → 1.1 Win rate
- `#perf-accuracy` → 1.2 Accuracy
- `#perf-advantage` → 1.3 Advantage conversion
- `#perf-defensive` → 1.4 Defensive conversion
- `#perf-volatility` → 1.5 Volatility/trajectory
- `#perf-engine` → 1.6 Engine decision quality
- `#perf-tactical` → 1.7 Tactical conversion
- `#perf-exchanges` → 1.8 Knight/bishop exchanges
- `#perf-forced` → 1.9 Forced moves
- `#perf-positions` → 1.10 Winning/losing position handling

### Style Parameters (Section 2)
- `#style-maneuver` → 2.1 Maneuver
- `#style-prophylaxis` → 2.2 Prophylaxis
- `#style-semantic_control` → 2.3 Semantic control
- `#style-control_over_dynamics` → 2.4 Control over dynamics
- `#style-initiative` → 2.5 Initiative
- `#style-tension` → 2.6 Tension management
- `#style-structural` → 2.7 Structural play
- `#style-sacrifice` → 2.8 Sacrificial play
- `#style-exchanges_forced` → 2.9 Style synthesis

**重要**: 这些锚点ID由report_builder.py中的`render_style_parameters`函数生成，格式为`style-{key}`，其中key来自STYLE_PROMPTS列表。

### Opening Repertoire (Section 4)
- `#opening-white-table` → 4.1 White openings table
- `#opening-black-table` → 4.2 Black openings
- `#opening-main-repertoires` → 4.3 Main repertoires
- `#opening-secondary` → 4.4 Secondary weapons
- `#opening-depth` → 4.5 Theoretical depth
- `#opening-style` → 4.6 Connection to style
- `#opening-performance` → 4.7 Underperforming vs shining
- `#opening-takeaways` → 4.8 Practical takeaways

### Training Recommendations (Section 5)
- `#training-priorities` → 5.1 Key priorities
- `#training-study` → 5.2 Study methods
- `#training-habits` → 5.3 Practical habits

### Opponent Preparation (Section 6)
- `#opponent-white` → 6.1 Opening choices vs white
- `#opponent-black` → 6.2 Opening choices vs black
- `#opponent-middlegame` → 6.3 Middlegame strategies
- `#opponent-endgame` → 6.4 Endgame strategies
- `#opponent-psychology` → 6.5 Psychology / risk
- `#opponent-gameplan` → 6.6 Summary game plan

## 仍需处理的问题

### 1. LLM输出的锚点ID
现在导航链接指向的ID（如`#perf-winrate`, `#style-maneuver`等）需要LLM在markdown中生成对应的标题ID。

**两种解决方案**:

**方案A (推荐)**: 在prompt中明确要求LLM使用特定ID
```markdown
#### 1.1 Win rate {#perf-winrate}
```

**方案B**: 在Python中post-process markdown，自动添加ID
修改`report_builder.py`中的`_render_markdown`函数，为heading自动添加ID。

### 2. Style Parameters的2.9特殊处理
`style_exchanges_forced.md`需要重命名或重新设计为"2.9 Style Synthesis"，整合前面2.1-2.8的所有tag families。

这个不同于其他子节，它应该：
- 综合分析所有tag families的交互
- 识别风格维度的主导模式
- 寻找一致性或矛盾
- 与最接近的2-3位GM比较
- 保持简洁(2-3段)，因为会被Section 3 (Overall Synthesis)补充

## 下一步行动

1. **批量更新剩余style prompts** (prophylaxis, semantic_control, cod, tension, sacrifice)
   - 添加上下文声明
   - 统一输出结构
   - 删除独立编号(1., 2., 3.)
   - 改用####级别标题

2. **重新设计style_exchanges_forced.md为2.9 Style Synthesis**
   - 不再是单独的"exchanges + forced moves"分析
   - 变成整合2.1-2.8的综合小结

3. **解决锚点ID问题**
   - 选择方案A或B
   - 确保导航点击能跳转到正确位置

4. **测试完整流程**
   - 生成一份完整报告
   - 检查所有导航链接
   - 验证展开/折叠功能
   - 确认LLM输出正确的section编号

## 关键原则

1. **所有LLM prompts必须知道自己的位置**: "你在写2.5 Initiative，这是Section 2的一个子节"
2. **禁止自创编号**: 不允许在2.x下面再出现1., 2., 3.这样的独立编号系统
3. **统一heading层级**:
   - Section标题: ### (由template提供)
   - Subsection标题: ### 2.X Topic (由LLM生成)
   - Sub-subsection标题: #### (由LLM生成)
4. **导航和内容必须同步**: 导航栏的编号必须与LLM生成的内容编号一致
5. **锚点ID必须可跳转**: 每个导航链接都要能正确跳转到对应内容

## 文件清单

### 已修改 ✅
- `style_report/templates/report_base.html`
- `style_report/assets/report.css`
- `style_report/prompts/performance_profile.md`
- `style_report/prompts/model_section.md`
- `style_report/prompts/overall_synthesis.md`
- `style_report/prompts/opening_repertoire.md`
- `style_report/prompts/training_recommendations.md`
- `style_report/prompts/opponent_preparation.md`
- `style_report/prompts/style_maneuver.md`
- `style_report/prompts/style_initiative.md`
- `style_report/prompts/style_structural.md`

### 待修改
- `style_report/prompts/style_prophylaxis.md`
- `style_report/prompts/style_semantic_control.md`
- `style_report/prompts/style_cod.md`
- `style_report/prompts/style_tension.md`
- `style_report/prompts/style_sacrifice.md`
- `style_report/prompts/style_exchanges_forced.md` (需要重新设计)

### 可能需要修改
- `style_report/scripts/report_builder.py` (如果选择方案B处理锚点ID)
