FROM python:3.11-slim

# Install system tools
RUN apt-get update && apt-get install -y \
    stockfish \
    && rm -rf /var/lib/apt/lists/*

# Set stockfish env
ENV STOCKFISH_PATH="/usr/games/stockfish"

# Create working dir
WORKDIR /app

# Copy backend
COPY backend/ /app/backend/

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Railway uses 8080)
EXPOSE 8080

# Start FastAPI using uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
