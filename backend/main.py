from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from . import models
from backend.study_api import router as study_router
from backend.workspace_api import router as workspace_router

# 自动创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 允许前端访问后端
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 study API
app.include_router(study_router)
app.include_router(workspace_router)


@app.get("/")
def root():
    return {"message": "Backend running."}
