FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir redis==5.2.1
COPY worker.py .
CMD ["python", "-u", "worker.py"]
