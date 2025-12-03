# 404 排查结果（WebSocket 前置的 join 请求）

- 现状：后端路由前缀改成了 `/battle`（backend/battle_api.py: `router = APIRouter(prefix="/battle", ...)`），FastAPI 在 `main.py` 中直接 `include_router(battle_router)`，因此实际接口是 `/battle/create`、`/battle/join`、`/battle/game_info`。
- 前端（website/cat_royale/game_page/index.js 和 game_page.html 内的 standalone 逻辑）依旧请求 `${apiBase()}/api/battle/join` 和 `${apiBase()}/api/battle/create`。线上 `apiBase()` 为 `https://api.chessortag.org`，因此请求地址是 `https://api.chessortag.org/api/battle/join`，与后端实际路径不一致，返回 404。
- WebSocket 未建立的直接原因：在执行 `new WebSocket(...)` 之前的 `join` fetch 404 报错，中断了后续流程。

可选修复方案（2 选 1）：
1. 后端前缀改回 `/api/battle`（battle_api.py 还原为 `APIRouter(prefix="/api/battle", ...)`），与当前前端调用保持一致。
2. 保持后端 `/battle`，同步修改前端所有 API 调用路径（index.js 和 game_page.html 的 standalone networking）为 `/battle/...`。

备注：无论选哪种，需要重启后端使路由生效。***
