# GM Axis Visualization Integration Guide

## ✅ 已完成的工作

### 1. 创建的文件
- ✅ [`style_report/assets/report_viz.css`](style_report/assets/report_viz.css) - 可视化样式
- ✅ [`style_report/assets/report_viz.js`](style_report/assets/report_viz.js) - JavaScript 库
- ✅ [`style_report/viz_demo.html`](style_report/viz_demo.html) - 演示页面（可直接打开查看效果）

### 2. 已添加可视化的 Sections
- ✅ 1.9 Forced Moves
- ✅ 1.10 Winning/Losing Position Handling
- ✅ 2.1 Maneuver

### 3. 需要手动添加可视化的 Sections
以下 sections 需要在 [`report_base_phase2.html`](style_report/templates/report_base_phase2.html) 中添加可视化组件：

- ⏳ 2.2 Prophylaxis
- ⏳ 2.3 Semantic Control
- ⏳ 2.4 Control Over Dynamics
- ⏳ 2.5 Initiative
- ⏳ 2.6 Tension Management
- ⏳ 2.7 Structural Play
- ⏳ 2.8 Sacrificial Play

## 📋 添加方法

### 步骤 1: 在 HTML 模板中添加可视化组件

在每个 section 的表格之后、LLM slot 之前添加以下 HTML：

```html
<!-- GM Comparison Axis Visualization -->
<div class="gm-axis-viz">
  <div class="gm-axis-title">标题文字 vs Top GMs</div>
  <div class="gm-axis-container">
    <div class="gm-axis-line"></div>
    <div class="gm-markers-layer" id="viz-SECTION-ID-axis"></div>
  </div>
  <div class="gm-axis-scale">
    <span class="gm-scale-mark">0%</span>
    <span class="gm-scale-mark">25%</span>
    <span class="gm-scale-mark">50%</span>
    <span class="gm-scale-mark">75%</span>
    <span class="gm-scale-mark">100%</span>
  </div>
  <div class="gm-axis-legend">
    <div class="legend-item">
      <div class="legend-dot"></div>
      <span>Top GMs</span>
    </div>
    <div class="legend-item">
      <div class="legend-dot player"></div>
      <span>You</span>
    </div>
  </div>
</div>
```

### 步骤 2: 配置每个 Section

#### 2.2 Prophylaxis
```html
<!-- 在表格后添加 -->
<div class="gm-axis-viz">
  <div class="gm-axis-title">Overall Prophylaxis Ratio vs Top GMs</div>
  <div class="gm-axis-container">
    <div class="gm-axis-line"></div>
    <div class="gm-markers-layer" id="viz-prophylaxis-axis"></div>
  </div>
  <div class="gm-axis-scale">
    <span class="gm-scale-mark">0%</span>
    <span class="gm-scale-mark">10%</span>
    <span class="gm-scale-mark">20%</span>
    <span class="gm-scale-mark">30%</span>
    <span class="gm-scale-mark">40%</span>
  </div>
  <div class="gm-axis-legend">...</div>
</div>
```

#### 2.3 Semantic Control
```html
<div class="gm-axis-viz">
  <div class="gm-axis-title">Semantic Control Ratio vs Top GMs</div>
  <div class="gm-axis-container">
    <div class="gm-axis-line"></div>
    <div class="gm-markers-layer" id="viz-semantic-control-axis"></div>
  </div>
  <div class="gm-axis-scale">
    <span class="gm-scale-mark">0%</span>
    <span class="gm-scale-mark">15%</span>
    <span class="gm-scale-mark">30%</span>
    <span class="gm-scale-mark">45%</span>
    <span class="gm-scale-mark">60%</span>
  </div>
  <div class="gm-axis-legend">...</div>
</div>
```

#### 2.4 Control Over Dynamics
```html
<div class="gm-axis-viz">
  <div class="gm-axis-title">Control Over Dynamics vs Top GMs</div>
  <div class="gm-axis-container">
    <div class="gm-axis-line"></div>
    <div class="gm-markers-layer" id="viz-cod-axis"></div>
  </div>
  <div class="gm-axis-scale">
    <span class="gm-scale-mark">0%</span>
    <span class="gm-scale-mark">15%</span>
    <span class="gm-scale-mark">30%</span>
    <span class="gm-scale-mark">45%</span>
    <span class="gm-scale-mark">60%</span>
  </div>
  <div class="gm-axis-legend">...</div>
</div>
```

#### 2.5 Initiative
```html
<div class="gm-axis-viz">
  <div class="gm-axis-title">Initiative Attempt Ratio vs Top GMs</div>
  <div class="gm-axis-container">
    <div class="gm-axis-line"></div>
    <div class="gm-markers-layer" id="viz-initiative-axis"></div>
  </div>
  <div class="gm-axis-scale">
    <span class="gm-scale-mark">0%</span>
    <span class="gm-scale-mark">10%</span>
    <span class="gm-scale-mark">20%</span>
    <span class="gm-scale-mark">30%</span>
    <span class="gm-scale-mark">40%</span>
  </div>
  <div class="gm-axis-legend">...</div>
</div>
```

#### 2.6 Tension Management
```html
<div class="gm-axis-viz">
  <div class="gm-axis-title">Tension Creation Ratio vs Top GMs</div>
  <div class="gm-axis-container">
    <div class="gm-axis-line"></div>
    <div class="gm-markers-layer" id="viz-tension-axis"></div>
  </div>
  <div class="gm-axis-scale">
    <span class="gm-scale-mark">0%</span>
    <span class="gm-scale-mark">5%</span>
    <span class="gm-scale-mark">10%</span>
    <span class="gm-scale-mark">15%</span>
    <span class="gm-scale-mark">20%</span>
  </div>
  <div class="gm-axis-legend">...</div>
</div>
```

#### 2.7 Structural Play
```html
<div class="gm-axis-viz">
  <div class="gm-axis-title">Structural Integrity Ratio vs Top GMs</div>
  <div class="gm-axis-container">
    <div class="gm-axis-line"></div>
    <div class="gm-markers-layer" id="viz-structural-axis"></div>
  </div>
  <div class="gm-axis-scale">
    <span class="gm-scale-mark">0%</span>
    <span class="gm-scale-mark">20%</span>
    <span class="gm-scale-mark">40%</span>
    <span class="gm-scale-mark">60%</span>
    <span class="gm-scale-mark">80%</span>
  </div>
  <div class="gm-axis-legend">...</div>
</div>
```

#### 2.8 Sacrificial Play
```html
<div class="gm-axis-viz">
  <div class="gm-axis-title">Overall Sacrifice Ratio vs Top GMs</div>
  <div class="gm-axis-container">
    <div class="gm-axis-line"></div>
    <div class="gm-markers-layer" id="viz-sacrifice-axis"></div>
  </div>
  <div class="gm-axis-scale">
    <span class="gm-scale-mark">0%</span>
    <span class="gm-scale-mark">3%</span>
    <span class="gm-scale-mark">6%</span>
    <span class="gm-scale-mark">9%</span>
    <span class="gm-scale-mark">12%</span>
  </div>
  <div class="gm-axis-legend">...</div>
</div>
```

## 🔧 JavaScript 数据注入

### 在 `fillReportData` 函数中添加

在 `report_base_phase2.html` 的末尾 `<script>` 标签中，添加可视化数据注入：

```javascript
// Load visualization library
const vizLib = new GMAxisViz();

// After filling fixed_data and llm_slots, render visualizations
if (dataJson.visualizations) {
  Object.keys(dataJson.visualizations).forEach(vizId => {
    vizLib.create(vizId, dataJson.visualizations[vizId]);
  });
}
```

### 后端 JSON 格式示例

```json
{
  "fixed_data": { ... },
  "llm_slots": { ... },
  "visualizations": {
    "viz-forced-moves-axis": {
      "min": 0,
      "max": 100,
      "player": { "name": "You", "value": 42.5 },
      "gms": [
        { "name": "Tal", "value": 28.3 },
        { "name": "Kasparov", "value": 35.7 },
        { "name": "Carlsen", "value": 45.2 },
        { "name": "Petrosian", "value": 52.8 },
        { "name": "Karpov", "value": 48.6 }
      ]
    },
    "viz-maneuver-axis": {
      "min": 0,
      "max": 40,
      "player": { "name": "You", "value": 18.3 },
      "gms": [
        { "name": "Karpov", "value": 24.5 },
        { "name": "Petrosian", "value": 22.8 },
        { "name": "Carlsen", "value": 19.7 }
      ]
    }
    // ... 其他可视化
  }
}
```

## 🎨 查看效果

打开 [`viz_demo.html`](style_report/viz_demo.html) 查看可视化效果演示！

## 📌 注意事项

1. **每个 viz ID 必须唯一** - 使用 `viz-{section}-axis` 格式
2. **scale 值应与数据范围匹配** - 不同的 style parameter 有不同的范围
3. **GM 数据点数量** - 建议 3-6 个 GM 点，太多会重叠
4. **响应式设计** - 在小屏幕上自动调整布局

## 🚀 下一步

1. ✅ 手动添加 2.2-2.8 的可视化 HTML 到模板
2. ✅ 在 HTML 中引入 `report_viz.js`
3. ✅ 更新后端代码生成 `visualizations` 数据
4. ✅ 测试完整报告渲染

---

完成后，所有 sections (1.9, 1.10, 2.1-2.8) 都将有美观的 GM 对比可视化！
