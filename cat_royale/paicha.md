***当前问题***
1. B端攻击效果没有显示
2. B端主塔显示有问题，现在B端主塔只占据一格，实则应当占据d1 d2 e1 e2（d7 e7 d8 e8）


***修复方案***
1. B端攻击效果没有显示  
   - HOST端：确认 `piece_deploy.scanTowerAttacks` 在 A 侧正常运行并广播 `tower_attack/tower_attack_stop`（461-482 行），补充日志观察 `postToParent` → WS → CLIENT 的消息链路。  
   - CLIENT端：在 `handleStateUpdate` 的 `tower_attack` 分支中，如果 attacker/target 未就绪则入队等待 spawn/snapshot 后重放，避免直接 `return` 导致动画缺失；同时确保 `attackScanTimer` 在 CLIENT 侧也启动，使用 `visualOnly=true` 兜底触发动画。  
   - 验证：A 端放塔，B 端放兵入射程，Network 面板应看到 `tower_attack`，B 端能看到旋转/弹道。

2. B端主塔只占一格  
   - `registerKingTowers`：生成前清理旧 `.king-anchor`，用绝对坐标 rows=[0,1], cols=[3,4] 计算 `gridRow/gridColumn`（通过 `logicalToGridRow/Col`），并为 B 侧显式注册 4 个 `king_tower` 条目。缺块时在控制台报警。  
   - 样式/阻挡：确认 `.king-anchor` 继续使用 `grid-row/column` 跨 2x2，`isCellBlocked` 覆盖 d7,d8,e7,e8；必要时为 anchor 设置 `grid-area` 明确跨度。  
   - 验证：控制台日志 rows/cols 和 gridRow/Col 均为 4 格，boardPieces 内有 4 条 king_tower 记录，d7/e7/d8/e8 无法部署。
