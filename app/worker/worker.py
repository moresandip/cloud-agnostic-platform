import os
import signal
import time
import redis
stopping = False
def handle_shutdown(signum, frame):
    global stopping
    print("Shutdown requested. Finishing current job before exit.", flush=True)
    stopping = True
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)
client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)
print("Worker started. Waiting for jobs...", flush=True)
while not stopping:
    try:
        item = client.blpop("jobs", timeout=2)
        if item is None:
            continue
        job = item[1]
        print(f"Started job: {job}", flush=True)
        # Demo jobs take 2 seconds. Set JOB_SECONDS for longer test jobs.
        duration = int(os.getenv("JOB_SECONDS", "2"))
        time.sleep(max(0, min(duration, 60)))
        print(f"Finished job: {job}", flush=True)
    except redis.RedisError as error:
        print(f"Redis connection error: {error}", flush=True)
        time.sleep(2)
print("Worker stopped.", flush=True)
