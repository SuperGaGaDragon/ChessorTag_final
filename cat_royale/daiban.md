# 待办事项 (To-Do List)

基于 paicha.md 中的调试报告，以下是需要完成的任务：

## 问题 A：修复 B 端错误调用 handleLocalDeploy

### 状态：✅ 已完成

### 问题描述
- B 端（CLIENT）在调用 `handleLocalDeploy`，但应该调用 `handleLocalDeployRequest`
- 当前 B 端显示 `IS_HOST: false`，但仍在走 HOST mode 的函数

### 需要做的事情
1. 在 `piece_deploy.js` 中全局搜索 `handleLocalDeploy(`
2. 确保只有一处在 `deployPiece()` 的 HOST 分支调用
3. 其他所有调用处要么删除，要么加上 `if (window.IS_HOST === true)` 检查
4. 重写 HOST/CLIENT 分支逻辑为明确的 if/else：

```javascript
if (!fromNetwork) {
    if (window.IS_HOST === true) {
        console.log('[piece_deploy] HOST mode: calling handleLocalDeploy');
        window.handleLocalDeploy(payload);
    } else {
        console.log('[piece_deploy] CLIENT mode: calling handleLocalDeployRequest');
        window.handleLocalDeployRequest(payload);
    }
    return;
}
```

### 验证标准
- B 端下子时 console 显示：`[piece_deploy] CLIENT mode: calling handleLocalDeployRequest`
- 不再出现 `[game_page] handleLocalDeploy called ...` 在 B 端

---

## 问题 B：父页面没有接收到消息

### 状态：✅ 已完成

### 问题描述
- iframe 发送了 `postMessage`，但父页面没有任何 `[PAGE ...]` 日志
- 说明 `bindFrameMessages()` 没有正常工作或 `init()` 没有被调用

### 需要做的事情
1. 在 `index.js` 的 `init()` 函数中添加日志：

```javascript
function init() {
    console.log('[PAGE] init top', window.location.href);
    cacheUI();
    bindUI();
    bindFrameMessages();
    updateStartButton();
    handleQueryJoin();
}
```

2. 在 `bindFrameMessages()` 函数中添加日志：

```javascript
function bindFrameMessages() {
    console.log('[PAGE] bindFrameMessages registered');
    window.addEventListener('message', (event) => {
        const msg = event.data || {};
        console.log('[PAGE raw message]', event.origin, event.data);
        ...
    });
}
```

3. 检查 HTML 文件，确保：
   - script 标签正确加载
   - script 不在 iframe 内部，而是在父页面上
   - 路径正确

### 验证标准
刷新页面后，在 top context 下应该看到：
- `[PAGE] init top https://chessortag.org/cat_royale/game_page/?game=DDD423`
- `[PAGE] bindFrameMessages registered`

B 端下子时，在 top context 应该看到：
- `[PAGE raw message] ... { type: "deploy_request", ... }`
- `[PAGE] handling deploy_request`
- `[PAGE → WS] sending deploy_request {...}`

---

## 完整链路测试

### 状态：🔴 待处理

### 需要做的事情
完成上述两个问题的修复后，进行 A/B 双开对局测试：

1. **B 端下子流程**：
   - B iframe log 显示：`CLIENT mode → handleLocalDeployRequest → postToParent`
   - top log 显示：`[PAGE raw message]` + `[PAGE] handling deploy_request` + `[PAGE → WS] sending deploy_request`

2. **A 端接收流程**：
   - A top 收到 "deploy" 消息
   - A iframe 显示棋子

3. **状态同步流程**：
   - A 发送 `state_update`
   - B 收到并更新棋盘

### 验证标准
整条联机链路完全跑通：
- B 下子 → 父页面收到 → WebSocket 发送 → A 接收 → A 显示 → A 同步状态 → B 更新

---

## 当前进度总结

### ✅ 已完成
- `handleLocalDeploy` 内部逻辑修复（不再误分 state_update / deploy_request）
- iframe → parent 的 postMessage 电线接通（B 端确实在发送消息）
- **修复 B 端分支逻辑**：在 `piece_deploy.js` 中添加了明确的 HOST/CLIENT 分支判断（487-509行）
- **修复父页面消息接收**：在 `index.js` 中添加了 `[PAGE] init top` 和 `[PAGE] bindFrameMessages registered` 日志（352行、321行）
- CLIENT 端早期返回，确保不会继续执行 HOST 逻辑
- HOST 端调用 `handleLocalDeploy` 时也添加了 `IS_HOST === true` 检查（608行）

### 🔴 待完成
- 完整链路测试和验证（需要 A/B 双开测试）

---

## 注意事项

1. **不要自以为修好了**：必须看到完整的日志链路才能确认
2. **使用 top context**：在 Chrome DevTools 中切换到 top 查看父页面日志
3. **日志驱动调试**：每一步都要有明确的 console.log 输出
4. **分步验证**：先修复分支逻辑，再修复消息接收，最后做完整测试

---

## 修复详情

### 修改文件 1: piece_deploy.js

**位置**: `/website/cat_royale/piece_deploy/piece_deploy.js`

**修改内容**:

1. **487-509行**：重写了 HOST/CLIENT 分支逻辑
   - 明确的 `if (window.IS_HOST === true)` 判断
   - CLIENT 模式调用 `handleLocalDeployRequest` 后立即 return
   - 确保 CLIENT 不会继续执行后续的部署代码

```javascript
// HOST vs CLIENT branching: only one path should execute
if (!fromNetwork) {
    if (window.IS_HOST === true) {
        // HOST mode: deploy locally and broadcast
        console.log('[piece_deploy] HOST mode: will deploy and broadcast');
    } else {
        // CLIENT mode: send request to host
        console.log('[piece_deploy] CLIENT mode: calling handleLocalDeployRequest');
        if (typeof window.handleLocalDeployRequest === 'function') {
            window.handleLocalDeployRequest({ ... });
        }
        return { requested: true };  // 早期返回，不继续执行
    }
}
```

2. **608-623行**：为 HOST 调用 handleLocalDeploy 添加了额外检查
   - 只有在 `window.IS_HOST === true` 时才调用
   - 防止任何情况下的误调用

### 修改文件 2: index.js

**位置**: `/website/cat_royale/game_page/index.js`

**修改内容**:

1. **352行**：在 `init()` 函数添加日志
   ```javascript
   console.log('[PAGE] init top', window.location.href);
   ```

2. **321行**：在 `bindFrameMessages()` 函数添加日志
   ```javascript
   console.log('[PAGE] bindFrameMessages registered');
   ```

这些日志帮助确认父页面的初始化和消息监听器是否正常注册。

---

## 测试指南

### 预期日志输出

刷新页面后应该看到：
```
[PAGE] init top https://chessortag.org/cat_royale/game_page/?game=DDD423
[PAGE] bindFrameMessages registered
```

B 端下子时应该看到：
```
// B iframe (CLIENT):
[piece_deploy] deployPiece called {..., IS_HOST: false}
[piece_deploy] CLIENT mode: calling handleLocalDeployRequest
[game_page] postToParent called { type: 'deploy_request', ... }
[game_page] sending postMessage to parent

// 父页面 top context:
[PAGE raw message] ... { type: "deploy_request", ... }
[PAGE] handling deploy_request
[PAGE → WS] sending deploy_request {...}
```

A 端（HOST）下子时应该看到：
```
// A iframe (HOST):
[piece_deploy] deployPiece called {..., IS_HOST: true}
[piece_deploy] HOST mode: will deploy and broadcast
[piece_deploy] HOST mode: calling handleLocalDeploy
Deployed shouter (a) at row 4, col 3
```

### 如果测试失败

- 确认已清除浏览器缓存并刷新页面
- 确认在正确的 DevTools context 中查看日志（top vs iframe）
- 检查 WebSocket 连接状态
- 查看是否有 JavaScript 错误
