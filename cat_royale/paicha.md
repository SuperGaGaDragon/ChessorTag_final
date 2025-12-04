问题记录（暂不修复代码）：
1. A 端 aggressive tower 图片仍旧显示异常，未按预期更新。
2. B 端 aggressive tower 常态应显示 aggressive_tower.png，但实际使用了 cooked_aggressive_tower.png。
3. solid tower 的死亡特效未正常播放，击毁后没有出现预期特效表现。
4. B 端释放技能后，A 端与 B 端同时进入冷却，未实现仅 B 端冷却的逻辑。

***原因排查***
- A 端 aggressive tower 贴图没有按阵营切换：右侧切换按钮和能力回落默认用 `../pieces/agressive_tower/aggressive_tower.png`，未按 allegiance 取 `_a` 资源（game_page.html:683-684 及 tower_ability_aggressive 回落逻辑），因此 A 侧一直显示 B 侧贴图。
- B 端 aggressive tower 正常态被渲染成 cooked：死亡处理 `handleAggressiveTowerDeath`（website/cat_royale/moving/pieces_move/aggressive_tower_move.js）把 `boardImagePath`/img.src 持久改成 `cooked_aggressive_tower.png` 并被 serialize 广播，重新开局/切换时没有重置活体贴图，存活状态仍沿用死亡贴图。
- solid tower 死亡特效缺失：远端只收到 death 事件时，如果 entry 已标记 `_isDead` 或 hp 未同步到 0，`pieceDeployment.handleDeath` 会直接返回，`handleSolidTowerDeath` 不执行，DOM 也不会替换成 `cooked_solid_tower.png`/灰度。
- B 端释放 aggressive 技能导致双方冷却：冷却与锁定状态保存在全局 `TowerAbilityState`/`ability2CooldownUntil`，未按 side 区分。`setAbilityLock('aggressiveActive', true)` 让 `canSwitchTowers` 认为能力激活，从而 A、B 两侧按钮同时被禁用/冷却。

***修复方案***
- aggressive tower 贴图选择补齐阵营判断：切换按钮与 ability 回落改用 `towerSpriteFor(..., allegiance)`，payload 中带上 allegiance，避免默认落到 B 侧资源。
- aggressive tower 在复活/重摆/切换形态时统一重置 `boardImagePath` 与 img.src（`aggressive_tower.png`/`_a`），仅在 hp<=0 时写入 cooked，serialize 时也依据当前 hp 选择正常或死亡贴图。
- solid tower death 同步兜底：`handleDeathFromServer` 即便 `_isDead` 已置也强制执行一次 `handleSolidTowerDeath`（或 death 事件携带 board_image_path 并强制覆盖），确保远端能看到 cooked/灰度效果。
- 将 tower ability 锁与冷却按 side 存储与判定（如 `ability2CooldownUntil[side]`、`TowerAbilityState[side].aggressiveActive`），按钮禁用逻辑带 side，避免一方施法占用全局锁导致另一方一并冷却。

***审核批注***
- 当前仅记录问题与方案，仓库未有对应代码修改；四个问题均未修复，需要按上述方案落地。
