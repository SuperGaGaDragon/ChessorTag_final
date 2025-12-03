from dataclasses import dataclass, field
from typing import Dict, Optional
import secrets


@dataclass
class BattlePlayer:
    user_id: Optional[str]
    side: str  # "a" or "b"


@dataclass
class BattleRoom:
    game_id: str
    player_a: Optional[BattlePlayer] = None
    player_b: Optional[BattlePlayer] = None
    sockets: Dict[str, "WebSocket"] = field(default_factory=dict)
    ready: Dict[str, bool] = field(default_factory=lambda: {"a": False, "b": False})
    tower_types: Dict[str, Optional[str]] = field(default_factory=lambda: {"a": None, "b": None})
    spectator_counter: int = 0


rooms: Dict[str, BattleRoom] = {}


def generate_game_id() -> str:
    """Generate a 6-char uppercase game id."""
    return secrets.token_hex(3).upper()


def create_room(user_id: Optional[str]) -> tuple[BattleRoom, str]:
    """
    创建房间，并且让创建者直接占掉 A 位。
    返回 (room, side)；side 永远是 "a"。
    """
    game_id = generate_game_id()
    room = BattleRoom(game_id=game_id)
    rooms[game_id] = room

    # 创建者 = A
    room.player_a = BattlePlayer(user_id=user_id, side="a")
    return room, "a"


def join_room(game_id: str, user_id: Optional[str]) -> tuple[Optional[BattleRoom], Optional[str]]:
    """
    加入房间，并决定这次加入者的 side：
    - 如果 A 还空：占 A（极端 fallback）
    - 否则如果 B 空：占 B
    - 否则：spectate
    返回 (room, side)；如果房间不存在，返回 (None, None)。
    """
    room = rooms.get(game_id)
    if not room:
        return None, None

    # 正常流程：房主已经是 A，所以第一次 join 应该走 B。
    if room.player_a is None:
        room.player_a = BattlePlayer(user_id=user_id, side="a")
        return room, "a"

    if room.player_b is None:
        room.player_b = BattlePlayer(user_id=user_id, side="b")
        return room, "b"

    # A / B 都满了，剩下的都是观战
    return room, "spectate"
