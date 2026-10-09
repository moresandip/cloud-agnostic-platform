FROM python:3.13-slim

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade \
    "redis==5.2.1" \
    "msgpack>=1.2.1" \
    "setuptools>=78.1.1" \
    "urllib3>=2.8.0"

COPY worker.py .

CMD ["python", "-u", "worker.py"]