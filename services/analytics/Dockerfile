FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY flow.py .

RUN pip install psycopg2-binary

CMD ["python", "flow.py"]
