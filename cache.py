from functools import lru_cache

@lru_cache(maxsize=1)
def cached_health_status():
    return {"status": "ok"}
