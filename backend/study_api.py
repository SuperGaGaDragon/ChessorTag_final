import os
import io
import uuid
from typing import Optional, List, Any, Dict
import json
from pathlib import Path
import sys
from datetime import datetime
from openai import OpenAI

import chess
import chess.pgn
import chess.engine
from fastapi import APIRouter, FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import get_db
from .models import Study


router = APIRouter(prefix="/api/study", tags=["study"])

# If someone runs `uvicorn backend.study_api:app`, expose a FastAPI app and include the router.
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


# ----------------------------
# Request/Response Models
# ----------------------------

class ImportPGNRequest(BaseModel):
    pgn: str
    title: Optional[str] = None
    source: Optional[str] = "user_upload"
    owner_id: Optional[str] = "demo-user"


class StudyImportResponse(BaseModel):
    study_id: str
    title: str
    owner_id: str
    raw_pgn: str  # keep raw PGN for now
    san_moves: List[str]
    message: str = "Study imported (PGN parsed: mainline SAN moves)."


class EngineTopRequest(BaseModel):
    fen: str
    depth: int = 12
    multipv: int = 5
    engine_path: Optional[str] = None  # if not set, will use env STOCKFISH_PATH or "stockfish"


class EngineTopMove(BaseModel):
    uci: str
    san: str
    cp: Optional[int] = None
    mate: Optional[int] = None
    depth: Optional[int] = None
    pv_san: List[str]


class EngineTopResponse(BaseModel):
    moves: List[EngineTopMove]
    info: str


class CoachNoteRequest(BaseModel):
    player_id: Optional[str] = None
    player_file: Optional[str] = None
    prompt: Optional[str] = None
    fen: Optional[str] = None  # kept for backward compat; treated as fen_after
    fen_before: Optional[str] = None
    fen_after: Optional[str] = None
    move_color: Optional[str] = None  # 'w' or 'b' for the move just played
    move_san: Optional[str] = None
    move_index: Optional[int] = None
    predictions: Optional[dict] = None


class CoachNoteResponse(BaseModel):
    text: str
    source: str = "local_template"
    player_id: Optional[str] = None


class AnalyzeRequest(BaseModel):
    fen: str
    engine_path: Optional[str] = None


class AnalyzeMove(BaseModel):
    san: str
    uci: str
    score_cp: Optional[float] = None
    probabilities: Optional[dict] = None
    tags: Optional[List[str]] = None
    tag_flags: Optional[dict] = None


class AnalyzeResponse(BaseModel):
    study_id: str
    players: List[str]
    moves: List[AnalyzeMove]
    metadata: Optional[dict] = None


class StudyGetResponse(BaseModel):
    study_id: str
    title: str | None
    data: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True

# lazy-loaded predictor deps
_predictor_ready = False
_predictor_err = None
_fetch_engine_moves = None
_tag_moves = None
_load_player_summaries = None
_compute_move_probabilities = None

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ----------------------------
# Helpers
# ----------------------------

def _players_dir() -> Path:
    """
    Locate the players directory. Repo contains a trailing-space folder
    named 'chess_imitator ' so we resolve it by stripping whitespace.
    """
    base = Path(__file__).resolve().parent.parent
    for child in base.iterdir():
        if child.name.strip() == "chess_imitator":
            players = child / "players"
            if players.exists():
                return players
    # fallback: assume sibling named exactly
    return base / "chess_imitator" / "players"


def _load_player_profile(player_file: Optional[str]) -> dict:
    if not player_file:
        return {}
    path = _players_dir() / player_file
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _top_tags(profile: dict, n: int = 3) -> List[str]:
    tags = profile.get("tag_weights") or {}
    sorted_tags = sorted(tags.items(), key=lambda kv: kv[1], reverse=True)
    return [k.replace("_", " ") for k, _ in sorted_tags[:n]]


def _best_moves_from_prediction(pred: Optional[dict], limit: int = 3) -> List[str]:
    if not pred:
        return []
    moves = pred.get("moves") or []
    top = []
    for mv in moves[:limit]:
        san = mv.get("san") or mv.get("uci") or ""
        prob = None
        probs = mv.get("probabilities") or {}
        if probs:
            # pick max probability if present
            try:
                prob = max(probs.values())
            except Exception:
                prob = None
        if prob is not None:
            top.append(f"{san} ({prob*100:.1f}%)")
        else:
            top.append(san)
    return top


def _build_local_note(req: CoachNoteRequest) -> str:
    profile = _load_player_profile(req.player_file)
    player_name = (profile.get("player_name") or req.player_id or "这位棋手").strip()
    move_label = req.move_san or "当前局面"
    tags = _top_tags(profile, 3)
    tag_line = ""
    if tags:
        tag_line = f" 我的风格标签重心在：{', '.join(tags)}。"
    best_moves = _best_moves_from_prediction(req.predictions, 3)
    move_line = ""
    if best_moves:
        move_line = f" 此处模型给出的首选/备选是：{'; '.join(best_moves)}。"
    fen_before = req.fen_before or req.fen
    fen_after = req.fen_after or req.fen
    if fen_before and fen_after:
        fen_line = f" 选择前的 FEN: {fen_before}。落子后的 FEN: {fen_after}。"
    elif fen_after:
        fen_line = f" 当前 FEN: {fen_after}。"
    else:
        fen_line = ""
    mover = req.move_color
    mover_line = " 当前轮到: " + ("白" if mover == "w" else "黑" if mover == "b" else "未知") if mover else ""
    takeaway = "Takeaway：确保走法服务于整体计划，同时持续评估对手的反击资源，避免让出关键节奏。"

    paragraphs = [
        f"我是 {player_name}。结合我的资料，我正在思考这一手：{move_label}.{tag_line}",
        f"{fen_line}{mover_line}我会优先考虑控制弱点格、保持子力协调，并在稳固安全的前提下寻找主动权。{move_line}",
        "我选择的方案兼顾了安全与压力：不只是单步收益，更是为后续节奏铺垫。",
        takeaway,
    ]
    return "\n\n".join([p for p in paragraphs if p.strip()])


def _ensure_predictor():
    """Lazy import predictor pipeline (engine + tagger + probability)"""
    global _predictor_ready, _predictor_err
    global _fetch_engine_moves, _tag_moves, _load_player_summaries, _compute_move_probabilities  # noqa: PLW0603
    if _predictor_ready:
        return
    base = Path(__file__).resolve().parent.parent
    predictor_root = None
    for child in base.iterdir():
        if child.name.strip() == "chess_imitator":
            predictor_root = child / "rule_tagger_lichessbot"
            break
    if predictor_root is None:
        _predictor_err = "predictor root not found"
        return
    sys.path.insert(0, str(predictor_root))
    try:
        from superchess_predictor.backend.engine_utils import fetch_engine_moves as fem  # type: ignore
        from superchess_predictor.backend.tagger_utils import tag_moves as tm  # type: ignore
        from superchess_predictor.backend.file_utils import load_player_summaries as lps  # type: ignore
        from superchess_predictor.backend.predictor import compute_move_probabilities as cmp  # type: ignore
    except Exception as exc:  # pragma: no cover
        _predictor_err = str(exc)
        return
    _fetch_engine_moves = fem
    _tag_moves = tm
    _load_player_summaries = lps
    _compute_move_probabilities = cmp
    _predictor_ready = True


def _predict_with_pipeline(fen: str, engine_path: Optional[str]) -> AnalyzeResponse:
    _ensure_predictor()
    if not _predictor_ready or not _fetch_engine_moves or not _tag_moves or not _load_player_summaries or not _compute_move_probabilities:
        raise HTTPException(status_code=500, detail=_predictor_err or "predictor not ready")

    tagged_moves = _tag_moves(
        fen,
        _fetch_engine_moves(
            fen,
            engine_path=engine_path,
        ),
        engine_path=engine_path,
    )
    player_summaries = _load_player_summaries(
        Path(__file__).resolve().parent.parent / "chess_imitator " / "rule_tagger_lichessbot" / "superchess_predictor" / "reports"
    )
    if not player_summaries:
        raise HTTPException(status_code=500, detail="No player summaries found.")

    probabilities = _compute_move_probabilities(
        tagged_moves,
        {name: summary["tag_distribution"] for name, summary in player_summaries.items()},
    )

    moves_output = []
    for move, probs in zip(tagged_moves, probabilities):
        moves_output.append(
            AnalyzeMove(
                san=move["san"],
                uci=move["uci"],
                score_cp=move.get("score_cp"),
                tags=move.get("tags", []),
                tag_flags=move.get("analysis", {}).get("tags", {}).get("all", {}),
                probabilities=probs,
            )
        )

    payload = AnalyzeResponse(
        study_id="",
        players=list(player_summaries.keys()),
        moves=moves_output,
        metadata={"engine_depth": 14, "top_n": len(moves_output)},
    )
    return payload


def _log_predictor_call(fen: str, result: AnalyzeResponse, engine_path: Optional[str]):
    try:
        log_dir = Path(__file__).resolve().parent.parent / "website" / "predictor_log"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"log_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        entry = {
            "ts_utc": datetime.utcnow().isoformat() + "Z",
            "fen": fen,
            "engine_path": engine_path,
            "players": result.players,
            "moves": [m.model_dump() for m in result.moves],
            "metadata": result.metadata,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ----------------------------
# Endpoint: import PGN
# ----------------------------

@router.post("/import_pgn", response_model=StudyImportResponse)
def import_pgn(req: ImportPGNRequest):
    if not req.pgn.strip():
        raise HTTPException(status_code=400, detail="Empty PGN.")

    # --- 用 python-chess 解析 PGN 主线 ---
    try:
        pgn_io = io.StringIO(req.pgn)
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            raise ValueError("Could not read PGN game.")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid PGN: {exc}")

    board = game.board()
    san_moves: List[str] = []
    for move in game.mainline_moves():
        san = board.san(move)
        san_moves.append(san)
        board.push(move)

    study_id = f"study_{uuid.uuid4().hex[:8]}"

    return StudyImportResponse(
        study_id=study_id,
        title=req.title or (game.headers.get("Event") or "Imported Study"),
        owner_id=req.owner_id,
        raw_pgn=req.pgn.strip(),
        san_moves=san_moves,
    )


# ----------------------------
# Endpoint: engine top moves (local engine)
# ----------------------------

@router.post("/engine_top", response_model=EngineTopResponse)
def engine_top(req: EngineTopRequest):
    engine_path = req.engine_path or os.getenv("STOCKFISH_PATH") or "stockfish"
    board = chess.Board(req.fen)

    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Engine not available: {exc}")

    try:
        limit = chess.engine.Limit(depth=req.depth)
        infos = engine.analyse(board, limit, multipv=req.multipv)
    except Exception as exc:
        engine.quit()
        raise HTTPException(status_code=500, detail=f"Engine error: {exc}")

    moves: List[EngineTopMove] = []
    for entry in infos:
        pv = entry.get("pv")
        if not pv:
            continue
        first = pv[0]
        tmp_board = board.copy()
        pv_san: List[str] = []
        for mv in pv:
            try:
                pv_san.append(tmp_board.san(mv))
                tmp_board.push(mv)
            except Exception:
                break
        cp = None
        mate = None
        score = entry.get("score")
        if score:
            try:
                if score.is_mate():
                    mate = score.white().mate()
                elif score.is_cp():
                    cp = score.white().score()
            except Exception:
                pass
        try:
            san_first = board.san(first)
        except Exception:
            san_first = first.uci()

        moves.append(
            EngineTopMove(
                uci=first.uci(),
                san=san_first,
                cp=cp,
                mate=mate,
                depth=entry.get("depth"),
                pv_san=pv_san,
            )
        )

    engine.quit()

    return EngineTopResponse(
        moves=moves,
        info=f"engine={engine_path} depth={req.depth} multipv={req.multipv}",
    )


# ----------------------------
# Endpoint: predictor analyze (engine + tagger + GM prob)
# ----------------------------

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    payload = _predict_with_pipeline(req.fen, req.engine_path)
    _log_predictor_call(req.fen, payload, req.engine_path)

    result_data = payload.model_dump()
    result_data.pop("study_id", None)
    result_json = jsonable_encoder(result_data)

    study = Study(
        title=getattr(req, "title", None),
        data=result_json,
        is_public=True,
        owner_id=None,
    )
    db.add(study)
    db.commit()
    db.refresh(study)

    return AnalyzeResponse(
        study_id=study.id,
        **result_json,
    )


# ----------------------------
# Endpoint: coach note (LLM stub with local fallback)
# ----------------------------

@router.post("/coach_note", response_model=CoachNoteResponse, tags=["study"])
def coach_note(req: CoachNoteRequest):
    """
    Generate a coach-style note via OpenAI; fallback to local template on errors.
    """
    profile = _load_player_profile(req.player_file)
    context = {
        "player_id": req.player_id,
        "player_profile": profile,
        "fen_before": req.fen_before or req.fen,
        "fen_after": req.fen_after or req.fen,
        "move_san": req.move_san,
        "move_index": req.move_index,
        "predictions": req.predictions,
        "move_color": req.move_color,
    }

    messages = [
        {
            "role": "system",
            "content": (
                "你是这个棋手，请根据这个棋手在 players/ 里的风格数据，"
                "用第一人称解释你在这局棋当前这一手的思路。100-400词，看情况决定长短。"
                "需要包括：1）为什么下这步而不是其它候选；"
                "2）从这步棋里，对自己或学生有什么 takeaway / lesson。"
                "所有输出必须为英文。"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(context, ensure_ascii=False),
        },
    ]

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
        )
        text = resp.choices[0].message.content.strip()
        return CoachNoteResponse(
            text=text,
            source="llm",
            player_id=req.player_id,
        )
    except Exception as exc:
        fallback = _build_local_note(req)
        return CoachNoteResponse(
            text=fallback,
            source=f"local_fallback ({exc})",
            player_id=req.player_id,
        )


@router.post("/test_db")
def test_db(db: Session = Depends(get_db)):
    dummy_data = {"hello": "world"}
    study = Study(
        title="test",
        data=dummy_data,
        is_public=True,
        owner_id=None,
    )
    db.add(study)
    db.commit()
    db.refresh(study)
    return {"study_id": study.id}


@router.get("/{study_id}", response_model=StudyGetResponse)
def get_study(study_id: str, db: Session = Depends(get_db)):
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.is_public == True)
        .first()
    )
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    return StudyGetResponse(
        study_id=study.id,
        title=study.title,
        data=study.data,
        created_at=study.created_at,
    )
