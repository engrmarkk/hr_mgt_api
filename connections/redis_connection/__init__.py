import redis
from constants import REDIS_URL
from logger import logger


class RedisConnection:
    def __init__(self, url=REDIS_URL):
        try:
            self.connection = redis.Redis.from_url(url, decode_responses=True)
        except Exception as e:
            logger.exception(e)

    def get_connection(self):
        return self.connection

    def close_connection(self):
        self.connection.close()

    def set(self, key, value, expire=None):
        return self.connection.set(key, value, ex=expire)

    def get(self, key):
        return self.connection.get(key)

    def delete(self, key):
        return self.connection.delete(key)

    def pipeline(self):
        return self.connection.pipeline()

    def partial_delete(self, key):
        pattern = f"{key}*"
        deleted_count = 0

        cursor = "0"
        while cursor != 0:
            cursor, keys = self.connection.scan(
                cursor=cursor, match=pattern, count=1000
            )

            if keys:
                deleted_count += self.connection.delete(*keys)

        return deleted_count


redis_conn = RedisConnection()
