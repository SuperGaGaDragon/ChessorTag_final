#!/usr/bin/env python3
"""UCI wrapper that routes Stockfish output through the chess style imitator."""

from __future__ import annotations

print("USING ENGINE FILE:", __file__, flush=True)

import logging
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import chess

from style_scorer import load_style_profile, pick_best_move
from tagger_bridge import tag_candidates_payload

print("[IMITATOR] VERSION OPENING_D6_TEST", file=sys.stderr, flush=True)

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("imitator_uci_engine")

# ==== Time limits for style imitator ====
MAX_THINK_TIME_S = 25.0     # total budget per move (Stockfish thinking budget target 20-30s)
# Carve out a smaller Stockfish slice so the remaining time (used by tagging/scoring) doubles.
STOCKFISH_FRACTION = 0.2    # portion reserved for Stockfish search
# =======================================


def maybe_opening_move(board: chess.Board, initial_fen: str | None = None) -> str | None:
    """
    Force the scripted opening on the very first half-move of a normal startpos game.

    - White's first move is always 1.Nf3 (from a standard starting position).
    - Black's first half-move is always 1...d6 as long as it is still Black's first turn.
    """
    is_startpos_game = initial_fen in (None, "startpos", chess.STARTING_FEN)
    if not is_startpos_game:
        return None
    if board.fullmove_number == 1 and board.turn == chess.WHITE:
        return "g1f3"
    if board.fullmove_number == 1 and board.turn == chess.BLACK:
        return "d7d6"
    return None

# The wrapper always enforces MAX_THINK_TIME_S as the upper bound; Stockfish
# only sees STOCKFISH_FRACTION of that time and ignores lichess-provided
# wtime/btime/movetime. The remaining time is reserved for tagging/scoring.

_DEFAULT_TARGET_PLAYER = "Kasparov"
TARGET_PLAYER = os.environ.get("TARGET_PLAYER", _DEFAULT_TARGET_PLAYER)
_DEFAULT_STOCKFISH = "/usr/local/bin/stockfish"
_USER_STOCKFISH = os.environ.get("CHESS_IMITATOR_STOCKFISH_PATH")
STOCKFISH_PATH = _USER_STOCKFISH or shutil.which("stockfish") or _DEFAULT_STOCKFISH
MULTIPV = int(os.environ.get("CHESS_IMITATOR_MULTIPV", "10"))


_STYLE_CACHE: Dict[str, Dict[str, Any]] = {}


def _get_style_profile(name: str) -> Dict[str, Any]:
    normalized = name.strip()
    if normalized in _STYLE_CACHE:
        return _STYLE_CACHE[normalized]
    profile = load_style_profile(normalized)
    _STYLE_CACHE[normalized] = profile
    return profile


def _parse_position(command: str, board: chess.Board) -> Tuple[chess.Board, Optional[str]]:
    tokens = command.split()
    if len(tokens) < 2:
        return board, None
    kind = tokens[1]
    next_tokens = tokens[2:]
    if kind == "startpos":
        board.reset()
        moves_idx = next_tokens.index("moves") + 1 if "moves" in next_tokens else None
        moves = next_tokens[moves_idx:] if moves_idx else []
        for move in moves:
            board.push_uci(move)
        return board, "startpos"
    if kind == "fen" and len(next_tokens) >= 6:
        fen = " ".join(next_tokens[:6])
        board = chess.Board(fen)
        if "moves" in next_tokens:
            moves_idx = next_tokens.index("moves") + 1
            for move in next_tokens[moves_idx:]:
                board.push_uci(move)
        return board, fen
    return board, None


class StockfishProcess:
    """Manage a long-lived Stockfish instance."""

    def __init__(self, path: str):
        self.path = path
        self.process = subprocess.Popen(
            [self.path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self._stdin_lock = threading.Lock()

    def send(self, command: str) -> None:
        if self.process.stdin is None:
            raise RuntimeError("Stockfish stdin closed.")
        with self._stdin_lock:
            self.process.stdin.write(f"{command}\n")
            self.process.stdin.flush()

    def readline(self) -> Optional[str]:
        if self.process.stdout is None:
            return None
        return self.process.stdout.readline()

    def drain(self, sentinel: str) -> None:
        while True:
            line = self.readline()
            if line is None:
                break
            if line.strip() == sentinel:
                break

    def initialize(self) -> None:
        self.send("uci")
        self.drain("uciok")
        self.send("isready")
        self.drain("readyok")

    def stop(self) -> None:
        self.send("stop")

    def quit(self) -> None:
        self.send("quit")
        self.process.wait()


class CommandReader(threading.Thread):
    """Read UCI lines from stdin without blocking the main loop."""

    def __init__(self, command_queue: queue.Queue[Optional[str]]):
        super().__init__(daemon=True)
        self._queue = command_queue

    def run(self) -> None:
        while True:
            line = sys.stdin.readline()
            if not line:
                self._queue.put(None)
                break
            self._queue.put(line.strip())


class SearchWorker(threading.Thread):
    """Run a Stockfish search and surface style-aware output."""

    def __init__(
        self,
        stockfish: StockfishProcess,
        go_command: str,
        position_fen: str,
        style_player: str,
        result_queue: queue.Queue[Dict[str, Any]],
        stop_event: threading.Event,
        multipv: int,
        initial_fen: Optional[str],
    ):
        super().__init__(daemon=True)
        self.stockfish = stockfish
        self.go_command = go_command
        self.position_fen = position_fen
        self.style_player = style_player
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.multipv = multipv
        self.initial_fen = initial_fen

    def run(self) -> None:
        best_move: Optional[str] = None
        candidates: List[Dict[str, Any]] = []
        selected: Optional[Dict[str, Any]] = None
        tagged_payload: Optional[Dict[str, Any]] = None
        sf_time = MAX_THINK_TIME_S * STOCKFISH_FRACTION
        move_time_ms = max(int(sf_time * 1000), 1)
        forced_go_command = f"go movetime {move_time_ms}"
        board = chess.Board(self.position_fen)
        opening_move = maybe_opening_move(board, self.initial_fen)
        if opening_move:
            print(
                f"[IMITATOR] opening move forced: {opening_move}",
                file=sys.stderr,
                flush=True,
            )
            self.result_queue.put(
                {
                    "final_move": opening_move,
                    "style_score": float("-inf"),
                    "tags": [],
                    "engine_bestmove": opening_move,
                    "fallback": opening_move,
                }
            )
            return
        t0 = time.time()
        error = False
        try:
            self.stockfish.send(f"setoption name MultiPV value {self.multipv}")
            logger.debug("Forcing search '%s' (ignoring %s).", forced_go_command, self.go_command)
            self.stockfish.send(forced_go_command)
            best_move, candidates = self._collect_candidates()
            if not candidates:
                raise RuntimeError("Stockfish emitted no candidates.")
        except Exception:
            logger.exception("Style scoring failed; falling back to engine best move.")
            error = True
        t1 = time.time()
        spent = t1 - t0
        remain = MAX_THINK_TIME_S - spent
        used_tagger = False
        tagger_spent = 0.0
        if not error:
            tagger_start = time.time()
            payload = {"fen": self.position_fen, "candidates": candidates}
            tagged_payload = tag_candidates_payload(payload)
            tagger_spent = time.time() - tagger_start
            if tagger_spent > remain:
                print(
                    f"[IMITATOR] tagging exceeded remaining budget "
                    f"({tagger_spent:.3f}s > {remain:.3f}s).",
                    file=sys.stderr,
                    flush=True,
                )
            style_profile = _get_style_profile(self.style_player)
            selected = pick_best_move(tagged_payload, style_profile)
            used_tagger = True
        print(
            f"[IMITATOR] sf_time={sf_time:.3f}s, spent={spent:.3f}s, remain={remain:.3f}s,"
            f" used_tagger={used_tagger}, tagger_spent={tagger_spent:.3f}s",
            file=sys.stderr,
            flush=True,
        )
        best_move = best_move if best_move else (candidates[0]["uci"] if candidates else "")
        if not selected:
            if candidates:
                selected = dict(candidates[0])
            else:
                selected = {"uci": best_move, "tags": [], "sf_eval": 0.0}
            selected.setdefault("style_score", float("-inf"))
        self.result_queue.put(
            {
                "final_move": selected.get("uci"),
                "style_score": selected.get("style_score"),
                "tags": selected.get("tags", []),
                "engine_bestmove": best_move,
                "fallback": best_move,
            }
        )

    def _collect_candidates(self) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        seen: Dict[int, Dict[str, Any]] = {}
        best_move: Optional[str] = None
        stop_sent = False
        while True:
            line = self.stockfish.readline()
            if line is None:
                break
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("info"):
                info = self._parse_info(stripped)
                if not info:
                    continue
                multipv = info.get("multipv", 1)
                if multipv > self.multipv:
                    continue
                pv = info.get("pv", [])
                if not pv:
                    continue
                score_cp = self._score_to_cp(info.get("score_cp"), info.get("mate"))
                seen[multipv] = {
                    "multipv": multipv,
                    "uci": pv[0],
                    "sf_eval": score_cp,
                    "sf_pv": " ".join(pv),
                    "engine_meta": {"engine_path": self.stockfish.path},
                }
            elif stripped.startswith("bestmove"):
                tokens = stripped.split()
                if len(tokens) > 1:
                    best_move = tokens[1]
                break
            if self.stop_event.is_set() and not stop_sent:
                self.stockfish.send("stop")
                stop_sent = True
        sorted_candidates = [seen[idx] for idx in sorted(seen)]
        if not sorted_candidates and best_move:
            sorted_candidates = [
                {
                    "multipv": 1,
                    "uci": best_move,
                    "sf_eval": 0.0,
                    "sf_pv": best_move,
                    "engine_meta": {"engine_path": self.stockfish.path},
                }
            ]
        return best_move, sorted_candidates

    @staticmethod
    def _score_to_cp(score_cp: Optional[int], mate: Optional[int]) -> float:
        if score_cp is not None:
            return float(score_cp)
        if mate is not None:
            return 100000.0 if mate > 0 else -100000.0
        return 0.0

    @staticmethod
    def _parse_info(line: str) -> Dict[str, Any]:
        fields: Dict[str, Any] = {}
        tokens = line.split()
        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token == "multipv" and i + 1 < len(tokens):
                fields["multipv"] = int(tokens[i + 1])
                i += 2
            elif token == "score" and i + 2 < len(tokens):
                if tokens[i + 1] == "cp":
                    fields["score_cp"] = int(tokens[i + 2])
                    i += 3
                elif tokens[i + 1] == "mate":
                    fields["mate"] = int(tokens[i + 2])
                    i += 3
                else:
                    i += 1
            elif token == "pv":
                fields["pv"] = tokens[i + 1 :]
                break
            else:
                i += 1
        fields.setdefault("multipv", 1)
        return fields


def main() -> None:
    stockfish = StockfishProcess(STOCKFISH_PATH)
    stockfish.initialize()
    current_board = chess.Board()
    current_fen = current_board.fen()
    current_initial_fen: Optional[str] = "startpos"
    command_queue: queue.Queue[Optional[str]] = queue.Queue()
    result_queue: queue.Queue[Dict[str, Any]] = queue.Queue()
    reader = CommandReader(command_queue)
    reader.start()
    active_search: Optional[SearchWorker] = None
    stop_event = threading.Event()
    running = True

    while running:
        while True:
            try:
                result = result_queue.get_nowait()
            except queue.Empty:
                break
            logger.info(
                "Selected %s score=%s tags=%s (engine best=%s)",
                result["final_move"],
                result["style_score"],
                result["tags"],
                result["engine_bestmove"],
            )
            move = result["final_move"] or result["fallback"]
            if move:
                print(f"bestmove {move}", flush=True)
            active_search = None
            stop_event.clear()

        try:
            command = command_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        if command is None:
            break
        if command == "uci":
            print("id name chess_imitator", flush=True)
            print("id author codex", flush=True)
            print("uciok", flush=True)
            continue
        if command == "isready":
            stockfish.send("isready")
            stockfish.drain("readyok")
            print("readyok", flush=True)
            continue
        if command == "ucinewgame":
            stockfish.send("ucinewgame")
            continue
        if command.startswith("setoption"):
            stockfish.send(command)
            continue
        if command.startswith("position"):
            stockfish.send(command)
            parsed_board, parsed_initial = _parse_position(command, current_board)
            current_board = parsed_board
            if parsed_initial is not None:
                current_initial_fen = parsed_initial
            current_fen = current_board.fen()
            continue
        if command.startswith("go"):
            if active_search and active_search.is_alive():
                logger.warning("Ignoring new go while previous search still running.")
                continue
            stop_event.clear()
            stop_event = threading.Event()
            active_search = SearchWorker(
                stockfish=stockfish,
                go_command=command,
                position_fen=current_fen,
                style_player=TARGET_PLAYER,
                result_queue=result_queue,
                stop_event=stop_event,
                multipv=MULTIPV,
                initial_fen=current_initial_fen,
            )
            active_search.start()
            continue
        if command == "stop":
            if active_search and active_search.is_alive():
                stop_event.set()
                stockfish.send("stop")
            continue
        if command == "quit":
            running = False
            break
        stockfish.send(command)

    if active_search and active_search.is_alive():
        stop_event.set()
        stockfish.send("stop")
        active_search.join()
    stockfish.quit()


if __name__ == "__main__":
    main()
