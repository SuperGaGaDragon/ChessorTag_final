# 1. 选一个轻量 Python 基础镜像
FROM python:3.11-slim

# 2. 安装系统依赖 + stockfish
RUN apt-get update && \
    apt-get install -y --no-install-recommends stockfish && \
    rm -rf /var/lib/apt/lists/*

# Debian/Ubuntu 的 stockfish 默认安装在 /usr/games/stockfish
ENV STOCKFISH_PATH=/usr/games/stockfish

# 3. 把代码拷进容器
WORKDIR /app
COPY . .

# 4. 安装 Python 依赖
RUN pip install --no-cache-dir -r backend/requirements.txt

# 5. 启动 FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
