# demo_user sandbox

Isolated frontend + backend so the main `website` folder stays untouched.

## Run backend (FastAPI + SQLite)
```bash
cd /Users/alex/Desktop/chess_report_page
python3 -m venv demo_user/.venv
source demo_user/.venv/bin/activate
pip install -r demo_user/backend/requirements.txt
uvicorn demo_user.backend.main:app --reload --port 8001
```

## Run frontend
Serve only from inside `demo_user` to avoid file:// issues.
```bash
cd /Users/alex/Desktop/chess_report_page/demo_user
python3 -m http.server 8000
```
Then open `http://localhost:8000/home.html`.

## Flow
- `home.html`: click **New study** → POST `/api/studies` → redirect to `study.html?id=...`
- `study.html`: drag a piece to make a move → POST `/api/studies/{id}/moves` with `move_index`, `fen_before`, `move_san`
- Reload `study.html?id=...` → GET `/api/studies/{id}` → chessboard + move list replays saved moves.
