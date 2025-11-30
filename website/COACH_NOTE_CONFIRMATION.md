# Coach Note Confirmation Modal - 实现文档

## 功能概述

为 "Generate coach note" 按钮添加了确认弹窗,包含猫咪图标和漫画对话框样式。

## 实现效果

### 点击 "Generate coach note" 后:
1. 立即弹出确认对话框
2. 对话框中显示问题: "Are you sure you want to generate coach note?"
3. 右下角显示猫咪图标 (cat.png)
4. 两个按钮:
   - **No** (灰色) - 关闭弹窗,取消操作
   - **Yes** (绿色) - 确认生成,开始显示旋转的 loading4.png

## 代码结构

### 1. CSS 样式 (第831-937行)

#### 弹窗覆盖层
```css
.coach-confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(2px);
  z-index: 100;
}
```

#### 对话框容器
```css
.coach-confirm-modal {
  background: #ffffff;
  border-radius: 20px;
  padding: 30px 24px 20px;
  max-width: 400px;
  animation: modalPop 0.3s ease-out;
}
```

#### 漫画对话框气泡
```css
.coach-confirm-bubble {
  background: #ffffff;
  border: 2px solid #1f2937;
  border-radius: 16px;
  padding: 20px;
  position: relative;
}

/* 对话框小三角 (指向猫咪) */
.coach-confirm-bubble::after {
  border-top: 16px solid #1f2937;  /* 外边框 */
}
.coach-confirm-bubble::before {
  border-top: 13px solid #ffffff;  /* 内填充 */
}
```

#### 猫咪图标
```css
.coach-confirm-cat {
  position: absolute;
  bottom: -10px;
  right: 10px;
  width: 80px;
  height: 80px;
}
```

#### 按钮样式
```css
.coach-confirm-btn.yes {
  background: #22c55e;  /* 绿色 */
  color: #ffffff;
}
.coach-confirm-btn.no {
  background: #ffffff;  /* 白色 */
  border: 1px solid #d1d5db;
}
```

### 2. HTML 结构 (第1130-1141行)

```html
<div id="coachConfirmOverlay" class="coach-confirm-overlay">
  <div class="coach-confirm-modal">
    <div class="coach-confirm-bubble">
      Are you sure you want to generate coach note?
    </div>
    <div class="coach-confirm-buttons">
      <button class="coach-confirm-btn no" onclick="closeCoachConfirm()">No</button>
      <button class="coach-confirm-btn yes" onclick="confirmGenerateCoachNote()">Yes</button>
    </div>
    <img src="assets/cat.png" class="coach-confirm-cat" />
  </div>
</div>
```

### 3. JavaScript 函数

#### `generateCoachNote()` - 修改后 (第2090-2107行)
**之前:** 直接执行生成逻辑
**现在:** 先显示确认弹窗

```javascript
function generateCoachNote() {
  const gm = pickActiveGm();
  if (!gm) {
    alert("Please add/select a player first...");
    return;
  }

  // 显示确认弹窗
  const overlay = document.getElementById('coachConfirmOverlay');
  if (overlay) {
    overlay.classList.add('show');
  }
}
```

#### `closeCoachConfirm()` - 新增 (第2110-2115行)
关闭确认弹窗

```javascript
function closeCoachConfirm() {
  const overlay = document.getElementById('coachConfirmOverlay');
  if (overlay) {
    overlay.classList.remove('show');
  }
}
```

#### `confirmGenerateCoachNote()` - 新增 (第2130行起)
点击 "Yes" 后执行的真正生成逻辑

```javascript
async function confirmGenerateCoachNote() {
  // 1. 关闭确认弹窗
  closeCoachConfirm();

  // 2. 开始显示 loading (旋转的 loading4.png)
  updateCoachStatus(`正在为 ${gm.name} 生成教练点评…`, true);

  // 3. 调用后端API生成
  // ... (原来的生成逻辑)

  // 4. 完成后隐藏 loading
  updateCoachStatus(`Coach note ready...`, false);
}
```

#### 点击外部关闭 (第2118-2127行)
```javascript
document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById('coachConfirmOverlay');
  if (overlay) {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        closeCoachConfirm();
      }
    });
  }
});
```

## 交互流程

```
用户点击 "Generate coach note"
         ↓
检查是否选择了棋手
         ↓
显示确认弹窗 (带猫咪图标)
         ↓
    ┌────┴────┐
    ↓         ↓
  点击 No   点击 Yes
    ↓         ↓
关闭弹窗   关闭弹窗
           ↓
    显示 loading 动画
    (80x80 旋转的 loading4.png)
           ↓
    调用后端API
           ↓
    生成完成,填入输入框
```

## 视觉设计特点

1. **对话框气泡样式**
   - 白色背景,黑色边框
   - 圆角设计 (16px)
   - 带指向猫咪的小三角

2. **猫咪位置**
   - 右下角固定定位
   - 80x80px 大小
   - 带阴影效果

3. **弹出动画**
   - `modalPop` 动画: 从 0.9 缩放到 1
   - 0.3秒缓动
   - 渐入效果

4. **按钮交互**
   - Hover 时向上移动 1px
   - 添加阴影
   - Yes 按钮绿色背景
   - No 按钮白色背景

## 关闭方式

用户可以通过以下方式关闭弹窗:
1. 点击 "No" 按钮
2. 点击弹窗外部的灰色区域
3. 点击 "Yes" 按钮后自动关闭并开始生成

## 资源依赖

- `assets/cat.png` - 猫咪图标
- `assets/loading4.png` - 加载动画图标
- 已有的 `spin360` CSS 动画

## 测试要点

1. ✅ 点击按钮立即显示弹窗
2. ✅ 猫咪图标正确显示在右下角
3. ✅ 对话框气泡的三角指向猫咪
4. ✅ "No" 按钮关闭弹窗
5. ✅ "Yes" 按钮开始生成并显示旋转动画
6. ✅ 点击外部关闭弹窗
7. ✅ 未选择棋手时显示提示
8. ✅ 弹窗弹出动画流畅
