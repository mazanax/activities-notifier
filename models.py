from datetime import datetime
from math import ceil

from peewee import *

from settings import DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT

db = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)


class User(Model):
    telegram_id = IntegerField()
    username = CharField(null=True, max_length=255)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db


class Activity(Model):
    activity_id = CharField(max_length=6)
    title = CharField(max_length=255)
    unit = CharField(max_length=7)
    amount = IntegerField()
    user = ForeignKeyField(model=User)

    class Meta:
        database = db
        indexes = (
            (('id', 'user_id'), True),
        )


class RunningActivity(Activity):
    started_at = DateTimeField(default=datetime.now)
    notified_at = DateTimeField(default=None, null=True)
    total_time = IntegerField()

    @property
    def finished(self):
        return (datetime.utcnow() - self.started_at).seconds >= self.total_time

    @property
    def progress(self):
        return ceil((datetime.utcnow() - self.started_at).seconds / self.total_time * 100)
