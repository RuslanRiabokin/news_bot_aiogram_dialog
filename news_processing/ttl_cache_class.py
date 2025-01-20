import time

class TTLCache:
    def __init__(self, ttl: int):
        self.ttl = ttl
        self.cache = {}

    def add(self, key: str, channel_id: str):
        current_time = time.time()
        full_key = f"{key}_{channel_id}"
        self.cache[full_key] = current_time

    def contains(self, key: str, channel_id: str) -> bool:
        current_time = time.time()
        full_key = f"{key}_{channel_id}"
        if full_key in self.cache:
            if current_time - self.cache[full_key] < self.ttl:
                return True
            else:
                del self.cache[full_key]
        return False

    async def clean_up(self):
        current_time = time.time()
        keys_to_delete = [key for key, timestamp in self.cache.items() if current_time - timestamp >= self.ttl]
        for key in keys_to_delete:
            del self.cache[key]