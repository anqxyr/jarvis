#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import concurrent.futures
import logging
import peewee
import queue

###############################################################################
# Global Constants And Variables
###############################################################################

log = logging.getLogger(__name__)
pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
queue = queue.Queue()


def queue_execution(fn, args=(), kwargs={}):
    queue.put(dict(fn=fn, args=args, kwargs=kwargs))
    pool.submit(async_write)

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


###############################################################################
# Helper Functions
###############################################################################


def async_write(buffer=[]):
    item = queue.get()
    buffer.append(item)
    if len(buffer) > 500 or queue.empty():
        log.debug('Processing {} queue items.'.format(len(buffer)))
        with db.transaction():
            write_buffer(buffer)
        buffer.clear()


def write_buffer(buffer):
    for item in buffer:
        try:
            item['fn'](*item.get('args', ()), **item.get('kwargs', {}))
        except:
            log.exception(
                'Exception while processing queue item: {}'
                .format(item))
        queue.task_done()


def create_tables(*tables):
    for table in tables:
        eval(table).create_table()
