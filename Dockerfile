# ── Stage 1: install dependencies ──────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app

# Install only production dependencies (no torch, no tensorboard)
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --user -r requirements-prod.txt

# ── Stage 2: runtime ────────────────────────────────────
FROM python:3.12-slim
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source
COPY . .

# Cloud Run sends traffic to PORT (default 8080)
ENV PORT=8080
EXPOSE 8080

# Health check — Cloud Run uses this
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8080}/health')"

# Run the server — binds to 0.0.0.0:$PORT automatically
CMD ["python", "-m", "visualization.server"]
