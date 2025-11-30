"""Test is_prophylaxis_candidate directly."""
import sys
import os
import chess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rule_tagger_lichessbot'))

from rule_tagger2.legacy.prophylaxis import is_prophylaxis_candidate

# case_highest_1
fen1 = "r1b1kb1r/pppnqp1p/3p1np1/4p3/2PPP3/2N2N2/PP2BPPP/R1BQ1RK1 b kq - 1 7"
board1 = chess.Board(fen1)
move1 = chess.Move.from_uci("h7h6")

print(f"case_highest_1 (h7h6):")
print(f"  FEN: {fen1}")
print(f"  Move: {move1}")
print(f"  Move stack length: {len(board1.move_stack)}")
print(f"  Piece count: {sum(1 for sq in chess.SQUARES if board1.piece_at(sq) is not None)}")
print(f"  Gives check: {board1.gives_check(move1)}")
print(f"  Is capture: {board1.is_capture(move1)}")
print(f"  Is check (before move): {board1.is_check()}")
print(f"  is_prophylaxis_candidate: {is_prophylaxis_candidate(board1, move1)}")
print()

# case_highest_2
fen2 = "r1b1kb1r/pppnqp2/3p1npp/2P1p3/3PP3/2N2N2/PP2BPPP/R1BQ1RK1 b kq - 0 8"
board2 = chess.Board(fen2)
move2 = chess.Move.from_uci("a7a6")

print(f"case_highest_2 (a7a6):")
print(f"  FEN: {fen2}")
print(f"  Move: {move2}")
print(f"  Move stack length: {len(board2.move_stack)}")
print(f"  Piece count: {sum(1 for sq in chess.SQUARES if board2.piece_at(sq) is not None)}")
print(f"  Gives check: {board2.gives_check(move2)}")
print(f"  Is capture: {board2.is_capture(move2)}")
print(f"  Is check (before move): {board2.is_check()}")
print(f"  is_prophylaxis_candidate: {is_prophylaxis_candidate(board2, move2)}")
