FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY indexer.py .

RUN pip install web3 psycopg2-binary

CMD ["python", "indexer.py"]
