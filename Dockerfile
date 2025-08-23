FROM python:3.11.6-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


RUN apt-get update \
 && apt-get install -y --no-install-recommends git build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
 && python -m pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt


WORKDIR /VJ-Forward-Bot
COPY . /VJ-Forward-Bot


CMD ["bash","-lc","gunicorn app:app & python3 main.py"]
