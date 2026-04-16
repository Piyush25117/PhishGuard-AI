# ── Stage 1: Build / train the model ──────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
WORKDIR /build/backend
RUN python train_model.py


# ── Stage 2: Runtime image ─────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/

# Copy the trained model from the build stage
COPY --from=builder /build/backend/model.pkl ./backend/model.pkl

# Copy frontend static files (served by Flask in production)
COPY frontend/ ./frontend/

EXPOSE 5000

# Use gunicorn for production
CMD ["gunicorn", \
     "--chdir", "backend", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--timeout", "120", \
     "app:create_app()"]
