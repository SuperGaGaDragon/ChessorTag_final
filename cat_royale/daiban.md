改动点1: 

1. 为什么 B 端每个棋子 spawn 会打印两次？

看 B 端这一段（CLIENT）：

[piece_deploy] deployPiece called {... fromNetwork: false}
[piece_deploy] CLIENT mode: calling handleLocalDeployRequest
[game_page] postToParent called {type: 'deploy_request' ...}
[PAGE → WS] sending deploy_request {...}

# 之后从 WS 收到服务器广播：
[battle] WS message {"type":"state_update","event":"spawn","piece":{...}}
[piece_deploy] deployPiece called {... fromNetwork: true}
Deployed shouter (b) at row 0, col 6

# 马上又来一条一模一样的：
[battle] WS message {"type":"state_update","event":"spawn","piece":{...}}
[piece_deploy] deployPiece called {... fromNetwork: true}
Deployed shouter (b) at row 0, col 6


说明什么？
服务器对同一次部署收到了两次几乎完全一样的 state_update: spawn，所以它忠实地转发了两次。

回头看 A 端（HOST）的 log，恰好印证了这一点：

[battle] WS message {"type":"deploy_request", ...}

piece_deploy.js:474 deployPiece called {... fromNetwork: false}
piece_deploy.js:491 HOST mode: will deploy and broadcast
piece_deploy.js:610 HOST mode: calling handleLocalDeploy
game_page:1406 handleLocalDeploy called {...} IS_HOST: true

game_page:1418 [game_page] sending state_update
game_page:710 postToParent called {type: 'state_update', ...}   ← 第一次
game_page:712 sending postMessage to parent

piece_deploy.js:633 Deployed shouter (b) at row 0, col 6

game_page:710 postToParent called {type: 'state_update', ...}   ← 第二次
game_page:712 sending postMessage to parent


也就是说：

handleLocalDeploy() 里 先 postToParent 一次（比如“spawn 某个 piece”）。

部署完（Deployed shouter）后，又再调用了一次 postToParent(...)，再次发同一个 state_update。

所以：服务器 → B 端 = 两条完全一样的 spawn。

建议改法（思路）

在 game_page.js 里找到 handleLocalDeploy 这一段，大概长这样：

function handleLocalDeploy(entry) {
    // ...
    postToParent({
        type: 'state_update',
        payload: { event: 'spawn', piece: entry }
    });

    // some code that eventually again calls postToParent(...) with the SAME payload
}


你需要保证：每次“真正的落子”只发一次 spawn 的 state_update。

比较安全的做法：

在 handleLocalDeploy 里发 一次 完整的 spawn update；

不要再在其他地方（比如 deployPiece 或 onPieceDeployed）对同一落子重复调用 postToParent。

伪代码参考（改成“只在这里广播一次”）：

function handleLocalDeploy(entry) {
    console.log('[game_page] handleLocalDeploy called', entry, 'IS_HOST:', IS_HOST);

    // 真正更新本地棋盘状态
    placePieceOnBoard(entry);

    // 只在这里广播一次
    if (IS_HOST && hasParentBridge) {
        postToParent({
            type: 'state_update',
            payload: {
                event: 'spawn',
                piece: {
                    id: entry.id,
                    owner: entry.allegiance,
                    kind: entry.pieceType,
                    row: entry.position.row,
                    col: entry.position.col,
                    hp: entry.hp,
                    max_hp: entry.maxHp,
                    boardImagePath: entry.boardImagePath,
                }
            }
        });
    }
}


同时检查：

在 deployPiece({ fromNetwork: true }) 的路径里 不要再调用 postToParent，只做本地落子即可。


改动点2： 

为什么 Game over: King tower destroyed 会刷到 252 次？

你在 console 里看到的是这种东西：

4piece_deploy.js:231 Game over: King tower destroyed
16piece_deploy.js:231 Game over: King tower destroyed
76piece_deploy.js:231 Game over: King tower destroyed
252piece_deploy.js:231 Game over: King tower destroyed


Chrome 的意思是：同一行 log 已经重复输出了 4 / 16 / 76 / 252 次。

说明你的 “检测游戏是否结束”的逻辑在不停地被触发，而且每次都没有被“终止”。

最可能的结构是类似这样：

checkForGameOver() {
    if (kingTower.hp <= 0) {
        console.log('Game over: King tower destroyed');
        this.handleGameOver(...);
    }
}


这段函数被谁调用？

很可能是 每一帧移动 / 每一次攻击 / 每个定时器 tick 都会调用一次 checkForGameOver()。

塔一旦爆了，hp 就一直 ≤0，所以之后每个 tick 都命中条件，于是无穷打印。

建议改法：加一个 gameOver flag

在 PieceDeployment 里加一个标记：

class PieceDeployment {
    constructor() {
        // ...
        this.gameOver = false;
    }

    checkForGameOver() {
        if (this.gameOver) return;  // 已经结束了就直接返回

        if (kingTower.hp <= 0) {
            this.gameOver = true;
            console.log('Game over: King tower destroyed');
            this.handleGameOver(/* winner or loser info */);
        }
    }
}


同样在任何可能再次触发 game over 的入口（比如定时器、碰撞检测）开头也可以加：

if (this.gameOver) return;


这样就会：

只打印一次 Game over；

不会重复弹出 overlay / 重复 reset 之类的奇怪效果。

3. 为什么 Game Over 了计时器还在走到 0？

看 HOST 端的 log，King tower 已经 destroyed 了，但还在疯狂：

76piece_deploy.js:231 Game over: King tower destroyed
...
[state_update, event: 'timer', seconds_left: 19]
[state_update, event: 'timer', seconds_left: 18]
...
直到 0


这说明现在的架构是：

计时器完全由 HOST 驱动：
game_page 每秒 postToParent({ type: 'state_update', event: 'timer', seconds_left: ... })。

服务器只是把 timer 的 state_update 按原样广播给双方。

但在 Game over 的时候，你没有停止 host 这边的计时器 / 游戏循环。

建议改法（最小修改版本）

在 HOST 的 handleGameOver 里：

清掉本地定时器（elixir + timer），比如：

function handleGameOver(result) {
    if (this.gameOver) return;
    this.gameOver = true;

    // 1) 停止本地计时器和 elixir
    stopTimerLoop();
    stopElixirGeneration();

    // 2) 通知服务器
    if (IS_HOST && window.battleSocket && battleSocket.readyState === WebSocket.OPEN) {
        battleSocket.send(JSON.stringify({
            type: 'state_update',
            event: 'game_over',
            result, // winner / loser / scores
        }));
    }

    // 3) 本地 UI 处理
    showGameOverOverlay(result);
}


在服务器那边的 battle 逻辑里：

收到 event: 'game_over' 后，把当前 game 状态打成 finished；

停止继续处理 timer（如果服务器有 timer loop，就停掉；如果完全是 host 驱动，那至少不要再把 host 传上来的 timer 往其他人广播）。

在 CLIENT 端的 onMessage 里加一个 case：

case 'state_update':
    if (data.event === 'game_over') {
        pieceDeployment.handleGameOverFromNetwork(data.result);
        break;
    }
    // 其他 event 正常处理
    break;


这样效果就是：

一旦 game over，host 停止发送 timer，server 停止广播。

双方页面都会收到一次 game_over，本地各自处理 UI，不再有计时 spam。

改动点3：

把本地的一些 function 也挂到 socket 上（比如 ability 等）

现状问题：

目前很多游戏逻辑（比如释放技能、攻击判定等）可能分散在 HOST 和 CLIENT 两端，或者完全依赖 HOST 端执行后再广播结果。这导致：

- 代码重复，维护困难
- CLIENT 端可能需要等待网络延迟才能看到效果
- 不同端的逻辑容易不一致

改进思路：

将关键的游戏逻辑函数统一挂载到 WebSocket 消息处理流程上，让：

1. HOST 端执行逻辑 + 广播结果
2. CLIENT 端直接根据广播消息同步状态

主要需要处理的功能模块：

### 1. 技能系统（Abilities）

当前可能的结构：
```javascript
// 在 piece_deploy.js 或 abilities.js 里
function useAbility(pieceId, abilityType, target) {
    // 本地执行技能效果
    applyAbilityEffect(pieceId, abilityType, target);

    // 如果是 HOST，可能会发送一个 state_update
    if (IS_HOST) {
        postToParent({
            type: 'state_update',
            event: 'ability_used',
            payload: { pieceId, abilityType, target, result: ... }
        });
    }
}
```

建议改为统一的消息驱动：

```javascript
// HOST 端：
function handleAbilityRequest(pieceId, abilityType, target) {
    // 1) 验证合法性（是否有足够资源、CD 等）
    if (!canUseAbility(pieceId, abilityType)) {
        return;
    }

    // 2) 执行本地效果
    const result = applyAbilityEffect(pieceId, abilityType, target);

    // 3) 广播给所有人（包括自己）
    if (IS_HOST && hasParentBridge) {
        postToParent({
            type: 'state_update',
            event: 'ability_used',
            payload: {
                pieceId,
                abilityType,
                target,
                result,
                timestamp: Date.now()
            }
        });
    }
}

// CLIENT 端：
function handleAbilityFromNetwork(data) {
    const { pieceId, abilityType, target, result } = data.payload;

    // 只根据 HOST 传来的结果同步本地状态
    applyAbilityEffect(pieceId, abilityType, target, result);
}
```

### 2. 攻击系统（Attack/Damage）

类似地，攻击判定也应该统一：

```javascript
// HOST 端在每次攻击触发时：
function handlePieceAttack(attackerId, targetId) {
    const damage = calculateDamage(attackerId, targetId);
    const target = getPieceById(targetId);
    target.hp -= damage;

    // 广播攻击事件
    postToParent({
        type: 'state_update',
        event: 'attack',
        payload: {
            attackerId,
            targetId,
            damage,
            targetHp: target.hp
        }
    });

    // 如果目标死亡，同时发送 death 事件
    if (target.hp <= 0) {
        handlePieceDeath(targetId);
    }
}

// CLIENT 端：
case 'attack':
    const attacker = getPieceById(data.payload.attackerId);
    const target = getPieceById(data.payload.targetId);

    // 播放攻击动画
    playAttackAnimation(attacker, target);

    // 同步 HP
    target.hp = data.payload.targetHp;
    updateHealthBar(target);
    break;
```

### 3. 移动系统（Movement）

如果棋子有自动移动逻辑：

```javascript
// HOST 端：
function updatePieceMovement(piece) {
    const newPos = calculateNewPosition(piece);
    piece.position = newPos;

    postToParent({
        type: 'state_update',
        event: 'move',
        payload: {
            pieceId: piece.id,
            fromRow: piece.position.row,
            fromCol: piece.position.col,
            toRow: newPos.row,
            toCol: newPos.col
        }
    });
}

// CLIENT 端：
case 'move':
    const piece = getPieceById(data.payload.pieceId);
    movePieceWithAnimation(piece, data.payload.toRow, data.payload.toCol);
    break;
```

### 4. 资源系统（Elixir）

```javascript
// HOST 端定时生成：
function generateElixir() {
    playerAElixir += ELIXIR_PER_TICK;
    playerBElixir += ELIXIR_PER_TICK;

    postToParent({
        type: 'state_update',
        event: 'elixir_update',
        payload: {
            playerA: playerAElixir,
            playerB: playerBElixir
        }
    });
}

// CLIENT 端：
case 'elixir_update':
    updateElixirDisplay(data.payload.playerA, data.payload.playerB);
    break;
```

### 统一的消息处理架构

在 `game_page.js` 里建立统一的消息分发机制：

```javascript
// 接收来自 parent 的 WebSocket 消息
window.addEventListener('message', (e) => {
    if (e.data.type === 'state_update') {
        handleStateUpdate(e.data.event, e.data.payload);
    }
});

function handleStateUpdate(event, payload) {
    switch (event) {
        case 'spawn':
            pieceDeployment.deployPiece({ ...payload, fromNetwork: true });
            break;
        case 'ability_used':
            pieceDeployment.handleAbilityFromNetwork(payload);
            break;
        case 'attack':
            pieceDeployment.handleAttackFromNetwork(payload);
            break;
        case 'move':
            pieceDeployment.handleMoveFromNetwork(payload);
            break;
        case 'elixir_update':
            updateElixirDisplay(payload.playerA, payload.playerB);
            break;
        case 'timer':
            updateTimerDisplay(payload.seconds_left);
            break;
        case 'game_over':
            pieceDeployment.handleGameOverFromNetwork(payload);
            break;
        default:
            console.warn('[game_page] Unknown state_update event:', event);
    }
}
```

### 好处：

1. **单一数据源**：所有状态变更都由 HOST 发起并广播，CLIENT 只负责渲染
2. **易于调试**：所有网络消息都有明确的 event 类型，方便追踪
3. **减少重复代码**：不需要在 HOST 和 CLIENT 分别写两套逻辑
4. **状态一致性**：CLIENT 永远跟随 HOST 的状态，不会出现不同步

### 注意事项：

- 所有游戏逻辑判定（伤害计算、CD 检查、资源消耗等）只在 HOST 端执行
- CLIENT 端只做"表现层"工作：播放动画、更新 UI、响应玩家输入（输入后通过 WebSocket 发给 HOST 处理）
- 确保每个 state_update 都有唯一的 event 名称，避免混淆
- 在 HOST 端加上防作弊检查（比如玩家是否真的有足够 elixir 来部署棋子）

---

总结：

以上三个改动点的核心思路都是：

1. **避免重复逻辑**：在 HOST 和 CLIENT 之间明确分工
2. **统一消息格式**：所有状态变更都通过 `state_update` + `event` 的形式广播
3. **防止重复触发**：加 flag（如 `gameOver`）或合并重复的 postToParent 调用
4. **及时清理资源**：游戏结束时停止定时器、清空事件监听等

这样才能保证双端状态一致、log 清晰、没有奇怪的重复或竞争问题。