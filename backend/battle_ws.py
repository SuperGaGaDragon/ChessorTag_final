from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .battle_rooms import rooms


ws_router = APIRouter()


@ws_router.websocket("/ws/battle/{game_id}")
async def battle_ws(websocket: WebSocket, game_id: str):
    await websocket.accept()

    room = rooms.get(game_id)
    if not room:
        await websocket.close(code=1000)
        return

    side: str
    if "a" not in room.sockets and room.player_a:
        side = "a"
    elif "b" not in room.sockets and room.player_b:
        side = "b"
    else:
        room.spectator_counter += 1
        side = f"spectate-{room.spectator_counter}"

    room.sockets[side] = websocket
    if side in ("a", "b"):
        room.ready[side] = False

    await websocket.send_json({"type": "side", "side": "spectate" if side.startswith("spectate") else side})

    async def broadcast(payload: dict, exclude: str | None = None):
        for s_key, ws in list(room.sockets.items()):
            if exclude and s_key == exclude:
                continue
            try:
                await ws.send_json(payload)
            except Exception:
                continue

    def other_side(current: str) -> str:
        return "b" if current == "a" else "a"

    try:
        # Notify when both players are connected
        if "a" in room.sockets and "b" in room.sockets:
            await broadcast({"type": "players_connected"})

        # If game already started, sync late joiners (spectators)
        if room.ready.get("a") and room.ready.get("b"):
            await websocket.send_json(
                {
                    "type": "start",
                    "side": side if side in ("a", "b") else "spectate",
                    "towers": room.tower_types,
                }
            )

        while True:
            msg = await websocket.receive_json()
            msg_type = msg.get("type")

            if msg_type == "ready":
                if side not in ("a", "b"):
                    # Spectators cannot ready
                    continue
                room.ready[side] = True
                tower = msg.get("tower")
                if tower:
                    room.tower_types[side] = tower
                await broadcast({"type": "opponent_ready", "side": side, "tower": tower}, exclude=side)

                if room.ready["a"] and room.ready["b"]:
                    for s_key, ws in list(room.sockets.items()):
                        await ws.send_json(
                            {
                                "type": "start",
                                "side": s_key if s_key in ("a", "b") else "spectate",
                                "towers": room.tower_types,
                            }
                        )

            elif msg_type in ("deploy", "deploy_request", "ruler_move", "ruler_move_request", "surrender", "tower_setup", "state_update"):
                await broadcast(msg, exclude=side)

            else:
                await websocket.send_json({"type": "error", "error": "unknown_type"})
    except WebSocketDisconnect:
        room.sockets.pop(side, None)
        if side in ("a", "b"):
            room.ready[side] = False
        await broadcast({"type": "opponent_disconnected"}, exclude=side)
