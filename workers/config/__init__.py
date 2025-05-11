from celery import Celery, shared_task
import os
from datetime import datetime
import workers.schedule as celeryConfig
from dotenv import load_dotenv
from logger import logger

load_dotenv()


def make_celery():
    celery = Celery(
        "workers",
        backend=f"redis://{os.environ.get('REDIS_HOST')}:{os.environ.get('REDIS_PORT')}",
        broker=f"redis://{os.environ.get('REDIS_HOST')}:{os.environ.get('REDIS_PORT')}",
    )
    celery.conf.update(vars(celeryConfig))

    return celery


celery = make_celery()


@shared_task
def add_numbers(x, y):
    logger.info("Adding")
    return x + y
