"""
Command-line helper that ingests PGN batches and exports qualifying "quick win" games.

This mirrors the FastAPI backend logic:
  - filters games by rating range / move count
  - runs a Stockfish engine at given depth
  - counts per-side evaluation drops larger than `threshold_cp`
  - returns games where the winner makes <= `max_errors`

Outputs the qualifying games as a PGN file and prints a summary per match.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional

import chess
import chess.engine
import chess.pgn


@dataclass
class QuickWinConfig:
    min_rating: int = 0
    max_rating: int = 4000
    max_moves: int = 40
    max_errors: int = 1
    depth: int = 14
    threshold_cp: int = 60
    engine_path: Optional[str] = None
    max_results: int = 20


@dataclass
class QuickWinMatch:
    title: str
    pgn: str
    result: str
    winner: str
    move_count: int
    white_elo: Optional[int]
    black_elo: Optional[int]
    errors: Dict[str, int]


@dataclass
class QuickWinsResult:
    total_games_scanned: int
    qualifying_games: List[QuickWinMatch]
    engine_info: str


def _parse_rating(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits) if digits else None


def _winner_from_result(result: Optional[str]) -> Optional[str]:
    if result == "1-0":
        return "white"
    if result == "0-1":
        return "black"
    return None


def _iterate_pgn_games(pgn_text: str) -> Iterator[chess.pgn.Game]:
    stream = io.StringIO(pgn_text)
    while True:
        game = chess.pgn.read_game(stream)
        if game is None:
            break
        yield game


def _export_game_pgn(game: chess.pgn.Game) -> str:
    exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
    return game.accept(exporter)


def _score_cp(engine: chess.engine.SimpleEngine, board: chess.Board, limit: chess.engine.Limit) -> Optional[int]:
    try:
        info = engine.analyse(board, limit)
    except Exception as exc:
        raise RuntimeError(f"Engine analysis failure: {exc}")
    score = info.get("score")
    if not score:
        return None
    try:
        if score.is_cp():
            return score.white().score()
    except Exception:
        return None
    return None


def _evaluate_game(
    game: chess.pgn.Game,
    engine: chess.engine.SimpleEngine,
    limit: chess.engine.Limit,
    config: QuickWinConfig,
) -> Optional[QuickWinMatch]:
    moves = list(game.mainline_moves())
    move_count = len(moves)
    max_moves = config.max_moves if config.max_moves > 0 else None
    if max_moves and move_count > max_moves:
        return None
    white_elo = _parse_rating(game.headers.get("WhiteElo"))
    black_elo = _parse_rating(game.headers.get("BlackElo"))
    if white_elo is None or black_elo is None:
        return None
    if white_elo < config.min_rating or white_elo > config.max_rating:
        return None
    if black_elo < config.min_rating or black_elo > config.max_rating:
        return None
    winner = _winner_from_result(game.headers.get("Result"))
    if not winner:
        return None
    errors = {"white": 0, "black": 0}
    board = game.board()
    for move in moves:
        turn_color = board.turn
        before_cp = _score_cp(engine, board, limit)
        board.push(move)
        after_cp = _score_cp(engine, board, limit)
        if before_cp is None or after_cp is None:
            continue
        turn_sign = 1 if turn_color == chess.WHITE else -1
        delta = (after_cp - before_cp) * turn_sign
        if delta < -config.threshold_cp:
            side = "white" if turn_color == chess.WHITE else "black"
            errors[side] += 1
    if errors[winner] > config.max_errors:
        return None
    return QuickWinMatch(
        title=game.headers.get("Event") or game.headers.get("Site") or "Imported Quick Win",
        pgn=_export_game_pgn(game),
        result=game.headers.get("Result") or "*",
        winner=winner,
        move_count=move_count,
        white_elo=white_elo,
        black_elo=black_elo,
        errors=errors,
    )


def find_quick_wins(pgn_text: str, config: QuickWinConfig) -> QuickWinsResult:
    engine_path = config.engine_path or "stockfish"
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as exc:
        raise RuntimeError(f"Unable to start engine ({engine_path}): {exc}")
    limit = chess.engine.Limit(depth=config.depth)
    total_games = 0
    matches: List[QuickWinMatch] = []
    try:
        for game in _iterate_pgn_games(pgn_text):
            total_games += 1
            match = _evaluate_game(game, engine, limit, config)
            if match:
                matches.append(match)
                if len(matches) >= config.max_results:
                    break
    finally:
        engine.quit()
    return QuickWinsResult(
        total_games_scanned=total_games,
        qualifying_games=matches,
        engine_info=f"{engine_path} depth={config.depth}",
    )


def _build_summary(result: QuickWinsResult) -> str:
    lines = [
        f"Scanned {result.total_games_scanned} game(s)",
        f"Qualifying quick win(s): {len(result.qualifying_games)}",
        f"Engine info: {result.engine_info}",
    ]
    for idx, match in enumerate(result.qualifying_games, start=1):
        lines.append(
            f"[{idx}] {match.title} ({match.winner} wins in {match.move_count} moves)"
            f" | Result: {match.result}"
            f" | Ratings: white {match.white_elo} / black {match.black_elo}"
            f" | Errors: white {match.errors['white']} / black {match.errors['black']}"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Extract quick-win PGNs according to 实现方案落地.txt")
    parser.add_argument("input", type=Path, help="PGN file or stdin (- for stdin)", nargs="?", default="-")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("quick_wins.pgn"),
        help="Destination PGN file that receives qualifying games (defaults to quick_wins.pgn)",
    )
    parser.add_argument("--metadata", type=Path, help="Optional JSON file that stores result metadata")
    parser.add_argument("--min-rating", type=int, default=0, help="Minimum rating for both players")
    parser.add_argument("--max-rating", type=int, default=4000, help="Maximum rating for both players")
    parser.add_argument("--max-moves", type=int, default=40, help="Maximum moves per game")
    parser.add_argument("--max-errors", type=int, default=1, help="Maximum errors allowed for winner")
    parser.add_argument("--depth", type=int, default=14, help="Engine depth for evaluation")
    parser.add_argument("--threshold-cp", type=int, default=60, help="CP drop threshold for errors")
    parser.add_argument("--engine-path", type=str, help="Path to the Stockfish binary")
    parser.add_argument("--max-results", type=int, default=20, help="Cap on quick win games collected")
    args = parser.parse_args()

    if args.input == Path("-"):
        pgn_data = sys.stdin.read()
    else:
        pgn_data = args.input.read_text(encoding="utf-8")
    if not pgn_data.strip():
        parser.error("PGN input is empty.")

    config = QuickWinConfig(
        min_rating=args.min_rating,
        max_rating=args.max_rating,
        max_moves=args.max_moves,
        max_errors=args.max_errors,
        depth=args.depth,
        threshold_cp=args.threshold_cp,
        engine_path=args.engine_path,
        max_results=args.max_results,
    )

    result = find_quick_wins(pgn_data, config)
    if args.metadata:
        args.metadata.write_text(
            json.dumps(
                {
                    "total_games_scanned": result.total_games_scanned,
                    "qualifying_games": [match.__dict__ for match in result.qualifying_games],
                    "engine_info": result.engine_info,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    stdout = _build_summary(result)
    print(stdout)
    if result.qualifying_games:
        args.output.write_text(
            "\n\n".join(match.pgn for match in result.qualifying_games),
            encoding="utf-8",
        )
        print(f"\nWritten matching PGNs to {args.output}")
    else:
        print("\nNo quick wins met the criteria; output file not written.")


if __name__ == "__main__":
    main()
