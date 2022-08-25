FROM python:3.7-slim

run apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "backend.wsgi:application", "--bind", "0:8000"]