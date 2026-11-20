# Python game engine (FastAPI) for Transopoly
FROM python:3.12-slim

# Don't write .pyc files, and print logs straight away (no buffering)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the engine code (board.json must sit next to gameserver.py)
COPY python/ .

# Run as a normal user, not root
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Container is "healthy" once the API answers
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json')" || exit 1

# One worker only: games live in this process's memory
CMD ["uvicorn", "gameserver:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]