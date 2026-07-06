# Judging VM runs linux/amd64. Building on Windows/amd64 produces that
# manifest by default, so a plain build is fine:
#   docker build -t <img>:latest . && docker push <img>:latest
FROM python:3.12-slim

WORKDIR /app

# Dependencies first for layer caching (empty for the echo skeleton).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

# Harness mounts /input and /output at runtime.
ENTRYPOINT ["python", "main.py"]
