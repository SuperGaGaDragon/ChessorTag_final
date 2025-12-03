# 404 排查结果（WebSocket 前置的 join 请求）

- 现状：后端路由前缀改成了 `/battle`（backend/battle_api.py: `router = APIRouter(prefix="/battle", ...)`），FastAPI 在 `main.py` 中直接 `include_router(battle_router)`，因此实际接口是 `/battle/create`、`/battle/join`、`/battle/game_info`。
- 前端（website/cat_royale/game_page/index.js 和 game_page.html 内的 standalone 逻辑）依旧请求 `${apiBase()}/api/battle/join` 和 `${apiBase()}/api/battle/create`。线上 `apiBase()` 为 `https://api.chessortag.org`，因此请求地址是 `https://api.chessortag.org/api/battle/join`，与后端实际路径不一致，返回 404。
- WebSocket 未建立的直接原因：在执行 `new WebSocket(...)` 之前的 `join` fetch 404 报错，中断了后续流程。

可选修复方案（2 选 1）：
1. 后端前缀改回 `/api/battle`（battle_api.py 还原为 `APIRouter(prefix="/api/battle", ...)`），与当前前端调用保持一致。
2. 保持后端 `/battle`，同步修改前端所有 API 调用路径（index.js 和 game_page.html 的 standalone networking）为 `/battle/...`。

备注：无论选哪种，需要重启后端使路由生效。***

---

## 继续排查（2024-XX-XX）

现象：在浏览器 Network 面板看不到 `/ws/battle/...`，Console 报 `https://api.chessortag.org/api/battle/create` 404，WS 未建立。

分析：
- battle_api.py 已改回前缀 `/api/battle`，但生产请求仍然 404，说明部署侧未加载最新代码或服务未重启。
- 前端 index.js / game_page.html 的 fetch 仍指向 `/api/battle/...`，只要后端生效就会调用 `connectWs(...)` 并打印 `[battle] connecting WS:`。

确认步骤（无需改代码）：
- 在后端环境 `curl -i https://api.chessortag.org/api/battle/create`，检查是否仍 404；若是，需重启/重新部署以加载新前缀。
- 本地启动后端验证 `/api/battle/create` 200，确认代码本身无误；再确保生产版本与之同步部署。

结论：当前 404 的直接原因是生产后端仍跑着旧路由，导致 create/join 阶段失败，WS 初始化未触发。等待后端重启/发布后，再次创建房间应能看到 WS 请求和 `[battle] WS open` 日志。***

## 新发现：battle_rooms.py 不应引用 WebSocket

- VSCode 报 `WebSocket is not defined` 指向 battle_rooms.py 行 17。原因：rooms 管理层不应类型标注/引用 WebSocket，WS 只应在 battle_ws.py 处理。
- 已修正：去掉 WebSocket 前向声明，将 `sockets` 类型标注改为 `Dict[str, Any]`，并注释说明仅存放不透明引用，收发逻辑仍在 battle_ws.py。文件：backend/battle_rooms.py。
- 需要重启后端加载该修复；本次修改不影响 API 路由前缀。***

## 最新现象：无任何 WS 请求（2024-XX-XX）

- 复现：直接打开 `https://chessortag.org/cat_royale/game_page/?game=B531BB`，Network 面板的 Socket 为空，没有 `/ws/battle/...` 记录；Console 也没有 `[battle] connecting WS:` / `[battle] WS open`。
- game_page 的单页模式按理会在 DOMContentLoaded 时调用 `directJoin`（POST `/api/battle/join`）成功后再 `connectDirectWs`。如果 join 返回 404/失败，WS 不会被创建。
- 截图中没有 WS 流量，说明前置的 create/join 仍未成功（大概率生产后端仍未加载 `/api/battle/*` 前缀），导致单页逻辑短路为本地假开局。
- 验证建议：
  - 直接请求 `https://api.chessortag.org/api/battle/join`/`create` 检查是否仍 404；若是，需确认生产后端已重启并加载新前缀 `/api/battle`。
  - 本地启动后端确认 `/api/battle/join` 200 正常，再确保生产镜像/容器与本地代码一致。
  - 前端调试：在 Console 搜索 `[battle] connecting WS`，如果没有，说明 join 没成功；找到 join fetch 的错误信息进一步定位。***
