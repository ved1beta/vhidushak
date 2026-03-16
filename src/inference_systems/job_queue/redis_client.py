import redis
import json

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

QUEUE_NAME = "inference_queue"
RESULT_PREFIX = "result:"


def push_job(job):
    redis_client.rpush(QUEUE_NAME, json.dumps(job))


def pop_job():
    job = redis_client.blpop(QUEUE_NAME)
    return json.loads(job[1])


def store_result(request_id, result):
    redis_client.set(RESULT_PREFIX + request_id, json.dumps(result))


def get_result(request_id):
    result = redis_client.get(RESULT_PREFIX + request_id)
    return json.loads(result) if result else None