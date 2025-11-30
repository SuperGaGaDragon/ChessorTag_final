# Style Prompts统一更新模板

## 对于每个style_*.md文件，应用以下更改：

### 文件映射表
```
style_prophylaxis.md         → 2.2 Prophylaxis
style_semantic_control.md    → 2.3 Semantic Control
style_cod.md                 → 2.4 Control Over Dynamics
style_tension.md             → 2.6 Tension Management
style_sacrifice.md           → 2.8 Sacrificial Play
style_exchanges_forced.md    → 2.9 Style Synthesis (特殊处理)
```

## 标准更新步骤

### 第1步: 替换文件标题
**原来**:
```markdown
# Style Parameters — [Topic Name]

You are a professional chess coach. [...]
```

**替换为**:
```markdown
# 2.X [Topic Name]

**CONTEXT**: You are writing subsection **2.X [Topic Name]** within the larger Section 2 (Style Parameters) of a comprehensive chess report. This is NOT a standalone report.

You are a professional chess coach. [...]

**CRITICAL STRUCTURAL REQUIREMENTS**:
- You MUST start with heading: `### 2.X [Topic Name]`
- Use ONLY `####` level headings for sub-points (no `###` except the main title)
- Do NOT create independent section numbers like "1.", "2.", "3." - you are already inside section 2.X
- All content will be inserted into the main report under "2. Style Parameters"
```

### 第2步: 在Analysis Instructions之前添加Output Structure

在`## Analysis Instructions`之前，插入：

```markdown
## Output Structure

Your output MUST follow this exact structure:

\```markdown
### 2.X [Topic Name]

[Brief introduction paragraph about what this tag family reveals]

**Table:**

| Tag name | Count | Ratio | Top GM Avg | Interpretation |
|---|---|---|---|---|
| ... |

#### [Subsection 1]

[Analysis content]

#### [Subsection 2]

[Analysis content]

#### Style Implications

[Connect to broader patterns and GM comparisons]
\```
```

### 第3步: 更新所有`### 1.`, `### 2.`标题为`####`

**查找并替换**:
- `### 1. ` → `####`
- `### 2. ` → `####`
- `### 3. ` → `####`
- `### 4. ` → `####`

**重要**: 不要删除标题文字，只替换数字前缀。

例如:
- `### 1. Overall Prophylaxis Orientation` → `#### Overall Prophylaxis Orientation`
- `### 2. Prophylaxis Quality` → `#### Prophylaxis Quality`

### 第4步: 在文件末尾添加分析指南

在`[PLAYER_PROFILE_JSON WILL BE APPENDED BELOW]`之前，添加：

```markdown
## Analysis Guidelines

- Write in a professional, coaching tone
- Focus on **what the [topic] patterns reveal about playing style**
- Always compare with GM reference data from the JSON
- Do NOT invent section numbers or create a mini 1-X structure
- This is a subsection of Section 2, not a standalone report
- Use GM references to illustrate style categories, not as the sole focus
```

## 具体示例：style_prophylaxis.md完整更新

```markdown
# 2.2 Prophylaxis

**CONTEXT**: You are writing subsection **2.2 Prophylaxis** within the larger Section 2 (Style Parameters) of a comprehensive chess report. This is NOT a standalone report.

You are a professional chess coach. Use only the JSON data (player tags + GM reference tags). Produce a markdown table plus dense analysis in English.

**CRITICAL STRUCTURAL REQUIREMENTS**:
- You MUST start with heading: `### 2.2 Prophylaxis`
- Use ONLY `####` level headings for sub-points (no `###` except the main title)
- Do NOT create independent section numbers like "1.", "2.", "3." - you are already inside section 2.2
- All content will be inserted into the main report under "2. Style Parameters"

## CRITICAL CONSTRAINTS - MUST FOLLOW

[保持原有的CRITICAL CONSTRAINTS部分不变]

## Table

[保持原有的Table部分不变]

## Output Structure

Your output MUST follow this exact structure:

\```markdown
### 2.2 Prophylaxis

[Brief introduction paragraph]

**Table:**

| Tag name | Count | Ratio | Top GM Avg | Interpretation |
|---|---|---|---|---|
| Direct prophylactic | ... | ... | ... | ... |
| Latent prophylactic | ... | ... | ... | ... |
| Meaningless prophylactic | ... | ... | ... | ... |
| Failed prophylactic | ... | ... | ... | ... |

#### Overall Prophylaxis Orientation

[Analysis of prophylaxis frequency and comparison with GMs]

#### Prophylaxis Quality & Type

[Analysis of direct vs latent balance, meaningless and failed ratios]

#### Style Implications

[What this prophylactic profile reveals about playing style]
\```

## Analysis Instructions

[保持原有的detailed analysis instructions，但将所有 ### 1., ### 2. 改为 ####]

#### Overall Prophylaxis Orientation

Identify which GM range the player falls within, then explain what that level means:

[...保持原内容...]

#### Prophylaxis Quality & Type

[...保持原内容...]

#### Style Implications

[...保持原内容...]

## Analysis Guidelines

- Write in a professional, coaching tone
- Focus on **what prophylaxis patterns reveal about playing style**
- Always compare with GM reference data from the JSON
- Do NOT invent section numbers or create a mini 1-X structure
- This is a subsection of Section 2, not a standalone report
- Use GM references to illustrate style categories, not as the sole focus

[PLAYER_PROFILE_JSON WILL BE APPENDED BELOW]
```

## 特殊处理：style_exchanges_forced.md → 2.9 Style Synthesis

这个文件需要完全重写，因为2.9不是一个单独的tag family，而是对2.1-2.8的综合。

### 新的2.9 Style Synthesis应该：

1. **不再分析exchanges和forced moves** (这些应该移到1.8和1.9)
2. **综合整合2.1-2.8的所有patterns**
3. **识别主导的style dimensions**
4. **寻找一致性或矛盾**
5. **与最接近的2-3位GM比较**
6. **保持简洁** (2-3段)，作为Section 3 (Overall Synthesis)的前奏

### 建议的2.9结构：

```markdown
# 2.9 Style Synthesis

**CONTEXT**: You are writing subsection **2.9 Style Synthesis** within Section 2 (Style Parameters). This subsection integrates all the tag families (2.1-2.8) into a cohesive style profile.

**CRITICAL STRUCTURAL REQUIREMENTS**:
- You MUST start with heading: `### 2.9 Style Synthesis`
- This is NOT a new tag analysis - it's a synthesis of sections 2.1-2.8
- Keep this concise (2-3 paragraphs) as it will be complemented by Section 3 (Overall Synthesis)
- Do NOT repeat detailed analysis from 2.1-2.8
- Focus on cross-domain patterns and interactions

## Output Structure

Your output MUST follow this exact structure:

\```markdown
### 2.9 Style Synthesis

#### Dominant Style Dimensions

[Identify which of the tag families (maneuver, prophylaxis, control, dynamics, initiative, tension, structure, sacrifice) are most prominent in the player's style, based on the ratios from 2.1-2.8]

#### Pattern Consistency and Contradictions

[Look for consistency (e.g., high control + high prophylaxis + low sacrifice = Karpov-like) or contradictions (e.g., high tension but low initiative = wait-and-pounce player)]

#### GM Style Cluster

[Based on the integrated patterns from 2.1-2.8, identify which 2-3 GMs the player most resembles. Be specific about which dimensions match and which differ.]
\```

## Analysis Guidelines

- Integrate all patterns from 2.1-2.8
- Identify the player's central style identity
- Look for cross-domain consistency or contradictions
- Compare with 2-3 closest GMs based on the composite profile
- Keep concise - detailed synthesis is in Section 3
- Do NOT re-analyze individual tag families
- Focus on how the families interact and what the composite reveals

[PLAYER_PROFILE_JSON WILL BE APPENDED BELOW]
```

## 批量应用检查清单

对每个文件 `style_*.md`:

- [ ] 更新文件标题为 `# 2.X [Topic]`
- [ ] 添加CONTEXT和STRUCTURAL REQUIREMENTS
- [ ] 插入Output Structure section
- [ ] 将所有 `### 1.`, `### 2.` 等改为 `####` (不带数字)
- [ ] 添加Analysis Guidelines section
- [ ] 确认CRITICAL CONSTRAINTS section保持不变
- [ ] 确认Table section保持不变
- [ ] 确认[PLAYER_PROFILE_JSON]占位符在文件末尾

## 测试验证

更新后，生成一份报告并检查：

1. 左侧导航显示 "2.1 Maneuver", "2.2 Prophylaxis" 等
2. 点击导航链接能跳转到正确位置
3. LLM生成的内容以 `### 2.X [Topic]` 开头
4. 子标题使用 `####` 而不是 `### 1.`, `### 2.`
5. 没有出现独立的1-6编号系统
6. 每个subsection保持在2-3页以内
7. GM比较基于JSON数据，不是凭空捏造

## 导航ID对应关系

确保LLM生成的markdown heading能被正确转换为HTML id：

- `### 2.1 Maneuver` → 被插入`<div id="style-maneuver">`
- `### 2.2 Prophylaxis` → 被插入`<div id="style-prophylaxis">`
- 等等...

这些ID由`report_builder.py`的`render_style_parameters`函数生成。
