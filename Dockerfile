FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update  && apt-get install  -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . /app
# Copy the entrypoint script and ensure it has executable rights inside the container
COPY ./docker-entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/code/entrypoint.sh"]

CMD [ "gunicorn","config.wsgi:application" , "-c", "gunicorn_config.py"]