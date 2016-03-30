#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import peewee

###############################################################################
# Database ORM Classes
###############################################################################


db = peewee.SqliteDatabase('jarvis.db')


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
