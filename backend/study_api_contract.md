# Study API contract (draft v1)

Front-end pages:
- `/website/home.html`
- `/website/study_board.html`

Goal: allow user to create / load a "study" from their own games (PGN/FEN),
then for each node request engine + style-tag + LLM commentary.

---

## 1. Create / import a study

`POST /api/study/import_pgn`

Request JSON:

```json
{
  "pgn": "<full PGN text>",
  "title": "optional human title",
  "source": "user_upload | lichess_game | other",
  "owner_id": "demo-user-1"
}


Response JSON (draft):

{
  "study_id": "study_2025_0001",
  "title": "optional title or from PGN",
  "owner_id": "demo-user-1",
  "initial_fen": "startpos",
  "moves": [
    {
      "index": 0,
      "san": "e4",
      "fen_after": "....",
      "side": "white",
      "node_id": "n0"
    }
  ]
}


v1 实现可以先不真正解析 PGN，只返回 study_id 和原始 pgn，但接口形状不要改。

2. Load an existing study

GET /api/study/{study_id}

Response JSON (简化版)：

{
  "study_id": "study_2025_0001",
  "title": "My study",
  "owner_id": "demo-user-1",
  "nodes": [
    {
      "node_id": "n0",
      "move_index": 0,
      "san": "e4",
      "fen_after": "...",
      "parent_id": null
    }
  ]
}

3. Get GM-style move predictions for a node

POST /api/study/{study_id}/predict_moves

Request JSON:

{
  "node_id": "n0",
  "fen": "current FEN",
  "profiles": ["Kasparov", "Petrosian", "Tal"]
}


Response JSON:

{
  "study_id": "study_2025_0001",
  "node_id": "n0",
  "predictions": [
    {
      "profile": "Kasparov",
      "moves": [
        {"uci": "e2e4", "san": "e4", "score_cp": 20, "prob": 0.45},
        {"uci": "d2d4", "san": "d4", "score_cp": 15, "prob": 0.30}
      ]
    }
  ]
}


这里将来真正接你的 style-tag + imitator。前端左侧「GM move predictions」就用这个数据。

4. Request LLM commentary for a node

POST /api/study/{study_id}/comment

Request JSON:

{
  "node_id": "n0",
  "fen": "current FEN",
  "player_style": "Kasparov",
  "language": "en"
}


Response JSON:

{
  "study_id": "study_2025_0001",
  "node_id": "n0",
  "comment_id": "c123",
  "player_style": "Kasparov",
  "text": "LLM-generated commentary here.",
  "created_at": "2025-11-29T12:00:00Z"
}


前端右下角的 LLM comment 区就用这个。

5. Save study state (optional v1)

POST /api/study/{study_id}/save

Body:

{
  "nodes": [...],
  "comments": [...]
}


Response:

{"ok": true}


---
