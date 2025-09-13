FROM python:3.11-slim

RUN pip install uv

WORKDIR /app
COPY pyproject.toml .
RUN uv pip install --system -r pyproject.toml
COPY backend ./backend

EXPOSE 8000

# Healthcheck: curl localhost:8000/health
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
