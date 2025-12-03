from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .battle_rooms import create_room, join_room, rooms


router = APIRouter(prefix="/api/battle", tags=["battle"])


class CreateGameResponse(BaseModel):
    game_id: str
    url: str
    side: str


@router.post("/create", response_model=CreateGameResponse)
def create_game():
    # TODO: 以后接 auth 的时候把 user_id 填进来
    user_id = None
    room, side = create_room(user_id)
    return CreateGameResponse(
        game_id=room.game_id,
        url=f"https://chessortag.org/battle/?game={room.game_id}",
        side=side,  # 这里一定是 "a"
    )


class JoinGameRequest(BaseModel):
    game_id: str


class JoinGameResponse(BaseModel):
    game_id: str
    side: str


@router.post("/join", response_model=JoinGameResponse)
def join_game(req: JoinGameRequest):
    user_id = None  # TODO: 以后接 auth
    room, side = join_room(req.game_id, user_id)
    if not room or not side:
        raise HTTPException(status_code=404, detail="Game not found")

    return JoinGameResponse(game_id=req.game_id, side=side)


class GameInfoResponse(BaseModel):
    game_id: str
    has_player_a: bool
    has_player_b: bool
    next_side: str | None


@router.get("/info", response_model=GameInfoResponse)
def get_game_info(game: str = Query(..., description="Game id to inspect")):
    room = rooms.get(game)
    if not room:
        raise HTTPException(status_code=404, detail="Game not found")

    next_side = None
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
