import redis
import json
import os

redis_client = redis.StrictRedis(host=os.getenv(
    "REDIS_HOST", "127.0.0.1"), port=6379, db=0)
# redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

NAMESPACE = "robotAnalysis:"


def _namespaced_key(job_id):
    return f"{NAMESPACE}{job_id}"


def init_job(job_id):
    data = {
        "upload_status": "pending",
        "analysis_status": "pending",
        "error": None,
        "filename": None,
        "result": None
    }
    redis_client.set(_namespaced_key(job_id), json.dumps(data))


def update_job_status(job_id, stage, status, error=None, filename=None):
    namespace_id = _namespaced_key(job_id)
    job_data = json.loads(redis_client.get(namespace_id))
    job_data[stage] = status
    if error:
        job_data["error"] = error
    if filename:
        job_data["filename"] = filename
    redis_client.set(namespace_id, json.dumps(job_data))


def get_job_status(job_id):
    namespace_id = _namespaced_key(job_id)
    job_data = redis_client.get(namespace_id)
    if job_data:
        return json.loads(job_data)
    return None


def update_job_result(job_id, result):
    namespace_id = _namespaced_key(job_id)
    job_data = redis_client.get(namespace_id)
    if job_data:
        job_data = json.loads(job_data)
        job_data["result"] = result
        redis_client.set(namespace_id, json.dumps(job_data))
        print("update job result", result)
        return True
    else:
        print(f"Job ID {namespace_id} not found in Redis.")
        return False


def clear_namespace():
    """
    clean ups for this namespace
    """
    keys = redis_client.keys(f"{NAMESPACE}*")
    if keys:
        redis_client.delete(*keys)
        print(f"Deleted {len(keys)} keys under the namespace '{NAMESPACE}'")
        return len(keys)
    else:
        print("No keys found under the namespace.")
        return 0
