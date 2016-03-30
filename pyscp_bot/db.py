#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import concurrent.futures
import peewee

###############################################################################
# Global Constants And Variables
###############################################################################

pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)


def queue_execution(fn, args=(), kwargs={}):
    pool.submit(fn, *args, **kwargs)

###############################################################################
# Database ORM Classes
###############################################################################


db = peewee.SqliteDatabase('jarvis.db')


class BaseModel(peewee.Model):

    class Meta:
        database = db

    @classmethod
    def create(cls, **kwargs):
        queue_execution(fn=super().create, kwargs=kwargs)

    @classmethod
    def create_table(cls):
        queue_execution(fn=super().create_table, args=(True,))

    @classmethod
    def delete_records(cls, *args):
        queue_execution(
            fn=lambda x: super(BaseModel, cls).delete().where(*x).execute(),
            args=args)


class Tell(BaseModel):
    sender = peewee.CharField()
    recipient = peewee.CharField()
    message = peewee.TextField()
    time = peewee.DateTimeField()


class Message(BaseModel):
    user = peewee.CharField()
    channel = peewee.CharField()
    time = peewee.CharField()
    text = peewee.TextField()
