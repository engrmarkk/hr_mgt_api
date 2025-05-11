from celery.schedules import crontab


CELERY_IMPORTS = ("workers.jobs.test_jobs",)
CELERY_TASK_RESULT_EXPIRES = 30
CELERY_TIMEZONE = "Africa/Lagos"

CELERY_ACCEPT_CONTENT = ["json", "msgpack", "yaml"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERYBEAT_SCHEDULE = {
    "test_cron": {
        "task": "workers.jobs.test_jobs.test_cron",
        "schedule": crontab(minute="29", hour="11"),
    },
}
