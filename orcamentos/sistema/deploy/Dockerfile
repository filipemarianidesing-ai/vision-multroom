FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core postgresql-client \
    && apt-get clean
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m orc && mkdir -p /dados && chown orc /dados
USER orc
ENV ORC_DADOS=/dados
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py inicializar && python manage.py collectstatic --noinput -v0 && gunicorn config.wsgi -b 0.0.0.0:8000 -w 3 --timeout 600"]
