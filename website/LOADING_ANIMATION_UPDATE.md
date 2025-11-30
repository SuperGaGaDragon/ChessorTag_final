# Loading Animation Update - study/index.html

## 修改概述

在 `study/index.html` 中为 "Generate coach note" 功能添加了 loading4.png 的360度旋转动画。

## 修改详情

### 1. 添加CSS样式 (第810-819行)

```css
.coach-note-loading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.coach-note-loading-icon {
  width: 24px;
  height: 24px;
  animation: spin360 1.2s linear infinite;
}
```

- 使用已有的 `spin360` 关键帧动画 (第298-301行定义)
- 图标大小: 24x24px
- 旋转速度: 1.2秒一圈,无限循环

### 2. 更新 `updateCoachStatus()` 函数 (第1921-1934行)

**之前:**
```javascript
function updateCoachStatus(msg) {
  if (coachNoteStatus) {
    coachNoteStatus.textContent = msg;
  }
}
```

**修改后:**
```javascript
function updateCoachStatus(msg, showLoading = false) {
  if (coachNoteStatus) {
    if (showLoading) {
      coachNoteStatus.innerHTML = `
        <div class="coach-note-loading">
          <img src="../assets/loading4.png" alt="loading" class="coach-note-loading-icon" />
          <span>${msg}</span>
        </div>
      `;
    } else {
      coachNoteStatus.textContent = msg;
    }
  }
}
```

**改进点:**
- 添加 `showLoading` 参数来控制是否显示加载动画
- 当 `showLoading = true` 时,显示旋转的 loading4.png 图标
- 否则显示普通文本

### 3. 修改 `generateCoachNote()` 函数 (第2004和2036行)

**修改点:**

**开始加载时:**
```javascript
updateCoachStatus(`正在为 ${gm.name} 生成教练点评…`, true);  // showLoading = true
```

**完成后:**
```javascript
updateCoachStatus(`Coach note ready: 已为 ${gm.name} 写入输入框，点击下方 "Add comment" 保存。`, false);  // showLoading = false
```

## 效果展示

### 加载中状态
```
[旋转的loading4.png图标] 正在为 Kasparov 生成教练点评…
```

### 完成状态
```
Coach note ready: 已为 Kasparov 写入输入框，点击下方 "Add comment" 保存。
```

## 使用的资源

- **图标:** `assets/loading4.png`
- **动画:** 复用了已有的 `spin360` CSS 关键帧
- **显示位置:** Comment / coach notes 区域的状态栏

## 兼容性

- 动画使用标准CSS `@keyframes`,兼容所有现代浏览器
- 图标大小适配移动端和桌面端
- 如果 loading4.png 不存在,会显示 alt 文本

## 测试步骤

1. 打开 study/index.html
2. 选择一个 GM 棋手 (点击 "+ Add" 按钮)
3. 点击 "Generate coach note" 按钮
4. 观察 Comment 区域的状态栏:
   - 应该看到 loading4.png 图标在旋转
   - 旋转动画应该流畅,无卡顿
5. 等待生成完成后,旋转图标消失,显示完成消息
