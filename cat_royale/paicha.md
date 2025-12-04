已完成：
- 客户端画面保持更新：fromNetwork 部署也创建移动器，tower 扫描/攻击动画在客户端开启；攻击函数去掉 HOST 限制，客户端运行动画但伤害仍仅由 Host 计算与广播。
- 血条悬浮提示修复：health bar 统一写入 title，并在 HP 变化后刷新，客户端悬浮可看到 “当前/最大”。

未完成 / 风险：
- Elixir 仍仅维护 side a，Host 未对 deploy/ruler/ability 做扣费/冷却校验，B 侧可能免费操作且不广播 elixir。
- 移动仍为本地模拟，未有 Host → 客户端的权威位置广播，极端情况下可能与 Host 路径分叉（虽 HP 会被广播纠正战斗结果）。
- 塔切换/ability 依旧本地执行，无请求-响应链，对端仍看不到切换或减伤状态。

***修复计划书***

目标：消除三项风险（圣水仅管 A、移动漂移、塔切换/能力不同步），由 Host 持有唯一真相，Client 只渲染广播事实，确保 B 端血条与战场状态完全一致。

交付物：
- Host 权威：圣水、移动、塔模式/技能的请求-校验-广播链路。
- 快照：进入/重连时，提供 elixir、棋子坐标、塔模式/减伤、血条标题的全量快照。
- 客户端：去掉本地模拟/扣费，改为渲染广播并重建 UI（含 health bar）。
- 验收脚本：30s 双端对局回放，校验扣费、位置、技能、血条同步。

工作拆解与责任：
- 圣水权威（Owner: backend）
  - `elixir.js`：Host 维护 `a_elixir/b_elixir`（含上限、加速），定时递增并广播 `{event:"elixir", side, elixir}`。
  - Host 校验 deploy/ruler/ability 费用与冷却，合法扣费广播，非法返回 err code；客户端移除本地加圣水。
  - 新增 B 侧初始 elixir 推送 + 断线重连 elixir 快照。
- 权威移动同步（Owner: moving）
  - mover/ruler 仅在 Host 跑；按步广播 `{event:"ruler_move"/"move", id, row, col, tick}`。
  - 客户端停本地坐标模拟，收到广播直接覆盖；进入/重连请求全量棋子坐标快照。
  - death/game_over：Host 停止 mover 并广播终态，客户端只做动画清理。
- 塔切换/能力请求链（Owner: tower）
  - Client→Host request 携带 `tower_id、mode/skill、cost、cooldown_token`。
  - Host 校验费用/冷却/目标，成功扣费并广播 `{event:"tower_switch"/"ability", tower_id, mode/skill, expire_at, side}`；失败回 err code。
  - 客户端不本地切换/减伤，只渲染广播；塔模式/减伤剩余写入快照。
- B 端血条修复（Owner: UI/WS）
  - damage state_update 统一走 `handleDamageFromServer`：覆盖 hp、调用 `updateHealthBar` + `writeHealthBarTitle`（当前/最大），禁用本地 `applyDamage` 改血。
  - 进入/重连后按棋子快照重建 health bar DOM + title，确保 UI 有基座。
  - 关闭客户端本地伤害/战斗循环，只渲染 Host 广播；增加 WS 日志/回放验证血条掉血。

回归与验收：
- 功能：双端放兵、走 ruler、切塔、放技能，Host 日志出现 request→state_update，elixir 正确扣减，双方画面同步。
- 断线重连：刷新后立即拿到 elixir/棋子坐标/塔模式/血条快照，继续广播无漂移。
- 异常防护：重复 request 幂等/去抖；非法费用/冷却返回明确 err code；game_over 后拒绝新 request。
- e2e：录制 30s 双端回放，验证圣水曲线、移动、能力、血条同步。


- Step1：圣水双侧维护与扣费校验，移除客户端加圣水。
- Step2：权威移动广播、客户端覆盖与快照。
- Step3：塔切换/能力请求链与广播。
- Step4：血条修复收尾、断线重连回归、自测脚本。

***核对审查***

- [Step1 圣水权威] `game_page/elixir.js` 现已维护双侧池并只在 HOST 侧计时广播，`deploy_request`/`ruler_move_request` 都会走 `elixirManager.spend` 校验与扣费，匹配计划。但塔能力仍未接入：`pieces_ability/solid_tower_ability.js:76-152` 完全免费，且广播时把 `side` 硬编码为 `a`，远端会收到错误圣水同步；`pieces_ability/aggressive_tower_ability.js:255-266` 仅本地扣 1 费，未做冷却令牌/err code，缺乏请求-响应链。
- [Step2 移动权威] mover 构造仅在 `window.IS_HOST===true` 执行（`piece_deploy.js:685-725`），`movePiece` 在 HOST 时广播 `state_update`，客户端通过事件覆盖坐标；`beginMatch` 非 HOST 会主动 `snapshot_request`。该风险基本消除。
- [Step3 塔切换/能力同步] 切换模式走请求链并扣 1 费（`game_page.html:1068-1140` + `aggressive_tower_ability.js:185-210`），符合计划。但两条能力链缺失：Solid 及 Aggressive 2 均为 HOST 本地触发，未校验请求端、未广播 err code/冷却令牌，Aggressive 2 也未向客户端广播减伤/形态，仅靠移动广播位置，视觉与状态不同步。
- [Step4 血条/快照] `handleStateUpdate('damage')` 落地到 `applyDamageFromServer` 并强制刷 `healthBar.title`，快照含棋子坐标与 elixir（`game_page.html:1179-1233`）。但快照未包含塔能力/减伤状态，重连后能力形态会丢失，仍需补充。
- 重大缺陷：`aggressive_tower_ability.js:255` 处在声明 `playerAllegiance` 之前调用，Enter 触发会直接抛 `ReferenceError`，导致能力 2 失效并阻断后续逻辑；需立即修复并补同步广播。

***本轮整改核对***

- 已修复 Aggressive 2 的 `playerAllegiance` 未定义崩溃，提取为 `runAggressiveAbility2` 并加 cooldown 保护。
- 塔技能现走 Host 权威扣费与请求链：非 Host 触发会发送 `tower_ability_solid/aggressive_request`，Host 校验 `elixirManager.spend`，不足会广播 `error: elixir_insufficient`；Solid 费用 1，Aggressive 2 费用 2。
- 能力广播补齐：Host 启动 Solid 会广播 `tower_ability_solid`（含 side/targets/duration），Aggressive 2 会广播 `tower_ability_aggressive`（含位移/减伤/形态），客户端渲染并按 duration 回滚。
- 快照增强：`serializePiece` 加入 `board_image_path` 与 `damage_reduction`，`applySnapshot` 覆盖图片与减伤，重连保留能力形态/减伤。
- 遗留：Aggressive 2 的 cooldown/降伤状态未传 cooldown token，仅用本地计时，若多端重复请求可能需要服务端去抖；Solid/Aggressive 2 仍未单独广播冷却时间或拒绝原因外的其他 err code。
