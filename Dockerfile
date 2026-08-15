# ============================================================
# Single-container image: PHP web + Python scraper pipeline.
# api.php runs `venv/bin/python main.py ...` via shell_exec,
# so PHP and Python MUST live in the same container sharing
# one filesystem and the venv at /app/venv.
# ============================================================
FROM python:3.12-slim

# --- System deps: PHP CLI + SQLite PDO driver + build tools ---
# php-cli          : serves webapp-php via `php -S`
# php-sqlite3      : PDO sqlite driver used by koneksi.php
# php-mbstring     : mb_* functions used in api.php
# build-essential  : some Python wheels (numpy/scipy) may compile
RUN apt-get update && apt-get install -y --no-install-recommends \
        php-cli \
        php-sqlite3 \
        php-mbstring \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python venv at /app/venv (api.php expects this exact path) ---
ENV VENV=/app/venv
RUN python -m venv "$VENV"
ENV PATH="$VENV/bin:$PATH"

# Install Python deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Copy application source ---
# .dockerignore keeps out venv/, secrets, pdfs, local db.
COPY src/ ./src/
COPY webapp-php/ ./webapp-php/
COPY main.py setup_env.py view_db.py ./
COPY config/settings.json ./config/settings.json

# Bundled lexicon seed files (positive/negative.tsv) if labeler falls back to local
COPY data/positive.tsv data/negative.tsv ./data/

# --- Non-root user; owns app + writable data/config/results dirs ---
RUN useradd -m -u 10001 appuser \
    && mkdir -p /app/data /app/results /app/config \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["php", "-S", "0.0.0.0:8000", "-t", "webapp-php"]
