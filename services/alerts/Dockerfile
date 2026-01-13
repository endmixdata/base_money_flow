FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY alerts.py .

RUN pip install psycopg2-binary requests

CMD ["python", "alerts.py"]
