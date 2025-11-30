from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from . import models
from .auth_api import router as auth_router
from .study_api import router as study_router
from .workspace_api import router as workspace_router

# 自动创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 允许前端访问后端
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://chessortag.org",
    "https://www.chessortag.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 study API
app.include_router(auth_router)
app.include_router(study_router)
app.include_router(workspace_router)


@app.get("/")
def root():
    return {"message": "Backend running."}
