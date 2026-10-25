FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY apps/api/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock && useradd --create-home magribi
COPY --chown=magribi:magribi apps/api/ ./
USER magribi
EXPOSE 8000
CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --threads 2 --timeout 30 --access-logfile - --error-logfile -"]
