# syntax=docker/dockerfile:1.6

# ============================================================
# 1) BASE IMAGE
# ============================================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ="Asia/Almaty"

WORKDIR /app

# ============================================================
# 2) INSTALL SYSTEM DEPENDENCIES (CACHED)
# ============================================================
FROM base AS builder

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# ============================================================
# 3) INSTALL PYTHON DEPENDENCIES (CACHED)
# ============================================================
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================
# 4) FINAL RUNTIME STAGE
# ============================================================
FROM base AS final

WORKDIR /app

# Копируем зависимости из builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Добавляем весь проект
COPY . .

# Создаём нужные папки
RUN mkdir -p logs data

CMD ["python", "main.py"]
