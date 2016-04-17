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
    recipient = peewee.CharField(index=True)
    topic = peewee.CharField(null=True)
    text = peewee.TextField()
    time = peewee.DateTimeField()


class Message(BaseModel):
    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    time = peewee.CharField()
    text = peewee.TextField()


class Quote(BaseModel):
    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    time = peewee.CharField()
    text = peewee.TextField()


class Rem(BaseModel):
    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    text = peewee.TextField()


class Subscriber(BaseModel):
    user = peewee.CharField()
    topic = peewee.CharField(index=True)


class Restricted(BaseModel):
    topic = peewee.CharField(index=True)


class Alert(BaseModel):
    user = peewee.CharField(index=True)
    time = peewee.DateTimeField()
    text = peewee.TextField()
