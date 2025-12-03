# 卡牌死亡两端不同步问题分析

## 问题现状

在当前的架构中，卡牌死亡时可能出现两端不同步的情况。具体表现为：
- HOST 端显示卡牌已死亡（消失或停止移动）
- CLIENT 端卡牌仍然存活并继续移动/攻击
- 或者相反：CLIENT 端看到卡牌死亡，但 HOST 端仍在运行

## 根本原因分析

### 1. 伤害计算完全在本地执行

查看代码发现，所有的 `applyDamage` 调用都是在**本地**执行的：

```javascript
// piece_deploy.js:166
applyDamage(targetEntry, amount, attacker = null) {
    // 本地计算伤害
    const effectiveAmount = Math.max(0, amount * (1 - reduction));
    // 本地更新 HP
    this.updateHealth(targetEntry, (targetEntry.hp ?? targetEntry.maxHP ?? 0) - effectiveAmount);
}

// piece_deploy.js:144
updateHealth(entry, newHP) {
    entry.hp = Math.max(0, Math.min(newHP, entry.maxHP));
    if (entry.hp <= 0) {
        this.handleDeath(entry);  // 本地触发死亡
    }
}
```

各个攻击模块也都是直接调用本地的 `applyDamage`：

- `shouter_attack.js:45`: `window.pieceDeployment.applyDamage(target, 75, shouter)`
- `fighter_move.js:52`: `window.pieceDeployment.applyDamage(target, ATTACK_DAMAGE, attacker)`
- `aggressive_tower_attack.js:53`: `window.pieceDeployment.applyDamage(target, DAMAGE, attacker)`
- `solid_tower_attack.js:53`: `window.pieceDeployment.applyDamage(target, DAMAGE, attacker)`
- `ruler_attack.js:45`: `window.pieceDeployment.applyDamage(target, DAMAGE, attacker)`

### 2. 死亡事件没有通过网络同步

当前 `handleDeath` 函数只做本地处理：

```javascript
// piece_deploy.js:195
handleDeath(entry) {
    entry.attack = false;
    entry.shouter_lived = false;  // 本地标记
    entry.aggressive_tower_lived = false;

    // 调用本地死亡处理函数
    if (entry.type === 'shouter') {
        window.handleShouterDeath(entry, this.activeMovers[entry.id]);
    }
    // ... 其他棋子类型

    // ⚠️ 没有发送网络消息！
}
```

### 3. state_update 中没有 death 事件

查看 `game_page.html` 中的 `handleStateUpdate` 函数：

```javascript
// game_page.html:958
function handleStateUpdate(msg) {
    const event = msg.event;
    switch (event) {
        case 'spawn':
            spawnPieceFromServer(msg.piece);
            break;
        case 'damage':
            applyDamageFromServer(msg.piece_id, msg.hp);
            break;
        case 'elixir':
            setElixir(msg.side, msg.elixir);
            break;
        case 'timer':
            updateTimerDisplay(msg.seconds_left);
            break;
        // ⚠️ 没有 'death' case！
        default:
            break;
    }
}
```

虽然有 `damage` 事件，但：
1. 没有看到在攻击时主动广播 `damage` 事件
2. CLIENT 端收到 `damage` 事件时，会调用 `updateHealth`，理论上 HP 为 0 会触发死亡
3. **但问题是**：如果 HOST 和 CLIENT 两边的攻击逻辑同时运行，可能产生竞态条件

### 4. HOST 和 CLIENT 都在运行攻击逻辑

关键问题：**攻击判定和伤害计算在两端都在执行！**

- HOST 端：塔攻击 → 本地 `applyDamage` → 本地 `handleDeath`
- CLIENT 端：同样的塔在攻击 → 同样本地 `applyDamage` → 本地 `handleDeath`

这导致：
- 两端的攻击时机可能不一致（网络延迟、定时器偏差）
- 两端计算的 HP 可能不一致
- 某一端先触发死亡，另一端可能还在攻击

## 不同步的具体场景

### 场景 1：HOST 端先判定死亡

```
时间线：
t=0: HOST 端塔攻击，目标 HP 100 → 25 (CLIENT 还在 100)
t=50ms: CLIENT 收到 damage 事件 (如果有广播的话)，HP 100 → 25
t=100ms: HOST 端再次攻击，目标 HP 25 → 0，触发 handleDeath
         - 本地停止移动器
         - 本地移除元素或标记死亡
t=150ms: CLIENT 端的攻击定时器触发，但目标在 CLIENT 看来还是 HP 25
         - CLIENT 继续攻击本地的目标
         - CLIENT 端 HP 25 → 0，CLIENT 端也触发死亡
         - 但可能已经晚了几百毫秒，看起来"多活了一会儿"
```

### 场景 2：CLIENT 端棋子攻击塔，但 HOST 没收到

```
CLIENT 端：
- 棋子移动到塔附近
- 开始攻击，本地 applyDamage
- 塔 HP 逐渐降低

HOST 端：
- 如果 CLIENT 的攻击没有通过网络同步
- HOST 端塔仍然是满血
- 最终 CLIENT 看到塔爆了，HOST 看到塔还在
```

### 场景 3：网络消息丢失或延迟

```
HOST 广播了 damage 事件，但：
- 消息在网络中延迟
- CLIENT 收到时已经晚了几秒
- CLIENT 看到的 HP 变化和动画不连贯
```

## 解决方案

### 核心原则

**所有游戏逻辑判定只在 HOST 端执行，CLIENT 端只做表现层同步**

### 方案 1：完整的网络同步（推荐）

#### 步骤 1：在 HOST 端广播 damage 事件

修改 `piece_deploy.js` 中的 `applyDamage` 函数：

```javascript
applyDamage(targetEntry, amount, attacker = null) {
    if (!targetEntry || typeof amount !== 'number') return;

    // 只有 HOST 才执行伤害计算
    if (window.IS_HOST !== true) {
        console.warn('[piece_deploy] CLIENT should not call applyDamage directly');
        return;
    }

    const reduction = targetEntry.damageReduction || 0;
    const effectiveAmount = Math.max(0, amount * (1 - reduction));
    targetEntry.be_attacked = true;
    targetEntry.attackedById = attacker?.id || null;
    targetEntry.attackedByType = attacker?.type || null;
    targetEntry.attackedByAllegiance = attacker?.allegiance || null;
    targetEntry.lastAttackedAt = Date.now();

    if (targetEntry._beAttackedTimer) {
        clearTimeout(targetEntry._beAttackedTimer);
    }
    targetEntry._beAttackedTimer = setTimeout(() => {
        targetEntry.be_attacked = false;
        targetEntry.attackedById = null;
        targetEntry.attackedByType = null;
        targetEntry.attackedByAllegiance = null;
        targetEntry._beAttackedTimer = null;
    }, 1200);

    // 计算新的 HP
    let newHP;
    if (targetEntry.type === 'king_tower') {
        const shared = this.kingTowerShared[targetEntry.allegiance];
        const current = shared ? shared.hp : (targetEntry.hp ?? targetEntry.maxHP ?? 0);
        newHP = current - effectiveAmount;
        this.updateKingHealth(targetEntry.allegiance, newHP);
    } else {
        const current = targetEntry.hp ?? targetEntry.maxHP ?? 0;
        newHP = Math.max(0, Math.min(current - effectiveAmount, targetEntry.maxHP));
        targetEntry.hp = newHP;
        if (targetEntry.healthBar && typeof targetEntry.healthBar.update === 'function') {
            targetEntry.healthBar.update(targetEntry.hp);
        }
    }

    // ⭐ 广播 damage 事件
    if (typeof window.postToParent === 'function') {
        window.postToParent('state_update', {
            type: 'state_update',
            event: 'damage',
            piece_id: targetEntry.id,
            hp: newHP,
            attacker_id: attacker?.id,
            damage: effectiveAmount
        });
    }

    // 检查是否死亡
    if (newHP <= 0) {
        this.handleDeath(targetEntry);
    }
}
```

#### 步骤 2：添加 death 事件广播

修改 `handleDeath` 函数：

```javascript
handleDeath(entry) {
    // 防止重复触发
    if (entry._isDead) return;
    entry._isDead = true;

    entry.attack = false;
    if (entry.type === 'shouter') {
        entry.shouter_lived = false;
    } else if (entry.type === 'aggressive_tower') {
        entry.aggressive_tower_lived = false;
    }
    if (entry.type === 'fighter') {
        entry.fighter_lived = false;
    } else if (entry.type === 'ruler') {
        entry.ruler_lived = false;
    }
    if (entry._beAttackedTimer) {
        clearTimeout(entry._beAttackedTimer);
        entry._beAttackedTimer = null;
    }

    // 调用本地死亡处理
    if (entry.type === 'shouter') {
        if (typeof window.handleShouterDeath === 'function') {
            window.handleShouterDeath(entry, this.activeMovers[entry.id]);
        }
    } else if (entry.type === 'fighter') {
        if (typeof window.handleFighterDeath === 'function') {
            window.handleFighterDeath(entry, this.activeMovers[entry.id]);
        }
    } else if (entry.type === 'ruler') {
        if (typeof window.handleRulerDeath === 'function') {
            window.handleRulerDeath(entry, this.activeMovers[entry.id]);
        }
    } else if (entry.type === 'aggressive_tower') {
        if (typeof window.handleAggressiveTowerDeath === 'function') {
            window.handleAggressiveTowerDeath(entry);
        }
        this.stopTowerAttack(entry);
    } else if (entry.type === 'king_tower') {
        window.gameOver = true;
        console.log('Game over: King tower destroyed');
    }

    // ⭐ 如果是 HOST，广播 death 事件
    if (window.IS_HOST === true && typeof window.postToParent === 'function') {
        window.postToParent('state_update', {
            type: 'state_update',
            event: 'death',
            piece_id: entry.id,
            piece_type: entry.type,
            allegiance: entry.allegiance,
            position: entry.position
        });
    }
}
```

#### 步骤 3：CLIENT 端处理 death 事件

在 `game_page.html` 中添加死亡处理：

```javascript
function handleDeathFromServer(pieceId) {
    const entry = pieceDeployment.boardPieces.find(p => p.id === pieceId);
    if (!entry) {
        console.warn('[death] Piece not found:', pieceId);
        return;
    }

    // 防止重复处理
    if (entry._isDead) return;

    // 调用本地的 handleDeath，但不再广播
    pieceDeployment.handleDeath(entry);
}

function handleStateUpdate(msg) {
    const event = msg.event;
    switch (event) {
        case 'spawn':
            spawnPieceFromServer(msg.piece);
            break;
        case 'damage':
            applyDamageFromServer(msg.piece_id, msg.hp);
            break;
        case 'death':  // ⭐ 新增
            handleDeathFromServer(msg.piece_id);
            break;
        case 'elixir':
            setElixir(msg.side, msg.elixir);
            break;
        case 'timer':
            updateTimerDisplay(msg.seconds_left);
            break;
        default:
            break;
    }
}
```

#### 步骤 4：禁止 CLIENT 端执行攻击判定

修改所有攻击模块（以 `shouter_attack.js` 为例）：

```javascript
function startShouterAttack(shouter, target) {
    // ⭐ 只有 HOST 才执行攻击
    if (window.IS_HOST !== true) {
        console.log('[shouter_attack] CLIENT mode: skip attack execution');
        return;
    }

    if (!shouter || !target) return;
    shouter.attack = true;
    shouter.currentTargetId = target.id;

    const doAttack = () => {
        if (!shouter.attack || shouter.shouter_lived === false) {
            stopShouterAttack(shouter);
            return false;
        }
        const currentTarget = window.pieceDeployment?.boardPieces?.find(p => p.id === shouter.currentTargetId);
        if (!currentTarget || (currentTarget.hp ?? 0) <= 0 || currentTarget.shouter_lived === false) {
            stopShouterAttack(shouter);
            return false;
        }
        if (!isShouterInRange(shouter, currentTarget)) {
            stopShouterAttack(shouter);
            return false;
        }
        const glyph = glyphs[glyphIndex % glyphs.length];
        glyphIndex++;
        spawnAttackGlyph(shouter, target, glyph, () => {
            if (window.pieceDeployment) window.pieceDeployment.applyDamage(target, 75, shouter);
        });
        return true;
    };

    // 其余攻击逻辑...
}
```

同样的修改应用到：
- `fighter_move.js` 中的攻击逻辑
- `aggressive_tower_attack.js`
- `solid_tower_attack.js`
- `ruler_attack.js`
- `squirmer_attack.js`

### 方案 2：简化版（快速修复）

如果不想大改，至少要确保：

#### 修改 1：CLIENT 端收到 damage 时强制同步

```javascript
function applyDamageFromServer(pieceId, hp) {
    const entry = pieceDeployment.boardPieces.find(p => p.id === pieceId);
    if (!entry) return;

    // 强制设置 HP，不管本地计算的是多少
    entry.hp = hp;
    if (entry.healthBar && typeof entry.healthBar.update === 'function') {
        entry.healthBar.update(entry.hp);
    }

    // 如果 HP <= 0，触发死亡
    if (hp <= 0 && !entry._isDead) {
        pieceDeployment.handleDeath(entry);
    }
}
```

#### 修改 2：HOST 端定时广播所有棋子的 HP

在 HOST 端添加一个定时器，定期同步所有棋子的状态：

```javascript
// 在 game_page.html 的 HOST 端初始化代码中
if (isHost) {
    setInterval(() => {
        pieceDeployment.boardPieces.forEach(entry => {
            if (entry.role === 'troop' && entry.hp > 0) {
                postToParent('state_update', {
                    type: 'state_update',
                    event: 'health_sync',
                    piece_id: entry.id,
                    hp: entry.hp
                });
            }
        });
    }, 1000);  // 每秒同步一次
}
```

## 测试验证

修改后需要测试以下场景：

1. **单个棋子被塔击杀**
   - HOST 端看到棋子消失
   - CLIENT 端同时看到棋子消失
   - 时间差应该 < 100ms

2. **多个棋子同时被攻击**
   - 确保所有死亡事件都正确同步
   - 没有"僵尸"棋子（已死但还在动）

3. **网络延迟情况**
   - 模拟 200ms 延迟
   - CLIENT 端应该晚 200ms 看到死亡，但最终一致

4. **King Tower 被摧毁**
   - 双方同时看到 Game Over
   - 不再有重复的 "Game over" 打印

## 总结

**核心问题**：攻击和死亡逻辑在两端独立执行，没有通过网络同步。

**解决方案**：
1. 所有伤害计算只在 HOST 端执行
2. HOST 广播 `damage` 和 `death` 事件
3. CLIENT 端只根据收到的事件同步本地状态
4. CLIENT 端的攻击判定应该被禁用或仅用于动画表现

**优先级**：
- 高优先级：添加 `death` 事件的网络同步
- 中优先级：确保 CLIENT 端不执行攻击判定
- 低优先级：优化 `damage` 事件的广播频率
