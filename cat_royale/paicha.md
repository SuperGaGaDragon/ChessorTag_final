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

***用户端检查修复***

- “对局开始不产圣水”根因：宿主页面覆盖了 `window.elixirManager`，`startElixirGeneration` 前调用 `setElixir` 抛 `is not a function`，后续初始化中断。已在 `game_page/elixir.js` 强制单例化 `window.elixirManager`，避免被父框架污染。
- “卡牌不显示”“塔技能无效”系同一异常导致的初始化中止。圣水实例修复后，`initializeCards()` 正常填充卡槽，`AggressiveTowerAbility/SolidTowerAbility.init` 正常绑定，塔技能可用。


***用户端检查报告***

当前状况：
A 端一切正常；
B 端 状态数据是对的（HP 数值、tower 类型、elixir 都同步），
但是 画面/血条/图标没有跟着变。

这说明：Host → B 的网络链路是通的，问题在 B 端的 UI 应用层。
我们可以把问题压缩成一句话：“B 端收到了事件，但没正确画出来。”

下面我给你一个针对 B 端的排查 Checklist，全部是“目标级描述”，你照着对就行。

1. 确认：B 端确实收到了正确的事件

在 B 端 Console 加一组 log，只在 fromNetwork / state_update 那层打：

damage / hp 相关：

console.log('[B] damage event', payload);


确认：

每次 A 打 tower / 单位，B 端都能看到 {event:"damage", id, hp, max_hp, side}；

hp 数值和 A 端看到的一致（这一点你说“信息同步”应该已经成立）。

elixir / tower_switch / tower_ability 也类似打一行 log。

如果这里没问题，说明：

Host → B 的“数据”没问题，问题一定在“怎么把数据用到 DOM 上”。

2. 查所有「只更新自己 side」的 UI 逻辑

历史遗留里最容易踩坑的一类是这样：

if (side === 'a') {
  // 更新血条 / 塔图标 / 卡牌等
}


或者：

if (payload.side === mySide) {
  updateHealthBar(entry);
}


当时为了只画 A 端，用了 side === 'a' / payload.side === mySide 之类条件，现在 B 也要玩了，这会导致：

状态对象被改了（因为你说 “信息同步”）；

但 UI 更新只在“自己视角/host”的分支下跑，B 端直接 return 了。

你可以在 B 端全局搜索这几个关键词：

if (isHost

if (side === 'a' / if (side !== 'a'

if (payload.side === mySide / if (entry.side === mySide

然后按这个准则处理：

权威逻辑（扣费、移动、生成 movers、attack scan 等）
→ 保留 isHost 限制，只能 Host 做。

UI 逻辑（updateHealthBar、writeHealthBarTitle、updateTowerImage、renderAbility Effect）
→ 不要用 isHost 或 side === mySide 限制，
只要有事件就应该更新对应棋子 / 塔，无论是 A 还是 B。

目标：
“Host only 限制只出现在『修改游戏真相』的代码里，
任何以 DOM / CSS / title / icon 为主的代码都不做 side 过滤（除了决定画在哪边的位置）。”

3. 检查 HP → DOM 的映射是否对 B 也是对的

你现在的血条管线大致是：

收到 snapshot 或 damage：

找到 entry（piece/tower 的本地对象）；

更新 entry.hp；

调 updateHealthBar(entry)；

调 writeHealthBarTitle(entry)。

B 端“信息同步但显示不同步”很可能是：找到的 entry 不是你以为的那个。

重点检查两点：

3.1 entry 查找是不是只查 “自己 side”

例如这种：

const entry = deployedPieces.find(e => e.id === payload.id && e.side === mySide);


如果 Host 用的是 side === 'a'，B 是 'b'，再来一样的查找，就会：

找不到对方单位/塔；

entry 是 undefined，于是根本没更新血条；

但你另一个地方更新了内存 state（比如 piecesById），肉眼以为“数值对了”，DOM 没动。

修正目标：

查找 entry 时只用 唯一 id（+ board 类型），不要再用 side === mySide 限制：

const entry = piecesById[payload.id]; // 或 find(e => e.id === payload.id)


entry.side 只用于决定画在左/右、用哪套皮肤，不影响“是否更新”。

3.2 health bar DOM 是否为双方都构建了

在 syncPieceFromSnapshot / 初始摆塔的时候：

确保 不论 side 是 'a' 还是 'b'，都创建了 health bar 元素，并把它挂在 entry 上；

很多老逻辑可能写成：

if (entry.side === mySide) {
  attachHealthBar(entry);
}


这样 B 进场时，他自己的塔有血条，对手塔压根没 bar，自然就看不到对方掉血。

目标：

attachHealthBar(entry) 对所有棋子/塔都调用；

区别只体现在样式（颜色、位置），而不是“要不要有”。

4. 重点看 snapshot 的「orientation」和「行列」

你 Console 里有一行：

[createBoardGrid] data-row and data-col are ABSOLUTE coordinates (same for both sides)

这说明你现在的棋盘坐标是绝对坐标（a1 在左下，无论 A/B）。

那么要保证：

snapshot 中的 row/col 是绝对坐标；

syncPieceFromSnapshot 在 B 端不要再二次做“翻转”
（比如把 row 反过来），否则：

B 端会把 piece 画到别的位置；

damage 更新按 id 找 entry 可能找到了，但 DOM 显示因为坐标/anchor 错位，看起来“像没动”。

简单说：

坐标只翻转一次，要么在 snapshot 里已经是“观众视角”，要么在前端渲染时翻；
绝不能在 A/B 端各翻一遍。

5. 一套快速验证流程（只做 B 端）

给你一个 1 分钟的验证剧本：

A 当 Host，B 加入，打开 B 的 Console。

在 B 上加一个临时 log：

window.handleDamageFromServer = function(payload) {
  console.log('[B] damage', payload.id, payload.side, payload.hp);
  // 原来更新 entry + updateHealthBar 的逻辑也写这里
}


并确保 fromNetwork 的 damage 分支只调用这一个函数。

A 控制一枚单位持续攻击 B 的塔：

看 Console：每一下 [B] damage ... 都出现；

然后看：

对应塔的 title 是否从 1000/1000 → 900/1000 → ...；

条形血量是否有缩短（如果没有，多半是没调用 updateHealthBar 或找错 entry）。

再让 B 端点技能 / 切塔：

看 ability / switch 事件是否也触发 B 的 UI 更新；

同时确认没有任何只在 isHost 条件内的 UI 逻辑。

处理结果补充：
- 已对 `elixirManager` 做全局单例保护，避免父页面覆盖导致初始化中断，圣水/卡槽/塔技能在 B 端可正常渲染。
- 事件链路（damage/elixir/tower_switch/tower_ability）均在 `state_update` 中无视 side 应用到 DOM，并在快照里携带血条基座、减伤、图片路径，B 端刷新后可同步显示。需要验证时按上述脚本在 B 端 Console 打 log，即可确认 UI 与广播一致。
