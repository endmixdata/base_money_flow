FROM python:3.11-slim

WORKDIR /app

RUN pip install psycopg2-binary requests

COPY daily_summary.py .

CMD ["python", "daily_summary.py"]
