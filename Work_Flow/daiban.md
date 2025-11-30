# 待办事项 / 工作日志

## ✅ 已完成（2025-11-28）

### 1. Phase 2 模板架构迁移
- **目标**: 从"LLM 写整页"改为"前端模板 + LLM 填空"方案
- **完成文件**:
  - `change.md` - 详细说明 Phase 2 架构设计原则
  - `style_report/templates/report_base_phase2.html` - 完整的 Phase 2 HTML 模板

### 2. HTML 模板结构
- **Section 1**: Performance Profile (1.1-1.10) - 完整表格结构 + LLM slots
- **Section 2**: Style Parameters (2.1-2.9) - 完整表格结构 + LLM slots
- **Section 3-6**: 基础框架（Opening Prep, Tactics, Training Habits, Opponent Prep）

### 3. GM 对比轴可视化组件
**已添加可视化的 sections**:
- 1.9 Forced Moves
- 1.10 Winning/Losing Position Handling
- 2.1 Maneuver
- 2.2 Prophylaxis
- 2.3 Semantic Control
- 2.4 Control Over Dynamics
- 2.5 Initiative
- 2.6 Tension Management
- 2.7 Structural Play
- 2.8 Sacrificial Play

**实现细节**:
- 创建 `style_report/assets/report_viz.css` - 渐变轴线样式、GM 标记（蓝色）、玩家标记（红色带脉冲动画）
- 创建 `style_report/assets/report_viz.js` - GMAxisViz 类库
- 创建 `style_report/viz_demo.html` - 独立演示页面
- 在 `report_base_phase2.html` 中内联 GMAxisViz 类（第 1398-1521 行）
- 添加示例数据并渲染所有 10 个可视化（第 1527-1640 行）
- 更新坐标轴值域：不再固定 0-100，而是动态取该 metric 中 GM 的最小/最大百分比（若玩家值超出，则扩展边界）
- GM 轴仅展示 `current GM metrics` 文件夹内的棋手，并在标签中显示对应文件夹里的照片
- 所有需要 LLM 的位置预留可见框（含占位提示），带坐标图的 subsection 将 LLM 框放在坐标图之后
- 1.3 / 1.4 使用英文版 Metric/Value 表格布局（淡蓝斑马纹），替换原来的中文描述块
- 1.3 / 1.4 表格改为阈值 W/D/L 英文版（+1/+3/+5/+7 与 -1/-3/-5/-7），与示例图一致，并更新数据填充逻辑
- 1.5 Volatility/Trajectory 表格替换为英文版 Metric/Value 布局（Avg swings, Sharp positions, Win rate in sharp positions）
- 1.5 再次调整为六行 + White/Black 列（smooth crush/collapse, small/medium/big swings, high-precision draws），并更新数据填充逻辑

### 4. CSS 路径修复 🔧
**问题**: CSS 文件加载失败，页面无样式
**原因**:
```
错误路径: ../../assets/report.css  (从 templates/ 往上两级，跑到项目外了)
正确路径: ../assets/report.css     (从 templates/ 回到 style_report/，再进 assets/)
```
**修复**:
- 将 `href="../../assets/report.css"` 改为 `href="../assets/report.css"`
- 将 `href="../../assets/report_viz.css"` 改为 `href="../assets/report_viz.css"`
- 新增 CSS 兜底 loader：若相对路径加载失败（如 HTTP server 根目录不同），自动回退到 `/style_report/assets/report.css` 与 `/style_report/assets/report_viz.css`

**文件结构**:
```
/Users/alex/Desktop/chess_report_page/  (← HTTP server 根目录)
├── style_report/
│   ├── assets/
│   │   ├── report.css
│   │   └── report_viz.css
│   └── templates/
│       └── report_base_phase2.html
```

## 📂 关键文件说明

### `change.md`
Phase 2 架构设计文档，说明：
- 核心原则：前端写死表格，LLM 只填 slots
- JSON 数据结构：`{ fixed_data, llm_slots, visualizations }`
- Prompt 变化：从"写整节"改为"写一个 slot"

### `report_base_phase2.html`
完整的前端模板，包含：
- 所有表格的 HTML 结构（预留 `id="data-*"` 用于数据注入）
- LLM 插槽（`<div class="llm-slot" id="section-X-Y-topic-llm">`）
- 10 个 GM 对比轴可视化组件
- `window.fillReportData()` 函数（第 1487 行）
- GMAxisViz 类定义（第 1398 行）
- 示例数据渲染（第 1637 行）

### `VISUALIZATION_INTEGRATION_GUIDE.md`
完整的可视化集成指南，包含：
- 每个 section 的 HTML 模板
- JavaScript 数据注入方法
- JSON 数据格式示例

## 🎨 可视化效果

访问 `http://localhost:8000/style_report/templates/report_base_phase2.html` 可以看到：
- ✅ 左侧深色 sidebar 导航
- ✅ 右侧卡片式 sections
- ✅ 表格样式正常
- ✅ 10 个 GM 对比轴（水平渐变轴线，蓝色 GM 圆点，红色玩家圆点带脉冲动画）

## 📊 数据流程

```
后端 Python
  ↓
生成 JSON:
{
  "fixed_data": { winrate: {...}, accuracy: {...}, ... },
  "llm_slots": { "section-1-1-winrate-llm": "<p>...</p>", ... },
  "visualizations": { "viz-forced-moves-axis": { min: 0, max: 100, ... }, ... }
}
  ↓
渲染模板: report_base_phase2.html
  ↓
window.fillReportData(dataJson)
  ↓
vizLib.create() 渲染所有可视化
```

## 🚀 下一步

- [ ] 后端生成 `fixed_data` 数据（从统计计算中提取）
- [ ] 后端生成 `visualizations` 数据（GM 对比值）
- [ ] 配置 LLM prompts 用于填充 `llm_slots`
- [ ] 测试完整数据注入流程
- [ ] 添加更多交互功能（tooltip、hover 效果等）

## 🐛 调试技巧

1. **CSS 不加载**:
   - 按 F12 → Network 标签 → 查看 CSS 文件是否 404
   - 检查路径是否正确（相对于 HTML 文件位置）

2. **可视化不显示**:
   - 按 F12 → Console 标签 → 查看 JavaScript 错误
   - 确认 GMAxisViz 类在使用前已定义
   - 确认容器 ID 与数据 ID 匹配

3. **变量未替换** (如 `{{PLAYER_ID}}`):
   - 这是正常的 - 需要后端模板引擎（Jinja2）渲染
   - 直接打开 HTML 文件会显示原始模板变量
