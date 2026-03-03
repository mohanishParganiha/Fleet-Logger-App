FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update  && apt-get install  -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . /app

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD [ "gunicorn","vehicle_fleet.wsgi:application" , "-c", "gunicorn_config.py"]