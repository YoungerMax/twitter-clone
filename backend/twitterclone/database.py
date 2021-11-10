from __future__ import annotations

from datetime import datetime

from databases.core import Database
from orm import ModelRegistry, Model, BigInteger, String, DateTime, ForeignKey
from pydantic.main import BaseModel

from twitterclone import env

database = Database(env.db_uri)
registry = ModelRegistry(database)


class User(Model):
    tablename = 'users'
    registry = registry
    fields = {
        'id': BigInteger(primary_key=True, unique=True, read_only=True, allow_null=False),
        'name': String(max_length=env.max_name_length, allow_null=False),
        'handle': String(max_length=env.max_handle_length, allow_null=False, unique=True),

        # TODO: change 4 to a number that can actually calculate the approximate max length of a password
        'password': String(max_length=(len(env.salt) + len(env.pepper) + env.max_password_length) * 4,
                           allow_null=False),

        'timestamp': DateTime(allow_null=False),
    }


class Tweet(Model):
    tablename = 'tweets'
    registry = registry
    fields = {
        'id': BigInteger(primary_key=True, unique=True, read_only=True, allow_null=False),
        'text': String(max_length=250, allow_null=False),
        'author': ForeignKey(User),
        'timestamp': DateTime(allow_null=False)
    }


# pydantic
class UserSchema(BaseModel):
    id: int
    name: str
    handle: str
    timestamp: datetime


class TweetSchema(BaseModel):
    id: int
    author: UserSchema
    text: str
    timestamp: datetime
