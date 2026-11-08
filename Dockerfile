FROM python:3.12-slim
LABEL org.opencontainers.image.title="FundingLens AI" \
      org.opencontainers.image.source="https://github.com/OWNER/REPO"
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 DATA_DIR=/app/data
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN useradd --create-home --uid 10001 app && mkdir -p /app/data/documents && chown -R app:app /app/data
COPY VERSION ./VERSION
COPY backend ./backend
COPY frontend ./frontend
COPY demo_data ./demo_data
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:%s/api/health'%os.getenv('PORT','8000'),timeout=4)" || exit 1
# One worker on purpose: the login rate limiter is in-process memory. Use Redis before scaling out.
CMD ["sh","-c","exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
