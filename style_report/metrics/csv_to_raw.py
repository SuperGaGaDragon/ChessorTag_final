"""
Translate black-box outputs into a normalized raw structure for downstream metrics.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import chess
import chess.pgn


def _canonicalize(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def _matches_player(name: str, target_tokens: Iterable[str]) -> bool:
    canon = _canonicalize(name)
    return any(token in canon for token in target_tokens)


def _sanitize_identifier(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum() or ch in ("-", "_")).strip("_")


def _parse_int(value: str | None) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _result_from_header(result: str | None, player_color: str) -> str:
    if not result:
        return "unknown"
    result = result.strip()
    if result == "1-0":
        return "win" if player_color == "white" else "loss"
    if result == "0-1":
        return "loss" if player_color == "white" else "win"
    if result in {"1/2-1/2", "1/2"}:
        return "draw"
    return "unknown"


@dataclass
class MoveRecord:
    ply: int
    uci: str
    cp_eval: Optional[float]
    best_cp_eval: Optional[float]
    eval_delta_cp: Optional[float]
    cp_before: Optional[float]
    phase: str
    tags: list[str] = field(default_factory=list)
    has_queen: Optional[bool] = None

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "MoveRecord":
        eval_info = payload.get("eval", {}) or {}
        played = eval_info.get("played")
        best = eval_info.get("best")
        before = eval_info.get("before")
        delta_cp = None
        if played is not None and best is not None:
            delta_cp = (float(played) - float(best)) * 100

        has_queen = None
        fen_before = payload.get("fen_before")
        if fen_before:
            try:
                board = chess.Board(fen_before)
                has_queen = bool(board.queens)
            except ValueError:
                has_queen = None

        return cls(
            ply=int(payload.get("move_index", 0)),
            uci=str(payload.get("move")),
            cp_eval=float(played) * 100 if played is not None else None,
            best_cp_eval=float(best) * 100 if best is not None else None,
            eval_delta_cp=delta_cp,
            cp_before=float(before) * 100 if before is not None else None,
            phase=str(payload.get("phase") or "unknown"),
            tags=list(payload.get("tags") or []),
            has_queen=has_queen,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ply": self.ply,
            "uci": self.uci,
            "cp_eval": self.cp_eval,
            "best_cp_eval": self.best_cp_eval,
            "eval_delta_cp": self.eval_delta_cp,
            "cp_before": self.cp_before,
            "phase": self.phase,
            "tags": self.tags,
            "has_queen": self.has_queen,
        }


def _load_moves(moves_path: Path) -> dict[int, dict[str, Any]]:
    games: dict[int, dict[str, Any]] = {}
    if not moves_path.exists():
        return games

    with moves_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            game_index = record.get("game_index")
            if not isinstance(game_index, int):
                continue
            move = MoveRecord.from_json(record)
            entry = games.setdefault(
                game_index,
                {"game_id": record.get("game_id"), "moves": []},
            )
            entry["moves"].append(move)

    for info in games.values():
        info["moves"].sort(key=lambda m: m.ply)
    return games


def _load_pgn_metadata(pgn_path: Path, player_id: str, player_name: Optional[str] = None) -> dict[int, dict[str, Any]]:
    """
    Return metadata keyed by game_index in the order they appear in the PGN file.
    """
    meta: dict[int, dict[str, Any]] = {}
    if not pgn_path.exists():
        return meta

    target_tokens = {_canonicalize(player_id)}
    target_tokens.add(_canonicalize(player_id.replace("test", "", 1)))
    if player_name:
        target_tokens.add(_canonicalize(player_name))
    target_tokens = {token for token in target_tokens if token}

    game_index = 0
    with pgn_path.open(encoding="utf-8") as handle:
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break
            white = game.headers.get("White", "") or ""
            black = game.headers.get("Black", "") or ""
            color = None
            opponent = ""
            if _matches_player(white, target_tokens):
                color = "white"
                opponent = black
            elif _matches_player(black, target_tokens):
                color = "black"
                opponent = white
            else:
                continue

            board = game.board()
            san_moves: list[str] = []
            for idx, move in enumerate(game.mainline_moves()):
                if idx >= 8:  # first 4 full moves (8 plies)
                    break
                san_moves.append(board.san(move))
                board.push(move)

            formatted_moves: list[str] = []
            move_number = 1
            for i in range(0, len(san_moves), 2):
                white_san = san_moves[i]
                black_san = san_moves[i + 1] if i + 1 < len(san_moves) else ""
                if black_san:
                    formatted_moves.append(f"{move_number}. {white_san} {black_san}")
                else:
                    formatted_moves.append(f"{move_number}. {white_san}")
                move_number += 1

            game_index += 1
            opponent_elo = game.headers.get("BlackElo") if color == "white" else game.headers.get("WhiteElo")
            meta[game_index] = {
                "color": color,
                "opponent": opponent,
                "opponent_elo": _parse_int(opponent_elo),
                "date": game.headers.get("Date") or "",
                "result": _result_from_header(game.headers.get("Result"), color),
                "eco": game.headers.get("ECO") or "",
                "opening": game.headers.get("Opening") or "",
                "variation": game.headers.get("Variation") or "",
                "first_moves": " ".join(formatted_moves),
            }
    return meta


def _parse_csv(csv_path: Path) -> dict[str, dict[str, float]]:
    distribution: dict[str, dict[str, float]] = {}
    if not csv_path.exists():
        return distribution

    with csv_path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            tag = row.get("tag")
            if not tag:
                continue
            try:
                count = int(row.get("count") or 0)
            except ValueError:
                count = 0
            try:
                ratio = float(row.get("ratio") or 0.0)
            except ValueError:
                ratio = 0.0
            distribution[tag] = {"count": count, "ratio": ratio}
    return distribution


def csv_to_raw(
    csv_path: Path,
    *,
    player_id: str,
    pgn_path: Path | None = None,
    moves_path: Path | None = None,
    player_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert the black-box CSV plus optional PGN/moves into raw.json payload.
    """
    distribution = _parse_csv(csv_path)
    moves_map = _load_moves(moves_path) if moves_path else {}
    meta_map = _load_pgn_metadata(pgn_path, player_id, player_name=player_name) if pgn_path else {}

    if moves_map:
        game_indexes = set(moves_map.keys())
    else:
        game_indexes = set(meta_map.keys())
    games: List[Dict[str, Any]] = []
    total_moves = 0

    for game_index in sorted(game_indexes):
        move_info = moves_map.get(game_index, {})
        meta = meta_map.get(game_index, {})
        moves = [m.to_dict() for m in move_info.get("moves", [])]
        total_moves += len(moves)

        game_id = move_info.get("game_id")
        if not game_id:
            game_id = f"{_sanitize_identifier(player_id) or 'player'}_game_{game_index}"

        games.append(
            {
                "game_index": game_index,
                "game_id": game_id,
                "color": meta.get("color", "unknown"),
                "result": meta.get("result", "unknown"),
                "opponent": meta.get("opponent"),
                "opponent_elo": meta.get("opponent_elo"),
                "date": meta.get("date"),
                "eco": meta.get("eco") or "",
                "opening": meta.get("opening") or "",
                "variation": meta.get("variation") or "",
                "first_moves": meta.get("first_moves") or "",
                "moves": moves,
            }
        )

    raw: Dict[str, Any] = {
        "player_id": player_id,
        "player_name": player_name or player_id,
        "tag_distribution": distribution,
        "games": games,
        "totals": {
            "games": len(games),
            "moves": total_moves,
        },
    }
    return raw
