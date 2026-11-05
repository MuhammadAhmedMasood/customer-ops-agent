# ---- Stage 1: build -------------------------------------------------------
# Install dependencies into a virtualenv. pip, its cache and any build files
# stay in this stage and never reach the final image.
FROM python:3.14-slim AS builder

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---- Stage 2: runtime -----------------------------------------------------
# A clean slim image with only the virtualenv and our code.
FROM python:3.14-slim

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    APP_BASE_URL=http://localhost:8080

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app/ app/
COPY data/ data/

# Build the demo database, then run as a non-root user that can write to it.
RUN python data/seed.py \
    && useradd --create-home appuser \
    && chown -R appuser /app/data
USER appuser

EXPOSE 8080
# Cloud Run sets $PORT; sh -c lets the shell fill it in.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
