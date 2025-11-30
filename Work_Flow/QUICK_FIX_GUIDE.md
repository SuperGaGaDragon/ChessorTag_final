# Phase2迁移快速修复指南

## 核心问题总结

**问题**: LLM prompts还以为自己在写独立的1-6节报告，而实际上它们应该是2.x的子节。

**症状**:
- Initiative部分出现 `<h2>1. Initiative Timing</h2>`, `<h2>5. Practical Training</h2>`
- Structural部分出现 `<h2>1. Structural Philosophy</h2>`, `<h2>2. Style Implications</h2>`
- 导航栏点击`2.5 Initiative`无法跳转（因为LLM没生成正确的heading id）

**根本原因**:
1. Style prompts没有明确告诉LLM它是2.x的子节
2. Prompts允许LLM自己发明1-6编号
3. 没有统一的heading结构要求

## 立即修复方案

### 方案A: 最小改动（推荐用于快速修复）

只修改最明显有问题的两个文件：

1. **style_initiative.md** - 已修复 ✅
2. **style_structural.md** - 已修复 ✅

### 方案B: 完整修复（推荐用于长期）

按照`STYLE_PROMPTS_UPDATE_TEMPLATE.md`更新所有6个剩余文件：

```bash
cd /Users/alex/Desktop/chess_report_page/style_report/prompts

# 需要更新的文件：
# 1. style_prophylaxis.md → 2.2
# 2. style_semantic_control.md → 2.3
# 3. style_cod.md → 2.4
# 4. style_tension.md → 2.6
# 5. style_sacrifice.md → 2.8
# 6. style_exchanges_forced.md → 2.9 (需要重新设计)
```

## 每个文件需要的3个关键改动

### 改动1: 文件顶部添加上下文
在文件最开始，title之后立即添加：

```markdown
**CONTEXT**: You are writing subsection **2.X [Topic]** within the larger Section 2 (Style Parameters) of a comprehensive chess report. This is NOT a standalone report.

**CRITICAL STRUCTURAL REQUIREMENTS**:
- You MUST start with heading: `### 2.X [Topic]`
- Use ONLY `####` level headings for sub-points (no `###` except the main title)
- Do NOT create independent section numbers like "1.", "2.", "3." - you are already inside section 2.X
- All content will be inserted into the main report under "2. Style Parameters"
```

### 改动2: 所有`### 1.`, `### 2.`改为`####`

用查找替换功能：
- 查找: `### 1. `
- 替换: `#### `

- 查找: `### 2. `
- 替换: `#### `

...以此类推

**重要**: 保留标题文字，只删除数字前缀和一个`#`

### 改动3: 文件末尾添加指南

在`[PLAYER_PROFILE_JSON WILL BE APPENDED BELOW]`之前添加：

```markdown
## Analysis Guidelines

- Write in a professional, coaching tone
- Focus on **what the [topic] patterns reveal about playing style**
- Always compare with GM reference data from the JSON
- Do NOT invent section numbers or create a mini 1-X structure
- This is a subsection of Section 2, not a standalone report
```

## 最关键的禁止事项

**绝对不允许LLM做的事情**:

1. ❌ 在2.5下面出现 `## 1. xxx`, `## 2. xxx` 这样的标题
2. ❌ 创建 "5. Practical Training Directions" (这属于总的Section 5)
3. ❌ 创建 "6. Big Picture" (这属于Section 3 Overall Synthesis)
4. ❌ 使用 `###` 作为subsection heading (应该用 `####`)
5. ❌ 不带上下文就开始写（必须先说明自己是2.x的子节）

**必须要求LLM做的事情**:

1. ✅ 第一个heading必须是: `### 2.X [Topic Name]`
2. ✅ 所有subsection用 `####` 不带数字
3. ✅ 只在section 2.X的范围内分析
4. ✅ 所有GM比较严格基于JSON数据

## 快速测试方法

更新prompts后，生成一份新报告，检查：

### 检查点1: 左侧导航
```
✅ 2. Style Parameters
  ✅ 2.1 Maneuver
  ✅ 2.2 Prophylaxis
  ✅ 2.5 Initiative
  ✅ 2.7 Structural Play
```

### 检查点2: 点击"2.5 Initiative"
应该跳转到包含以下内容的区域：
```markdown
### 2.5 Initiative

[introduction]

#### Initiative Timing & Frequency
[content]

#### Initiative Quality & Timing
[content]

#### Style Implications
[content]
```

**不应该**出现：
```markdown
## 1. Initiative Timing & Frequency   ← ❌ 错误
## 5. Practical Training              ← ❌ 错误
```

### 检查点3: HTML源码
查看生成的HTML，应该看到：
```html
<div class="style-block" id="style-initiative">
  <h3>2.5 Initiative</h3>
  ...
  <h4>Initiative Timing & Frequency</h4>
  ...
  <h4>Style Implications</h4>
  ...
</div>
```

**不应该**看到：
```html
<h2>1. Initiative Timing...</h2>    ← ❌ 错误
<h2>5. Practical Training...</h2>   ← ❌ 错误
```

## 如果还有问题

### 问题: 导航点击无法跳转

**原因**: LLM生成的heading没有对应的ID

**解决方案**:
1. 检查`report_builder.py`中的`render_style_parameters`函数
2. 确认它正确生成`<div id="style-{key}">`
3. 确认markdown renderer将`### 2.5 Initiative`转换为`<h3>2.5 Initiative</h3>`

### 问题: 仍然出现1-6编号

**原因**: Prompt更新不完整或LLM没有遵守指令

**解决方案**:
1. 在prompt中更强硬地禁止: "You MUST NOT use section numbers 1-6. You are writing 2.X only."
2. 在`## Output Structure`中提供明确的模板
3. 考虑在Python中post-process，强制删除不符合规范的heading

### 问题: Subsection太长（>3页）

**原因**: Prompt太详细，LLM过度展开

**解决方案**:
1. 在prompt中添加: "Keep analysis concise. Each subsection should be 1-2 paragraphs."
2. 删除过于详细的例子和模板
3. 强调这只是Section 2的一部分，详细综合在Section 3

## 最简单的验证命令

```bash
# 生成报告
cd /Users/alex/Desktop/chess_report_page
python -m style_report.scripts.run_full_report testYuYaochen

# 在浏览器中打开
open style_report/Test_players/testYuYaochen/report.html

# 检查：
# 1. 左侧导航是否正确
# 2. 点击"2.5 Initiative"能否跳转
# 3. 该section是否以"### 2.5 Initiative"开头
# 4. 是否没有出现"## 1.", "## 2."这样的标题
```

## 成功标准

修复成功的标志：

- ✅ 左侧导航显示正确的编号 (1.1-1.10, 2.1-2.9, 3, 4.1-4.8, 5.1-5.3, 6.1-6.6)
- ✅ 所有导航链接都能跳转
- ✅ 每个section内容以正确的`### X.Y`标题开头
- ✅ 没有任何独立的1-6编号系统
- ✅ Subsections使用`####`不带数字
- ✅ 每个style subsection保持简洁 (1-3页)
- ✅ 所有GM比较基于JSON数据

## 紧急回退方案

如果更新后问题更多，可以临时回退到简化版本：

1. 删除所有style子prompts的详细instructions
2. 只保留基本的表格要求
3. 让每个subsection只输出：
   - 一个表格
   - 1-2段简短分析
   - GM比较（基于JSON）

示例最简prompts：
```markdown
# 2.X [Topic]

Output a table with these tags plus 1-2 paragraphs analyzing what they reveal about the player's style. Compare with GM data from JSON. Start with `### 2.X [Topic]`. Use `####` for any subsections.

[TABLE SPECIFICATION]

[PLAYER_PROFILE_JSON WILL BE APPENDED BELOW]
```

这种极简版本虽然不够详细，但至少不会出现结构混乱的问题。

## 总结

**最重要的三件事**:

1. **明确告诉LLM它的位置**: "你在写2.X，不是独立报告"
2. **禁止自创编号**: "不允许1-6编号，只能用####"
3. **提供明确模板**: "必须以 `### 2.X Topic` 开头"

按照这个原则更新所有prompts，问题就能解决。
