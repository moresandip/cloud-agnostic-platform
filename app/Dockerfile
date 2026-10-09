
FROM python:3.13-slim

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade \
    "msgpack>=1.2.1" \
    "setuptools>=78.1.1" \
    "urllib3>=2.8.0"

COPY server.py .

EXPOSE 8080

CMD ["python", "server.py"]