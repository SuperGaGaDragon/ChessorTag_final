from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .battle_rooms import create_room, join_room, rooms


router = APIRouter(prefix="/battle", tags=["battle"])


# ---------- 创建游戏 ----------

class CreateGameResponse(BaseModel):
    game_id: str
    url: str
    side: str


@router.post("/create", response_model=CreateGameResponse)
def create_game():
    # TODO: 以后接 auth 的时候把 user_id 填进来
    user_id = None
    room, side = create_room(user_id)

    # 现在你的前端战斗页面是 /cat_royale/game_page/
    url = f"https://chessortag.org/cat_royale/game_page/?game={room.game_id}"

    return CreateGameResponse(
        game_id=room.game_id,
        url=url,
        side=side,
    )


# ---------- 加入游戏（这就是现在缺的那个） ----------

class JoinGameRequest(BaseModel):
    game_id: str


class JoinGameResponse(BaseModel):
    game_id: str
    side: str


@router.post("/join", response_model=JoinGameResponse)
def join_game(payload: JoinGameRequest):
    """
    前端在打开 WebSocket 之前会先调这个接口，
    让后端给这个浏览器分配 side: "a" / "b" / "spectate"。
    """
    game_id = payload.game_id
    user_id = None  # 暂时没有登录系统

    room, side = join_room(game_id, user_id)
    if not room or side is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return JoinGameResponse(
        game_id=room.game_id,
        side=side,
    )


# ---------- 游戏信息（你原来就有的） ----------

class GameInfoResponse(BaseModel):
    game_id: str
    has_player_a: bool
    has_player_b: bool
    next_side: str | None


@router.get("/game_info", response_model=GameInfoResponse)
def get_game_info(game: str = Query(..., description="Game ID")):
    """
    给大厅 / 观战用的简单信息：A/B 是否已经有人，下一位加入会分到哪一边。
    """
    room = rooms.get(game)
    if not room:
        raise HTTPException(status_code=404, detail="Game not found")

    next_side: str | None = None
    if room.player_a is None:
        next_side = "a"
    elif room.player_b is None:
        next_side = "b"

    return GameInfoResponse(
        game_id=game,
        has_player_a=room.player_a is not None,
        has_player_b=room.player_b is not None,
        next_side=next_side,
    )
