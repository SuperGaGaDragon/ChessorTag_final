# 塔楼转换和Ability修复方案

## 问题总结

### 问题1：B端塔楼转换无效
- **根本原因**：所有ability代码硬编码了 `allegiance='a'`
- **影响**：B端玩家无法转换自己的塔楼，无法使用ability

### 问题2：两端同时计算导致不一致
- **根本原因**：塔楼转换、ability效果在两端都执行
- **影响**：
  - HP百分比转换在两端计算可能不一致
  - Ability效果在两端都触发，导致重复
  - 网络延迟导致B端看到的效果滞后

## 解决方案：HOST Authority模式

采用**完全的HOST权威模式**：

### 核心原则
1. **所有游戏逻辑只在HOST端执行**
2. **CLIENT端只处理UI交互，发送请求给HOST**
3. **HOST广播状态更新给所有CLIENT**
4. **CLIENT根据状态更新同步本地表现**

### 实施步骤

#### 第一步：定义新的网络消息类型

```javascript
// CLIENT -> HOST: 塔楼转换请求
{
  type: 'tower_switch_request',
  allegiance: 'b'  // 哪一方要转换塔楼
}

// HOST -> ALL: 塔楼转换完成
{
  type: 'state_update',
  event: 'tower_switch',
  allegiance: 'b',
  new_type: 'aggressive',  // or 'solid'
  towers: [
    { id: 'xxx', hp: 450, maxHP: 600, type: 'aggressive_tower', row: 1, col: 1 },
    { id: 'yyy', hp: 450, maxHP: 600, type: 'aggressive_tower', row: 1, col: 6 }
  ],
  elixir: 5  // 剩余elixir
}

// CLIENT -> HOST: Ability激活请求
{
  type: 'ability_request',
  allegiance: 'b',
  ability_type: 'aggressive_forward'  // or 'solid_shield'
}

// HOST -> ALL: Ability激活
{
  type: 'state_update',
  event: 'ability_start',
  allegiance: 'b',
  ability_type: 'aggressive_forward',
  towers: [
    { id: 'xxx', damageReduction: 0.25, position: {row: 0, col: 1}, ... }
  ],
  duration: 3000,
  elixir: 4
}

// HOST -> ALL: Ability结束
{
  type: 'state_update',
  event: 'ability_end',
  allegiance: 'b',
  ability_type: 'aggressive_forward',
  towers: [
    { id: 'xxx', damageReduction: 0, position: {row: 1, col: 1}, ... }
  ]
}
```

#### 第二步：修改ability代码

**aggressive_tower_ability.js 改造**：

1. `switchPlayerTowers()` - 改为发送请求而不是直接执行
2. 添加 `handleTowerSwitchFromHost()` - 接收HOST的更新
3. ability激活改为发送请求
4. 添加 `handleAbilityStartFromHost()` 和 `handleAbilityEndFromHost()`

**solid_tower_ability.js 改造**：

1. ability激活改为发送请求
2. 添加HOST端的ability执行逻辑
3. 添加CLIENT端的ability视觉更新逻辑

#### 第三步：在game_page.html中实现HOST逻辑

```javascript
// HOST端处理塔楼转换请求
function handleTowerSwitchRequest(msg) {
  if (!isHost) return;

  const allegiance = msg.allegiance;
  const towers = getTowersByAllegiance(allegiance);

  // 检查是否可以转换
  if (!canSwitchTowers(allegiance)) {
    console.log('Cannot switch towers');
    return;
  }

  // 执行转换
  const currentType = towers[0]?.type;
  const newType = currentType === 'solid_tower' ? 'aggressive' : 'solid';
  rescaleTowerStats(towers, newType);

  // 扣除elixir
  const elixirKey = allegiance === 'a' ? 'currentElixir' : 'opponentElixir';
  elixirManager[elixirKey]--;

  // 广播状态更新
  postToParent('state_update', {
    type: 'state_update',
    event: 'tower_switch',
    allegiance,
    new_type: newType,
    towers: towers.map(serializePiece),
    elixir: elixirManager[elixirKey]
  });
}

// CLIENT端接收塔楼转换更新
function handleTowerSwitchFromServer(msg) {
  const allegiance = msg.allegiance;
  const newType = msg.new_type;

  // 更新本地状态
  msg.towers.forEach(towerData => {
    const tower = pieceDeployment.boardPieces.find(p => p.id === towerData.id);
    if (tower) {
      tower.type = towerData.type;
      tower.hp = towerData.hp;
      tower.maxHP = towerData.maxHP;

      // 更新图片
      const img = tower.element?.querySelector('img');
      if (img) {
        img.src = newType === 'solid'
          ? '../pieces/solid_tower/solid_tower.png'
          : '../pieces/agressive_tower/aggressive_tower.png';
      }

      // 更新血条
      refreshHealthBar(tower);
    }
  });

  // 更新elixir显示
  setElixir(allegiance, msg.elixir);
}
```

## 优势

1. **数据一致性**：所有游戏状态在HOST端计算，保证唯一真实来源
2. **网络延迟容忍**：CLIENT只负责显示，延迟不影响游戏逻辑
3. **作弊防护**：CLIENT无法直接修改游戏状态
4. **易于调试**：所有逻辑集中在HOST端

## 实施优先级

### 高优先级（立即实施）
1. 修复塔楼转换的allegiance参数化
2. 添加网络消息定义
3. HOST端实现转换和ability逻辑

### 中优先级
1. CLIENT端UI交互改造
2. 状态同步优化
3. 错误处理

### 低优先级
1. 优化网络消息大小
2. 添加重连机制
3. 性能优化

## WebSocket 1006问题分析

### 可能原因

1. **服务器超时**
   - 服务器端设置了连接超时
   - 没有实现心跳机制

2. **网络不稳定**
   - 移动网络切换
   - WiFi信号弱

3. **服务器主动关闭**
   - 游戏结束后服务器关闭连接
   - 服务器重启或崩溃

4. **消息过大或频率过高**
   - timer每秒广播可能导致负载
   - 多个spawn消息同时发送

### 建议修复

1. **添加心跳机制**
```javascript
// 每30秒发送ping
setInterval(() => {
  if (directWs && directWs.readyState === WebSocket.OPEN) {
    directWs.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

2. **添加重连逻辑**
```javascript
directWs.onclose = (ev) => {
  console.log('[battle] WS closed', ev.code, ev.reason);
  if (ev.code === 1006) {
    console.log('[battle] Abnormal closure, attempting reconnect...');
    setTimeout(() => connectDirectWs(directGameId), 3000);
  }
};
```

3. **添加错误日志**
```javascript
directWs.onerror = (err) => {
  console.error('[battle] WS error', err);
  console.log('[battle] readyState:', directWs.readyState);
};
```

4. **优化消息频率**
   - 考虑将timer消息改为2秒一次
   - 批量发送多个状态更新
