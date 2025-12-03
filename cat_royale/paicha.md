
监工codex的工作：
## 新场景：WS 已 101，但双方不同步（2024-XX-XX）

- 现象：Socket 面板已显示 101（例如 game=5C2A84），但对局状态不同步（B 端看不到 A 端操作）。说明 WS 连接已建立，但消息链路中断。
- 架构回顾：iframe 内 `game_page.html` 通过 `postMessage` 把 `deploy_request` / `local_ruler_move` / `state_update` 发给父页；父页 `index.js` 在 `window.message` 监听里转发到 WS；WS 收到后广播，再由父页的 `onmessage` 把事件转发回 iframe。
- 可疑点：
  1) 父页转发：`index.js` 中只处理 `msg.type === 'local_deploy' | 'deploy_request' | 'local_ruler_move' | 'state_update'`。若 iframe 发送的 `postMessage` 类型与这里不匹配（例如漏了某个事件名），会直接被丢弃。
  2) 服务器广播：`battle_ws.py` 仅在 `msg_type in ("deploy", "deploy_request", "ruler_move", "ruler_move_request", "surrender", "tower_setup", "state_update")` 时广播。iframe 里 spawn 完之后通知父页的 payload 是 `type: 'state_update', event:'spawn', piece:{...}`，符合广播，但如果父页未发送，服务端就收不到。
  3) iframe 监听回流：`game_page.html` 监听 `window.message`，仅处理 `side_update/state_update/battle_start/deploy_request/remote_deploy/remote_ruler_move/opponent_disconnected`。如果服务端广播了 `deploy`（而父页未改名为 `remote_deploy`），则 iframe 不会处理。
- 定位建议（无需改代码）：
  - 在父页 Console 打 log：确认 `window.addEventListener('message', ...)` 收到 deploy/state 事件并调用 `state.ws.send(...)`。
  - 在 Network → WS → Frames 查看是否有客户端发出的 `{"type":"deploy_request"...}` / `{"type":"state_update","event":"spawn"...}`。
  - 在另一端的 WS Frames 看是否收到相应广播（服务端已 broadcast）。
  - 如果 Frames 里没有发出帧，问题在父页未转发；有发出但另一端没收到，问题在服务端广播；收到但 iframe 未更新，问题在 iframe 事件名匹配。


老板我对监工的判断：
架构 & 断点判断 ✅

“Socket 面板 101 但不同步 ⇒ WS 只是不挂线，消息链路某处断掉”
这个判断是完全正确的。

你画的链路：

iframe → parent(index.js) → WS → server broadcast → parent → iframe
和现有代码完全一致。

2. 三个可疑点的校对
① 父页转发 window.message ✅

只处理 local_deploy | deploy_request | local_ruler_move | state_update，类型不匹配就被丢弃。

对。
现在 index.js 里确实是这样写的：

switch (msg.type) {
  case 'local_deploy':
  case 'deploy_request':
  case 'local_ruler_move':
  case 'state_update':
    ...
}


所以 如果 game_page 里 postMessage 用了别的 type（比如 deploy、place_piece 之类），父页就完全不会转发——这是目前最可疑的一段。

② 服务器广播的消息类型 ✅（有个小 nuance）

battle_ws.py 中大致逻辑是：

if msg_type in ("deploy", "deploy_request", "ruler_move",
                "ruler_move_request", "surrender", "tower_setup", "state_update"):
    await broadcast(...)


从外层发出去的是 deploy_request / ruler_move_request / state_update

服务器收到后，会根据逻辑（特别是部署成功）再发出 deploy / ruler_move / state_update

这一点和你写的是一致的：

state_update 的 payload 形如 event:'spawn', piece:{...}，如果父页没发出去，服务端就啥也收不到。

这一点 ✅。

③ iframe 监听回流 ✅（注意 deploy→remote_deploy 的映射）

如果服务端广播了 deploy（而父页未改名为 remote_deploy），则 iframe 不会处理。

这里稍微修正一下说法：

现在 父页已经在 handleMessage 里做了一次映射：

case 'deploy':
  forwardToFrame('remote_deploy', msg);
  break;
case 'ruler_move':
  forwardToFrame('remote_ruler_move', msg);
  break;


game_page 里的 listener 是收 remote_deploy / remote_ruler_move，这正好对上。

所以这一段是设计正确的：
只要服务器广播 {"type": "deploy", ...}，父页就会转成 remote_deploy 丢给 iframe。

真正风险还是在 前半截没把 deploy_request / state_update 送进 WS，而不是这里。

3. 你列的“定位建议”也 ✅

完全可以照你写的步骤逐层排查：

在父页（Console 选 top）看 bindFrameMessages 是否有 log：

console.log('[PAGE raw message]', event.origin, event.data);


没任何 log：iframe 根本没 postMessage 或 type 不对；

有 raw 但没有 [PAGE → WS]：switch case 不匹配。

在 Network → Socket → Frames 看自己是不是有发 deploy_request / state_update 帧

没发：问题在父页没转发；

发了另一边没收到：问题在服务端广播逻辑；

收到了但 UI 不动：看 handleMessage / iframe 的 listener。

整体就是你写的那三层 check，只是加一句：

先确认 “parent 是否收到 iframe 的 postMessage”（这一层现在最可疑，因为你之前所有 [PAGE message] log 都没出现过）。

4. 总结一句话

你的这版“问题分析 + 调试计划”是 正确方向，逻辑也基本无坑；

需要微调的小地方只是：

服务器广播 deploy → 父页已经会转成 remote_deploy，这一段理论上没问题；

当前最可疑的是 iframe 发出的消息 type 与父页 switch 不匹配，或者压根没发。


claude的debug：

## 修复内容（2025-12-03）

### 问题分析
经过检查，发现 `index.js` 中 `bindFrameMessages` 函数存在以下问题：

1. **无用的 case 分支**：`case 'local_deploy'` 永远不会被触发，因为 `game_page.html` 从不发送 `type: 'local_deploy'` 的消息
   - 实际发送的类型只有：`deploy_request`、`local_ruler_move`、`state_update`

2. **调试信息不足**：当父页面没有收到 iframe 的 postMessage 时，无法确定是：
   - iframe 没发送
   - 类型不匹配被忽略
   - 还是其他原因

### 具体改动

**文件：`website/cat_royale/game_page/index.js`（第314-343行）**

#### 改动前：
```javascript
function bindFrameMessages() {
    window.addEventListener('message', (event) => {
        const msg = event.data || {};
        console.log('[PAGE message]', msg);
        switch (msg.type) {
            case 'local_deploy':  // ← 无用分支，game_page 从不发送此类型
                sendDeployRequest(msg.payload || msg);
                break;
            case 'deploy_request':
                sendDeployRequest(msg.payload || msg);
                break;
            case 'local_ruler_move':
                sendRulerMove(msg.payload || msg);
                break;
            case 'state_update':
                if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                    const payload = {
                        ...msg.payload,
                        type: 'state_update',
                    };
                    console.log('[PAGE → WS] sending state_update', payload);
                    state.ws.send(JSON.stringify(payload));
                }
                break;
            default:
                break;
        }
    });
}
```

#### 改动后：
```javascript
function bindFrameMessages() {
    window.addEventListener('message', (event) => {
        const msg = event.data || {};
        console.log('[PAGE raw message]', event.origin, event.data);  // ← 增强调试信息
        switch (msg.type) {
            // 删除了 case 'local_deploy' 无用分支
            case 'deploy_request':
                console.log('[PAGE] handling deploy_request');  // ← 新增
                sendDeployRequest(msg.payload || msg);
                break;
            case 'local_ruler_move':
                console.log('[PAGE] handling local_ruler_move');  // ← 新增
                sendRulerMove(msg.payload || msg);
                break;
            case 'state_update':
                console.log('[PAGE] handling state_update');  // ← 新增
                if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                    const payload = {
                        ...msg.payload,
                        type: 'state_update',
                    };
                    console.log('[PAGE → WS] sending state_update', payload);
                    state.ws.send(JSON.stringify(payload));
                }
                break;
            default:
                console.log('[PAGE] unhandled message type:', msg.type);  // ← 新增
                break;
        }
    });
}
```

### 改动说明

1. **删除了 `case 'local_deploy'` 分支**：
   - 这个分支从未被使用，因为 `game_page.html` 中：
     - Host 侧发送 `state_update`（第1412行）
     - 非Host 侧发送 `deploy_request`（第1429行）
     - 从不发送 `local_deploy`

2. **增强了调试日志**：
   - 第一行改为 `console.log('[PAGE raw message]', event.origin, event.data)`
     - 显示消息来源（origin）
     - 显示原始数据（data）
     - 这样即使类型不匹配，也能看到收到了什么消息

   - 在每个 case 中添加处理日志：
     - `[PAGE] handling deploy_request`
     - `[PAGE] handling local_ruler_move`
     - `[PAGE] handling state_update`

   - 在 default 中添加未处理类型的日志：
     - `[PAGE] unhandled message type: xxx`
     - 如果 iframe 发送了意外的消息类型，可以立即发现

### 调试建议

有了这些改动后，在浏览器 Console 中可以看到：

1. **如果看到 `[PAGE raw message]`**：说明父页面收到了 iframe 的消息
   - 继续看是否有 `[PAGE] handling xxx`：说明类型匹配，正在处理
   - 如果看到 `[PAGE] unhandled message type`：说明类型不匹配

2. **如果完全没有 `[PAGE raw message]`**：说明父页面根本没收到 iframe 的消息
   - 检查 iframe 的 `hasParentBridge` 是否为 true
   - 检查 iframe 是否正确调用了 `postToParent`

3. **如果看到 `[PAGE → WS]`**：说明消息已经发送到 WebSocket
   - 在 Network → WS → Frames 中查看是否真的发出去了
   - 检查另一端是否收到广播

### 消息流程总结

#### 非Host（B侧）部署棋子：
1. 用户点击部署
2. `piece_deploy.js` 第486行：检测到非Host → 调用 `handleLocalDeployRequest`
3. `game_page.html` 第1429行：发送 `postMessage({type: 'deploy_request', payload: {...}})`
4. 父页面 `index.js` 第319行：收到 → 打印 `[PAGE] handling deploy_request`
5. `index.js` 第247行：`sendDeployRequest` 发送到 WS
6. 服务器广播给所有人（包括Host）
7. Host 收到 WS 消息 → 第116行转发给 iframe → `handleDeployRequest` → 创建棋子 → 发送 `state_update`
8. 服务器再次广播 `state_update`
9. B侧收到 → `handleStateUpdate` → 创建棋子

#### Host（A侧）部署棋子：
1. 用户点击部署
2. `piece_deploy.js` 第486行：检测到是Host → 继续执行 → 第500-606行本地创建棋子
3. `piece_deploy.js` 第596行：调用 `handleLocalDeploy`
4. `game_page.html` 第1412行：发送 `postMessage({type: 'state_update', payload: {event: 'spawn', ...}})`
5. 父页面 `index.js` 第327行：收到 → 打印 `[PAGE] handling state_update`
6. `index.js` 第329行：发送到 WS
7. 服务器广播给所有人（包括B侧）
8. B侧收到 → `handleStateUpdate` → 创建棋子

### 注意事项

这次修复主要是：
- **清理无用代码**（`local_deploy` 分支）
- **增强调试能力**（详细的 console.log）

如果问题依然存在，现在可以通过 console.log 精确定位是哪个环节出了问题。


