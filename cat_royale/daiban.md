***总目标***

整局游戏只有一份“真相”，存在 Host 浏览器里；所有 Client 只是看到这份真相的投影。❓（逻辑已收束到 Host，但客户端缺少移动/塔切换同步，画面仍可能漂移）

具体要达到这些效果：

任何数值变化（血量 / 位置 / 圣水 / 计时 / 游戏结束）都只在 Host 上被“算出来”。

每一次变化，Host 都用 WS 明确告诉所有人：“某某东西现在的状态 = XXX”。

Client 不做“推理”，只做“执行”：收到状态 → 直接覆盖本地 → 播放动画。

不管网络延迟多少，两端看到的最终状态必然一样，差别只在于出现快半拍还是慢半拍。

***目标 1：统一的“游戏真相”状态*** ❓（Host 维护唯一状态，但客户端未接收移动/塔切换广播，B 侧费用与状态未被 Host 严格约束）

为整局对局定义一份清晰的“世界状态”，完全由 Host 控制：

对于每一个棋子，你要能在 Host 这边随时回答：

id / 类型（fighter / shouter / tower / ruler / king_tower…）

所属阵营 a/b

当前坐标（row, col）

当前 HP 与 maxHP

存活与否：isDead / _isDead

正在干什么：是否在攻击、是否在移动、目标 id 等

对整局游戏，还要有：

当前计时器剩余秒数

双方圣水值（a_elixir, b_elixir）

这盘是否已经结束（gameOver + winner）

要求：

这套“真相状态”只存在于 Host。

Client 的任何本地变量都只是“缓存副本”，随时可以被 Host 的广播覆盖。

***目标 2：消息流的责任边界非常明确*** ❓（deploy/ruler 走 Host，但 Host 未做费用/合法性校验；塔切换与能力仍本地执行，无请求/响应链）

把消息分两类，每一类的“谁说了算”要非常清晰：

2.1 玩家 → Host：只包含“意图”，不直接改世界 ❓（deploy/ruler 有请求，但 Host 没有扣费/冷却校验，塔切换/ability 没有请求路径）

客户端允许发送的内容，只是：

“我想在 (row, col) 放一只 fighter” → deploy_request

“我想让 ruler 走一步到 (row, col)” → ruler_move_request

“我点了 ready” → ready

（以后可以有：发表情、投降之类）

要求：

这些 request 本身不会改血、不会动棋子、不会扣圣水。

Host 收到后决定：

合法？（位置、冷却、费用）

如果合法，再在自己的世界状态里做修改，然后再广播给所有人。

2.2 Host → 所有人：只发送“已经发生的事实” ❓（spawn/damage/death/timer 有广播，但移动、塔切换、ability 状态未同步，表现层易漂移）

Host 用 state_update 广播的内容，都是已经判定好的结果，例如：

spawn：已经成功在 (row, col) 生成了一枚 id=xxx 的 fighter

damage：id=xxx 的血量现在是 hp=120 了（之前是多少不重要）

death：id=xxx 的棋子已经死亡

ruler_move：ruler 从 (r1,c1) 移动到了 (r2,c2)

elixir：阵营 a 的圣水现在是 7/10

timer：剩余时间 53 秒

game_over：游戏结束，获胜方是 side = 'a'

要求：

Client 收到这些消息只做一件事：把自己的 UI 改成这一事实，不再反推、再计算。

不允许 Client 再发任何二次推断消息（比如再给服务器回一条 damage）。

***目标 3：伤害 / 血量同步的具体行为*** ✅（applyDamage 仅 Host 执行，damage/death 广播，客户端按广播覆盖 HP）

让你刚才那种“B 端永远不掉血”彻底消失。

3.1 谁在算伤害？✅（攻击逻辑调用在 Host，客户端调用被 applyDamage 拦截）

所有攻击判定、范围检测、塔扫描、子弹命中、近战碰撞等：
只在 Host 上运行。

Client 上的同样逻辑如果还存在：

要么完全停掉（不再开定时器）

要么虽然还跑，但任何尝试改 HP 的地方都被硬挡（你现在 warning 就是干这个）

3.2 每一次伤害的生命周期 ✅（Host 计算→damage 广播→客户端覆盖 HP→HP<=0 调用 handleDeath）

理想流程：

Host 的攻击逻辑判断：某一刻，piece X 击中了 piece Y，期望造成 75 点伤害。

Host 在自己的状态里：

读出 Y 当前 HP

算出新 HP（考虑减伤、上限、不能低于 0）

更新 Y.hp、新 HP 如果 <=0 顺便标记死亡。

更新完之后，Host 立刻广播一条 state_update：

内容：event="damage", piece_id = Y.id, hp = 新 HP，可以附带 damage = 75 之类。

所有 Client 收到这条消息：

直接把本地那枚 Y 的 HP 设置为 新的 HP 值（不再自己计算差值）

如果 HP <= 0 且之前没死，就播放一套死亡动画，移除等。

目标可观测现象：

你在 Host 把 A 塔打到 50 HP，B 很快也会看到 “50” —— 中途可能出现一点点延迟，但最终数字始终相同。

即使 Client 中间误算过几次，只要下一条来自 Host 的 damage 到达，它就会被“打回现实”。

***目标 4：死亡 & Game Over 的同步*** ✅（Host 广播 death/game_over，客户端 handleDeathFromServer 接收）
4.1 单个棋子的死亡 ✅（Host 判定死亡并广播；客户端仅做动画/清理）

要求：

由 Host 决定“这枚棋子死亡的那一刻”：只有 Host 能把它从“活着”改成“死亡”。

Host 做的事情：

停止与它相关的 mover / attack loop

从 Host 的棋盘状态中移除或标记 dead

如果是 King Tower：立刻判输赢，设置 gameOver = true

发出一次 death 的 state_update（或依赖 HP=0 的 damage 也可以）

Client 行为：

收到死亡信号/HP=0 后，最多只做 UI 动画和清理，不再额外做判断。

4.2 Game Over ✅（Host 单次宣布 game_over，客户端弹窗并停交互）

要求：

永远只由 Host 宣布一次：

Host 内部判断“满足胜负条件” → 设置 gameOver = true → 广播 game_over 事件。

Client：

收到 game_over 后，弹出 Game Ends modal，停用所有交互。

不自己决定游戏是否结束。

可视化效果：

全天任何一方的 King Tower 爆掉，两边屏幕最多延迟几十毫秒，但一定都会收到 Game Ends，不会出现“我这边还能继续放子”。

目标 5：圣水 & 计时器的一致性 ❓（计时器由 Host 驱动，但圣水仅维护 side A，B 侧费用未被 Host 记录/同步）
5.1 圣水（Elixir）❓（elixir.js 仅 Host+A 递增并广播 side:'a'，B 侧部署/能力未扣费也未同步）

目标：

圣水值只由 Host 生成和递增（每秒 +1 之类），并写在自己的状态里。

每一次变化，Host 发 state_update: { event: "elixir", side: 'a', elixir: 7 }

Client：

不再本地计时加圣水。

只根据每一条广播直接覆盖自己显示的数字。

期望现象：

即使 Client 暂时卡顿或 tab 后台，回来后也会很快“追上现在正确的圣水值”。

5.2 计时器（Timer）✅（startTimer 仅 Host 跑，timer 事件按秒广播）

目标：

倒计时完全由 Host 驱动，每秒：

内部秒数 -1

发一条 state_update: { event: "timer", seconds_left: 52 }

Client 的时间显示只根据这条消息更新，不再自己 setInterval() 倒数。

期望现象：

多个浏览器打开同一盘棋，时间显示始终同步，不会一个写 0:12 一个写 0:09。

目标 6：B 端攻击 A 也能生效（当前你的痛点）❓（Host 已计算并广播伤害，但客户端未生成移动/攻击驱动，B 端画面静止且缺少位置同步）

你现在最想解决的是这个：

“我把逻辑都移到 Host 上之后，B 端放的兵能打到 A，但是 A 的血不掉 / B 看不到变化。”

要达到的目标状态是：

B 的点击只是“申请攻击”（放子、走 ruler），不直接动 HP；

Host 收到 B 的请求后：

把这枚 B 的兵放在自己的棋盘上

让它进入 Host 的攻击循环 → 参与正常战斗

当这个兵在 Host 上打到 A 的塔 / 子：

A 的 HP 真正在 Host 上减少

Host 广播 damage → 所有人（包括 B）看到 A 掉血

B 的 console 不再出现一堆 [CLIENT should not call applyDamage] 的黄字，
即使有，也只是说明“本地逻辑尝试算过，但没有真正生效”。

换句话说：

“B 能打 A”是因为 Host 替 B 出手了，而不是 B 在自己电脑上“打自己画的塔”。


***目标6*** ability的同步 ❓（塔切换/ability 仅 Host-A 本地执行，未走请求与 state_update，对端看不到切换/减伤）

请确保tower troop的ability，a端b端都同步。尤其是切换塔楼功能，当a端切换，b端也能看到显示；当b端切换，a端也能看到显示。
