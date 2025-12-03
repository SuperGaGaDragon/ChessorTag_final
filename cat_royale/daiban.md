目标：
让本游戏A为Host，B为Client，是A的Host Authority。

现在情况：这个迁移计划完成了一些，但是更多没完成，所以说现在这个一些地方比如说client被挡了，但是host又没有执行。你要扫描这些问题，然后进行解决。如下的计划书仅供参考！仅供参考！仅供参考！请你根据实际情况，现在已经改的情况，在最小化代码改动的情况下完成。

完成后，请把本地的一些功能和云端的核对，确保本地的比如说ability，比如说功能，和a端b端都是一致的。

Cat Royale 战斗系统：逻辑迁移计划书（Plan Document）
🎯 目标（Goal）

将当前分散在所有浏览器上的战斗逻辑，统一迁移到 Host 端（权威端, authoritative host） 执行，实现：

战斗同步一致性 100%（no desync）

客户端不再拥有任何逻辑权力（不能随便 deploy/attack/damage）

所有攻击、移动、血量、死亡、游戏结束都由 Host 决定并同步

B 客户端可以正常进攻 A（Host 代替 B 执行所有攻击）

为未来**迁移到服务器（Headless Host 模式）**做好架构

最终效果：

A 端是唯一的「游戏模拟器」
B 端只是纯展示（viewer）+ 输入（intent）
服务器只负责“转发消息，不做逻辑”

这是 Clash Royale、Brawl Stars 以及大部分实时 PvP 游戏的标准做法。

📌 当前情况（Realistic Current State）

下面是你当前系统的真实结构（基于你给的日志 + 我分析出的架构）：

✔ 1. 服务器不参与计算

battle_ws.py 只做转发，不做验证、不算 HP、不判断死亡、不判胜负

✔ 2. A（Host）和 B（Client）都在执行自己的战斗逻辑

表现为：

每一端都在跑 tower scan attack

每一端都在跑移动 movers

每一端都在尝试调用 applyDamage

你刚刚把 B 的 applyDamage 禁了，所以 B 打不了 A。

✔ 3. B 的棋子有时由 B 自己生成（双 spawn）

导致：

B 的棋子没有注册到 host 的 tower_scan 或移动管理器

host 根本不知道有这枚 B 的棋子

B 看见自己有攻击，但 host 看不到 → B 打不动 host

✔ 4. ruler_move_request 没有在 host 层验证

所以：

ruler 移动在 B 端自己跑 → 同步错误

elixir 在 B 自己扣 → 不一致

host 不知道 B 的 ruler 走到了哪里

✔ 5. death/game_over 只在本地触发，无网络同步

造成：

A 看到 game over，但 B 继续玩自己那套 local 动画

或 B 看到 A 死了但 host 不知道 → 永远不会结束

✔ 总结：现在是「双模拟器」模式

Host 和 Client 都在模拟游戏 → desync 是必然。

我们要改成“只有 Host 模拟，Client 只显示”。

🧭 大计划（Master Plan）

目标是一句话：

把所有游戏逻辑从浏览器的每个端 → 收拢到 Host 浏览器唯一运行。Client 只负责输入、展示，不准自己算逻辑。

整个计划分 3 个阶段：

Phase 1：Host 权威化（Authoritative Host）💎（当前阶段）

让 Host 成为唯一“游戏引擎”，Client 完全不算逻辑。

内容包括：

所有棋子只由 Host deployPiece() 创建

所有攻击只在 Host 执行

所有 applyDamage 只在 Host 执行

所有死亡只在 Host 触发

所有 game_over 只在 Host 判断

Client 端完全不执行任何 mover/tower/attack 逻辑

Phase 2：Host → 所有人同步（State Replication）💠

在 Host 执行完动作后：

HP、死亡、spawn、移动、timer、elixir
→ 全都用 state_update 广播出去
→ 所有人根据 state_update 来刷新 UI

这就是“client-side visual / host-side simulation architecture”的典型做法。

Step 1：禁止 Client 在本地 deployPiece
要实现：

B 点击格子时，本地不能生成棋子

只允许 Host 生成棋子（通过 state_update: spawn）

方法：

在 deployPiece() 顶部加：

if (!opts.fromNetwork && window.IS_HOST !== true) {
  console.warn("Client should not deploy locally");
  return;
}


完成标志：

B 点击不会本地下子

Host 会收到 deploy_request

Host 会下子

B 端只会收到 spawn → fromNetwork:true → 创建棋子

Step 2：禁止 Client 执行攻击/移动逻辑

所有攻击循环加：

if (!window.IS_HOST) return;


包括：

scanTowerAttacks

startShouterAttack

startFighterMove

startRulerMove

squirmer_attack

aggressive_tower_attack

solid_tower_attack

完成标志：

B 的 attack interval 不再运行

B 的控制台不会出现 "CLIENT should not call applyDamage"

Step 3：让 Host 执行所有棋子的攻击

检查：

B 的棋子是否真的在 Host 的 boardPieces 数组里

Host 有注册 B 这枚棋子的 mover/tower attack timer

Host 能检测到敌方棋子并打出伤害

完成标志：

B 的棋子可以打动 A 的塔（Host 模拟）

A 的塔可以打击 B 的棋子（Host 模拟）

Step 4：applyDamage → state_update

Host 扣血后：

postToParent('state_update', {
  event: 'damage',
  piece_id,
  hp
});


完成标志：

Client 端不会再调用 applyDamage

Client 端用 applyDamageFromServer 同步血量

Step 5：handleDeath → state_update

Host 死亡后：

postToParent('state_update', {
  event: 'death',
  piece_id
});


Client：

case 'death': handleDeathFromServer(...)


完成标志：

两端看到一致的死亡

不存在一端死、一端活的问题

Step 6：统一 Game Over

Host 执行：

postToParent('state_update', {event:'game_over', winner:'a'});
battleSocket.close();


Client：

case 'game_over':
  showGameOverScreen();
  disableAllInput();


完成标志：

双端同步结束，游戏不再继续发 WS 消息

不会出现“一端还在玩”的情况

Step 7（可选）：统一 ruler_move_request 逻辑

Host 接收 B 的路径请求

Host 执行合法性校验

Host 自己移动 ruler

Host 发 state_update: ruler_move

完成标志：

双端的 ruler 完全一致

elixir 消耗始终一致

🧨 最终总结（一句话）

你现在的问题就是：B 的攻击和 deploy 在自己的本地算了，但 Host 不知道 → Host 不帮 B 打伤害 → B 伤害无效。

你需要的不是修 bug，而是：

把所有战斗逻辑从 “多客户端执行” 合并到 “Host 端唯一执行”。

## 行动清单（基于当前代码）

- 阻断 Client 本地下子：`website/cat_royale/piece_deploy/piece_deploy.js` 的 `deployPiece` 顶部增加 `if (!fromNetwork && window.IS_HOST !== true) return { requested: true };`，只让 `handleLocalDeployRequest` 走网络；确保 `fromNetwork` 生成的棋子带 `skipElixir`。
- 只在 Host 跑攻击/巡检：`scanTowerAttacks` 计时器创建前加 `if (window.IS_HOST !== true) return;`；`startAggressiveTowerAttack`、`startSolidTowerAttack`、`startShouterAttack`、其他攻击/移动计时函数都加 `if (window.IS_HOST !== true) return;`，防止 B 自己扣血。
- 统一伤害广播：`applyDamage` 仍只允许运行在 Host，确认每次扣血必发送 `state_update damage`；客户端只用 `applyDamageFromServer` 更新血条。
- 统一死亡广播：`handleDeath` 仅 Host 调用时发送 `state_update death`；客户端通过 `handleDeathFromServer` 落地，避免双侧不同步。
- Ruler 移动权威：在 `website/cat_royale/game_page/index.js` 的 parent bridge 增加 `ruler_move_request` 处理，Host 验证后本地移动并广播 `state_update`（客户端忽略本地扣 elixir）；在 `ruler_move.js` 开头加 `if (window.IS_HOST !== true) return;` 防止 B 自己走。
- 计时与资源：`startTimer`、`elixir` 只由 Host 变更并通过 `state_update timer/elixir` 下发，客户端不自增；必要时在 ElixirManager 启动前判断 `window.IS_HOST`。
- Game Over 同步：Host 在王塔死亡后发送 `state_update game_over` 并关闭 WS；客户端收到后禁用输入/提示结果。
- 核对资产与能力：对照本地与线上静态资源/ability 脚本，确保双方加载同一版本（`pieces_ability/*`, `moving/*`）；如有新增能力，Host 执行逻辑，Client 仅显示。

