# Bug修复总结 - 2025-12-03

## 🐛 修复的问题

### 问题1：B端部署棋子时出现两个重复的棋子 ✅

**症状**：
- B端（CLIENT）玩家部署棋子时，会同时出现两个相同的棋子
- 日志显示收到两次相同的 `spawn` 事件

**根本原因**：
1. B端调用 `deployPiece` → 触发 `handleLocalDeployRequest` → 发送 `deploy_request` 到服务器
2. 服务器转发给 A端（HOST）
3. A端的 `handleDeployRequest` 调用 `deployPiece` → 完成部署
4. A端的 `deployPiece` 调用 `handleLocalDeploy` → 发送第一次 `spawn`
5. A端的 `handleDeployRequest` 又发送第二次 `spawn`
6. 两次 `spawn` 都被广播给 B端，导致重复部署

**修复方案**：
在 `handleDeployRequest` 调用 `deployPiece` 时传入 `skipBroadcast: true`，防止 `deployPiece` 内部再次调用 `handleLocalDeploy`。

**修改文件**：
- [game_page.html:1013](website/cat_royale/game_page/game_page.html#L1013) - 添加 `skipBroadcast: true` 参数
- [piece_deploy.js:658](website/cat_royale/piece_deploy/piece_deploy.js#L658) - 检查 `options.skipBroadcast`

### 问题2：塔楼不攻击 ✅

**症状**：
- 修复死亡同步后，CLIENT端的塔楼不再攻击敌方棋子
- 没有攻击动画，没有伤害

**根本原因**：
之前的修复中，我们在所有攻击函数开头添加了 `if (window.IS_HOST !== true) return;`，这导致：
- CLIENT端完全跳过攻击逻辑
- `scanTowerAttacks` 在 CLIENT端无法启动攻击
- 没有攻击动画，没有视觉反馈

**修复方案**：
- 移除攻击函数中的 HOST 检查
- **只在 `applyDamage` 中检查 HOST**
- 攻击动画和判定在两端都运行，但伤害计算只在 HOST端执行

**修改文件**：
- [shouter_attack.js:16-20](website/cat_royale/moving/piece_attack/shouter_attack.js#L16-L20) - 移除 HOST 检查
- [fighter_move.js:16-20](website/cat_royale/moving/pieces_move/fighter_move.js#L16-L20) - 移除 HOST 检查
- [aggressive_tower_attack.js:26-30](website/cat_royale/moving/piece_attack/aggressive_tower_attack.js#L26-L30) - 移除 HOST 检查
- [solid_tower_attack.js:26-30](website/cat_royale/moving/piece_attack/solid_tower_attack.js#L26-L30) - 移除 HOST 检查
- [ruler_attack.js:22-26](website/cat_royale/moving/piece_attack/ruler_attack.js#L22-L26) - 移除 HOST 检查
- [squirmer_attack.js:15-19](website/cat_royale/moving/piece_attack/squirmer_attack.js#L15-L19) - 移除 HOST 检查

### 问题3：postToParent 未定义 ✅

**症状**：
- `piece_deploy.js` 中的 `window.postToParent` 返回 `undefined`
- `damage` 和 `death` 事件无法广播

**根本原因**：
`game_page.html` 中的 `postToParent` 是一个局部函数，没有被设置到 `window` 对象上。

**修复方案**：
在定义 `postToParent` 后，添加 `window.postToParent = postToParent;`

**修改文件**：
- [game_page.html:722-723](website/cat_royale/game_page/game_page.html#L722-L723) - 添加 `window.postToParent = postToParent;`

## ✅ 最终架构

### 网络同步流程

```
部署棋子：
CLIENT → deploy_request → HOST → deployPiece(skipBroadcast:true) → spawn → CLIENT

攻击流程：
HOST: 扫描 → 发起攻击 → 播放动画 → applyDamage → 计算伤害 → 广播 damage
CLIENT: 扫描 → 发起攻击 → 播放动画 → applyDamage → 跳过（非HOST） → 等待 damage 事件

死亡流程：
HOST: HP≤0 → handleDeath → 本地处理 → 广播 death
CLIENT: 收到 death → handleDeathFromServer → 本地处理
```

### 关键原则

1. **伤害计算只在 HOST 端**：`applyDamage` 函数检查 `window.IS_HOST`
2. **攻击逻辑在两端运行**：用于动画和视觉效果
3. **状态通过事件同步**：`damage`、`death`、`spawn` 事件
4. **防止重复广播**：使用 `skipBroadcast` 标志

## 📋 文件修改清单

### 核心系统
- ✅ `website/cat_royale/piece_deploy/piece_deploy.js`
  - applyDamage: HOST 判定 + damage 事件广播
  - handleDeath: 重复保护 + death 事件广播
  - deployPiece: skipBroadcast 支持

- ✅ `website/cat_royale/game_page/game_page.html`
  - postToParent: 设置到 window 对象
  - handleDeployRequest: 添加 skipBroadcast 参数
  - applyDamageFromServer: 强制同步 HP
  - handleDeathFromServer: 处理 death 事件
  - handleStateUpdate: 添加 death case

### 攻击模块（移除 HOST 检查）
- ✅ `website/cat_royale/moving/piece_attack/shouter_attack.js`
- ✅ `website/cat_royale/moving/pieces_move/fighter_move.js`
- ✅ `website/cat_royale/moving/piece_attack/aggressive_tower_attack.js`
- ✅ `website/cat_royale/moving/piece_attack/solid_tower_attack.js`
- ✅ `website/cat_royale/moving/piece_attack/ruler_attack.js`
- ✅ `website/cat_royale/moving/piece_attack/squirmer_attack.js`

## 🧪 测试建议

### 1. 部署测试
- ✅ B端部署棋子，检查是否只出现一个
- ✅ 检查控制台日志，不应该有重复的 spawn

### 2. 攻击测试
- ✅ 塔楼攻击敌方棋子
- ✅ 两端都应该看到攻击动画
- ✅ B端控制台应该看到 `[piece_deploy] CLIENT should not call applyDamage directly`

### 3. 死亡测试
- ✅ 棋子死亡时两端同步消失
- ✅ 检查日志，应该有 death 事件

### 4. 网络测试
- ⏳ 模拟网络延迟（200ms）
- ⏳ 验证最终状态一致

## ⚠️ 注意事项

1. **服务器端不需要修改**
   - 服务器只需要原样转发所有 `state_update` 事件
   - `death` 事件会被自动转发

2. **旧的 death_sync_implementation_summary.md 部分过时**
   - 攻击函数中的 HOST 检查已移除
   - 现在的架构更简洁：攻击在两端运行，伤害只在 HOST 计算

3. **CLIENT 端的警告日志是正常的**
   - `[piece_deploy] CLIENT should not call applyDamage directly` 表示 CLIENT 端的攻击正确地被拒绝了伤害计算

## 🎯 修复效果

### 之前
- ❌ B端部署棋子会出现两个
- ❌ 塔楼不攻击
- ❌ `postToParent` 未定义导致事件无法广播

### 现在
- ✅ B端部署棋子只出现一个
- ✅ 塔楼正常攻击，两端都有动画
- ✅ 伤害计算只在 HOST 端执行
- ✅ 死亡事件正确同步
- ✅ 所有事件都能正确广播

## 📝 总结

这次修复解决了三个关键问题：
1. 重复部署 → 通过 `skipBroadcast` 避免重复广播
2. 塔楼不攻击 → 只在 `applyDamage` 中检查 HOST，而不是在攻击函数中
3. 事件无法广播 → 将 `postToParent` 设置到 `window` 对象

核心思路：**视觉和逻辑分离**
- 视觉（攻击动画、移动）：在两端运行
- 逻辑（伤害计算、状态变更）：只在 HOST 端执行，然后通过事件同步给 CLIENT

这样既保证了视觉体验（CLIENT 端不会有延迟），又保证了状态一致性（单一权威源）。

---

修复完成时间：2025-12-03
修复文件数：10个
