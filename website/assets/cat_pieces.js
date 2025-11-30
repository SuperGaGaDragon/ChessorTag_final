// Cat piece theme mapping helper
// Exported function: getCatPieceImage(piece) where piece = { type: 'p', color: 'w'|'b' }

function getCatPieceImage(piece) {
  if (!piece) return null;
  const base = "../assets/cat_pieces/";
  switch (piece.type) {
    case "k":
      return base + "King.png";
    case "q":
      return base + "Queen.png";
    case "r":
      return base + "Rook.png";
    case "n":
      return base + "Knight.png";
    case "b":
      return base + (piece.color === "w" ? "white_bishop.png" : "black_bishop.png");
    case "p":
      return base + (piece.color === "b" ? "black_pawn.png" : "pawn.png");
    default:
      return null;
  }
}
