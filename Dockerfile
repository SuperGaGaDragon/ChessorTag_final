# 1. 选择基础镜像
FROM python:3.11-slim

# 2. 安装 Stockfish 引擎
RUN apt-get update && \
    apt-get install -y --no-install-recommends stockfish && \
    rm -rf /var/lib/apt/lists/*

ENV STOCKFISH_PATH="/usr/games/stockfish"

# 3. 工作目录
WORKDIR /app

# 4. 安装 Python 依赖（用根目录的 requirements.txt）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 拷贝后端代码
COPY backend/ ./backend/

# 6. 拷贝 predictor 资源（superchess predictor / rule tagger）
COPY chess_imitator/ ./chess_imitator/

# 7. 启动 FastAPI（Railway 默认会把 PORT 传进来）
ENV PORT=8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
