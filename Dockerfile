FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update  && apt-get install  -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt /app/

ARG BUILD_ENV=production

RUN pip install --upgrade pip && \
    pip install -r requirements.txt \
    && if [ "$BUILD_ENV" = "development" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt; \
        fi

COPY . /app

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD [ "gunicorn","config.wsgi:application" , "-c", "gunicorn_config.py"]