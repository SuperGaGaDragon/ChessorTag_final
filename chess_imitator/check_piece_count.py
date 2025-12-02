"""Check piece count for the two test cases."""
import chess

# case_highest_1
fen1 = "r1b1kb1r/pppnqp1p/3p1np1/4p3/2PPP3/2N2N2/PP2BPPP/R1BQ1RK1 b kq - 1 7"
board1 = chess.Board(fen1)
pieces1 = sum(1 for sq in chess.SQUARES if board1.piece_at(sq) is not None)

print(f"case_highest_1 (h7h6):")
print(f"  FEN: {fen1}")
print(f"  Piece count: {pieces1}")
print(f"  Would pass is_prophylaxis_candidate piece check: {pieces1 < 32}")
print()

# case_highest_2
fen2 = "r1b1kb1r/pppnqp2/3p1npp/2P1p3/3PP3/2N2N2/PP2BPPP/R1BQ1RK1 b kq - 0 8"
board2 = chess.Board(fen2)
pieces2 = sum(1 for sq in chess.SQUARES if board2.piece_at(sq) is not None)

print(f"case_highest_2 (a7a6):")
print(f"  FEN: {fen2}")
print(f"  Piece count: {pieces2}")
print(f"  Would pass is_prophylaxis_candidate piece check: {pieces2 < 32}")
