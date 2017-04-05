#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import peewee
import playhouse.sqlite_ext
import playhouse.migrate


###############################################################################
# Database ORM Classes
###############################################################################


db = playhouse.sqlite_ext.SqliteExtDatabase(None, journal_mode='WAL')


class BaseModel(peewee.Model):
    """Peewee Base Table/Model Class."""

    def __iter__(self):
        return iter(self.select())

    def __len__(self):
        return self.select().count()

    @classmethod
    def all(cls):
        return list(cls.find())

    @classmethod
    def _apply_rules(cls, query, **rules):
        for column, value in rules.items():
            if column.endswith('_lower'):
                column = column[:-6]
                column = cls._meta.fields[column]
                column = peewee.fn.Lower(column)
            else:
                column = cls._meta.fields[column]

            query = query.where(column == value)
        return query

    @classmethod
    def find(cls, **rules):
        query = cls.select()
        return cls._apply_rules(query, **rules)

    @classmethod
    def find_one(cls, **rules):
        try:
            return cls.find(**rules).get()
        except cls.DoesNotExist:
            return None

    @classmethod
    def purge(cls, **rules):
        query = cls.delete()
        return cls._apply_rules(query, **rules).execute()

    class Meta:
        """Bind Model definitions to the database."""

        database = db


class Tell(BaseModel):
    """Database Tell Table."""

    sender = peewee.CharField()
    recipient = peewee.CharField(index=True)
    topic = peewee.CharField(null=True)
    text = peewee.TextField()
    time = peewee.DateTimeField()


class Message(BaseModel):
    """Database Message Table."""

    user = peewee.CharField(index=True, null=True)
    channel = peewee.CharField(index=True)
    time = peewee.DateTimeField()
    text = peewee.TextField()


class Quote(BaseModel):
    """Database Quote Table."""

    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    time = peewee.DateTimeField()
    text = peewee.TextField()


class Memo(BaseModel):
    """Database Memo Table."""

    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    text = peewee.TextField()


class Subscriber(BaseModel):
    """Database Subscriber Table."""

    user = peewee.CharField()
    topic = peewee.CharField(index=True)


class Restricted(BaseModel):
    """Database Restricted Table."""

    topic = peewee.CharField(index=True)


class Alert(BaseModel):
    """Database Alert Table."""

    user = peewee.CharField(index=True)
    time = peewee.DateTimeField()
    text = peewee.TextField()


class ChannelConfig(BaseModel):

    channel = peewee.CharField(index=True)
    memos = peewee.CharField(null=True)
    lcratings = peewee.BooleanField(null=True)
    keeplogs = peewee.BooleanField(null=True)



###############################################################################


def init(path):
    """Initialize the database, create missing tables."""
    db.init(path)

    try:
        migrator = playhouse.migrate.SqliteMigrator(db)
        playhouse.migrate.migrate(
            #migrator.drop_column('ChannelConfig', 'lcratings'),
            migrator.add_column(
                'ChannelConfig', 'keeplogs', peewee.BooleanField(null=True)),
            migrator.add_column(
                'ChannelConfig', 'lcratings', peewee.BooleanField(null=True)))
    except peewee.OperationalError:
        pass

    db.connect()
    db.create_tables([
        Tell, Message, Quote, Memo,
        Subscriber, Restricted, Alert, ChannelConfig], safe=True)
