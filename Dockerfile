# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies in an isolated layer for cache efficiency
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY main.py .
COPY agent.py .
COPY database.py .
COPY mcp_tools.py .
COPY assets/ ./assets/
COPY frontend/ ./frontend/

# Cloud Run injects PORT at runtime; default to 8080
ENV PORT=8080

# Non-root user for security best practices
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8080

# Use exec form for proper signal handling
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1"]
