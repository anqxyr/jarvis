#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import peewee
from playhouse.sqlite_ext import SqliteExtDatabase


###############################################################################
# Database ORM Classes
###############################################################################


db = SqliteExtDatabase('jarvis.db', journal_mode='WAL')


class BaseModel(peewee.Model):

    class Meta:
        database = db


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
