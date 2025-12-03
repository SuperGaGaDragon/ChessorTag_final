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


def create_room(user_id: Optional[str]) -> BattleRoom:
    game_id = generate_game_id()
    room = BattleRoom(game_id=game_id)
    room.player_a = BattlePlayer(user_id=user_id, side="a")
    rooms[game_id] = room
    return room


def join_room(game_id: str, user_id: Optional[str]) -> Optional[BattleRoom]:
    room = rooms.get(game_id)
    if not room:
        return None
    if room.player_a is None:
        room.player_a = BattlePlayer(user_id=user_id, side="a")
    elif room.player_b is None:
        room.player_b = BattlePlayer(user_id=user_id, side="b")
    # If both filled, allow spectate (no player slot added)
    return room
