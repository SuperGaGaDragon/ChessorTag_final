已完成：
- 客户端画面保持更新：fromNetwork 部署也创建移动器，tower 扫描/攻击动画在客户端开启；攻击函数去掉 HOST 限制，客户端运行动画但伤害仍仅由 Host 计算与广播。
- 血条悬浮提示修复：health bar 统一写入 title，并在 HP 变化后刷新，客户端悬浮可看到 “当前/最大”。//

未完成 / 风险：
- Elixir 仍仅维护 side a，Host 未对 deploy/ruler/ability 做扣费/冷却校验，B 侧可能免费操作且不广播 elixir。
- 移动仍为本地模拟，未有 Host → 客户端的权威位置广播，极端情况下可能与 Host 路径分叉（虽 HP 会被广播纠正战斗结果）。
- 塔切换/ability 依旧本地执行，无请求-响应链，对端仍看不到切换或减伤状态。

***修复计划书***

- Host 统一圣水：在 Host 状态中维护 a_elixir/b_elixir，客户端仅显示广播；deploy/ruler/ability request 全部由 Host 校验费用/冷却并扣费后再广播 state_update: {event:"elixir", side, elixir}；补上 B 侧圣水递增定时与持久化，客户端本地加圣水逻辑移除。
- 权威移动同步：ruler_move/troop mover 只在 Host 运行并每步广播位置；客户端停掉自算坐标，收到广播直接覆盖显示；补充对 host_offline/backfill 的初始位置快照，避免路径漂移。
- 塔切换与能力请求链：tower ability/switch 改为 Client→Host request，Host 校验费用/冷却/目标合法后修改状态并广播 ability/switch 事件（含当前模式/减伤剩余时间）；客户端只渲染广播结果且播放动画。
- 回归与验证：
  - 双端放兵、切塔、放技能时，Host 日志出现 request→state_update 且 elixir 正确扣减；B 侧操作能看到 A 侧画面同步变化。
  - 断线/重连：新加入的客户端能收到当前 elixir/能力模式/棋子坐标的完整快照。
  - 性能与保护：为重复 request 加去抖/幂等 id，防止多次扣费；添加最小 e2e 场景回放用例（双端对战 30s）验证圣水/移动/能力同步。
