FROM python:3.9-slim

WORKDIR /app

COPY ./shared /app/shared
COPY ./edge-agent/src /app/edge-agent/src
COPY ./edge-agent/requirements.txt /app/edge-agent/requirements.txt

RUN pip install --no-cache-dir -r /app/edge-agent/requirements.txt

WORKDIR /app/edge-agent

CMD ["python", "src/main.py"]
