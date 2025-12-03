# 棋盘坐标系统统一修复说明

## 问题描述

之前AB两端的棋盘虽然界面翻转了，但底层坐标定义不同，导致同一个位置在A端和B端的坐标值不一样。这会导致部署的棋子在两端显示位置不一致。

## 解决方案

### 核心思路

采用**绝对坐标系统**（类似国际象棋）：

- **横坐标（列）**: 使用 a-h（对应 col 0-7）
- **纵坐标（行）**: 使用 1-8（对应 row 7-0，注意是反向的）

无论棋盘如何翻转显示，底层的 `data-row` 和 `data-col` 属性**始终保持不变**，只改变CSS Grid的视觉位置。

### 坐标系统定义

```
Row 0 = Rank 8 (a8, b8, c8, d8, e8, f8, g8, h8) - 棋盘顶部
Row 1 = Rank 7 (a7, b7, c7, d7, e7, f7, g7, h7)
Row 2 = Rank 6 (a6, b6, c6, d6, e6, f6, g6, h6)
Row 3 = Rank 5 (a5, b5, c5, d5, e5, f5, g5, h5)
Row 4 = Rank 4 (a4, b4, c4, d4, e4, f4, g4, h4)
Row 5 = Rank 3 (a3, b3, c3, d3, e3, f3, g3, h3)
Row 6 = Rank 2 (a2, b2, c2, d2, e2, f2, g2, h2)
Row 7 = Rank 1 (a1, b1, c1, d1, e1, f1, g1, h1) - 棋盘底部

Col 0 = File 'a'
Col 1 = File 'b'
Col 2 = File 'c'
Col 3 = File 'd'
Col 4 = File 'e'
Col 5 = File 'f'
Col 6 = File 'g'
Col 7 = File 'h'
```

### 部署规则

使用绝对坐标系统后：

- **Side A (allegiance='a')**: 只能部署在 rows 4-7（对应 ranks 1-4，棋盘下半部分）
- **Side B (allegiance='b')**: 只能部署在 rows 0-3（对应 ranks 5-8，棋盘上半部分）

### 关键修改

#### 1. game_page.html 中的 `createBoardGrid` 函数

- `data-row` 和 `data-col` 固定为绝对坐标（0-7）
- `gridRow` 和 `gridColumn` 根据 `boardOrientation` 动态调整视觉位置
- 标签始终显示绝对坐标（如 "e4"）

```javascript
// Side A (orientation='a'): 从下往上看
// Row 7 (rank 1) 显示在 gridRow 8（底部）
// Row 0 (rank 8) 显示在 gridRow 1（顶部）

// Side B (orientation='b'): 从上往下看（棋盘翻转）
// Row 0 (rank 8) 显示在 gridRow 8（底部，从B端看）
// Row 7 (rank 1) 显示在 gridRow 1（顶部，从B端看）
```

#### 2. piece_deploy.js 中的 `isValidCell` 函数

添加了详细的注释说明绝对坐标系统，确保部署规则基于绝对坐标。

#### 3. 增强的日志输出

- 点击棋盘格子时，显示 `square`, `row`, `col`, `gridRow`, `gridCol`
- 部署棋子时，显示 `square (row, col)` 以便调试

## 测试验证步骤

### 1. 启动游戏并检查棋盘生成

打开浏览器控制台，应该看到：

```
[createBoardGrid] Created board with orientation: a (或 b)
[createBoardGrid] data-row and data-col are ABSOLUTE coordinates (same for both sides)
```

### 2. 点击棋盘格子测试坐标

**在 Side A 端（orientation='a'）**：
- 点击左下角的格子，应该显示：`square=a1, row=7, col=0, gridRow=8, gridColumn=1`
- 点击右上角的格子，应该显示：`square=h8, row=0, col=7, gridRow=1, gridColumn=8`

**在 Side B 端（orientation='b'）**：
- 点击左下角的格子（从B端视角），应该显示：`square=h8, row=0, col=7, gridRow=8, gridColumn=1`
- 点击右上角的格子（从B端视角），应该显示：`square=a1, row=7, col=0, gridRow=1, gridColumn=8`

**关键验证点**：
- ✅ Side A 和 Side B 对于**同一个物理位置**，`data-row` 和 `data-col` **必须相同**
- ✅ 但 `gridRow` 和 `gridColumn` 会因为棋盘翻转而不同

### 3. 部署棋子测试

**在 Side A 端部署棋子**：
- 在 e4 位置部署一个棋子，控制台应该显示：
  ```
  [piece_deploy] deployPiece called {square: "e4", row: 4, col: 4, ...}
  [piece_deploy] ✓ Deployed shouter (a) at e4 (row=4, col=4)
  ```

**在 Side B 端查看**：
- Side B 应该在**相同的绝对位置** e4 看到这个棋子
- 但从 Side B 的视角看，e4 显示在不同的屏幕位置（因为棋盘翻转了）

### 4. 网络同步测试

1. 在 Side A 端部署一个棋子到 d5
2. 检查网络消息（在控制台查找 `state_update` 消息）：
   ```json
   {
     "type": "state_update",
     "event": "spawn",
     "piece": {
       "row": 3,
       "col": 3,
       ...
     }
   }
   ```
3. 在 Side B 端应该收到相同的 row=3, col=3
4. Side B 端应该在 d5 位置显示这个棋子（从B端视角看，d5 在不同的屏幕位置，但绝对坐标相同）

### 5. 对称性验证

在 Side A 和 Side B 同时部署棋子：

- Side A 在 e2 部署一个 shouter → `row=6, col=4`
- Side B 在 e7 部署一个 shouter → `row=1, col=4`

两端都应该能正确看到对方的棋子在**正确的绝对位置**。

## 预期效果

修复后：

1. ✅ AB两端对于同一个棋盘位置，使用**相同的 data-row 和 data-col**
2. ✅ 棋盘翻转只影响视觉显示（CSS Grid），不影响底层坐标
3. ✅ 网络同步时，双方使用相同的坐标值
4. ✅ 部署的棋子在双方看到的**绝对位置**一致（虽然屏幕显示位置因翻转而不同）

## 额外说明

### King Tower 位置

King Tower 固定在：
- Side A: rows 6-7, cols 3-4 (对应 d1, e1, d2, e2)
- Side B: rows 0-1, cols 3-4 (对应 d8, e8, d7, e7)

### 普通塔位置

普通塔固定在：
- Side A (row=6): cols 1 和 6 (对应 b2 和 g2)
- Side B (row=1): cols 1 和 6 (对应 b7 和 g7)

### Shouter 限制

Shouter 不能放在 home row 的角落：
- Side A: 不能放在 a1, c1, f1, h1 (row=7, cols 0,2,5,7)
- Side B: 不能放在 a8, c8, f8, h8 (row=0, cols 0,2,5,7)

## 调试技巧

如果发现位置不一致：

1. 检查控制台中的 `[piece_deploy] deployPiece called` 消息，对比 row/col 值
2. 检查 `[BoardCell] Clicked` 消息，确认 data-row 和 data-col 在两端是否相同
3. 检查网络消息中的 row/col 是否正确传输
4. 确认 `boardOrientation` 变量在两端的值（A端应该是'a'，B端应该是'b'）

## 相关文件

- `website/cat_royale/game_page/game_page.html` - 棋盘生成和坐标系统
- `website/cat_royale/piece_deploy/piece_deploy.js` - 部署逻辑和坐标验证
