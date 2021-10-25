from __future__ import annotations

import urllib.parse

import argon2
from databases.core import Database
from orm import BigInteger, String, ForeignKey, DateTime
from orm import Model
from orm import ModelRegistry

import env


# helper functions
def parse_database_conn_string(string: str):
    uri = urllib.parse.urlsplit(string)
    user_pass, host_port = uri.netloc.split('@')

    username, password = user_pass.split(':')
    host, port = host_port.split(':')

    return uri.scheme, username, password, host, int(port), uri.path[1:], uri


async def ensure_database_exists():
    driver, user, password, host, port, name, uri = parse_database_conn_string(env.db_uri)

    temp_database = Database(f'{driver}://{user}:{password}@{host}:{port}?{uri.query}')
    await temp_database.connect()

    # select the database
    exists = await temp_database.execute(
        'SELECT datname FROM pg_catalog.pg_database WHERE lower(datname) = lower(:database)', {
            'database': name
        })

    # create if it doesn't exist
    if not exists:
        # this is safe because `name` can only be edited by the site admins
        # even so, TODO: make parameterized
        await temp_database.execute('CREATE DATABASE ' + name)

    await temp_database.disconnect()


# database connection and orm
database = Database(env.db_uri)
models = ModelRegistry(database)

# passwords
password_hasher = argon2.PasswordHasher(
    time_cost=env.time_cost,
    memory_cost=env.memory_cost,
    parallelism=env.parallelism
)


# actual models
class User(Model):
    tablename = 'users'
    registry = models
    fields = {
        'id': BigInteger(primary_key=True, unique=True, read_only=True, allow_null=False),
        'name': String(max_length=env.max_name_length, allow_null=False),
        'handle': String(max_length=env.max_handle_length, allow_null=False, unique=True),

        # TODO: change 4 to a number that can actually calculate the approximate max length of a password
        'password': String(max_length=
                           (len(env.salt) + len(env.pepper) + env.max_password_length) * 4, allow_null=False),

        'timestamp': DateTime(allow_null=False),
    }


class Tweet(Model):
    tablename = 'tweets'
    registry = models
    fields = {
        'id': BigInteger(primary_key=True, unique=True, read_only=True, allow_null=False),
        'text': String(max_length=250, allow_null=False),
        'author': ForeignKey(User),
        'timestamp': DateTime(allow_null=False)
    }


# more helper functions that depend on the models above
def create_password(password: str) -> str:
    return password_hasher.hash(f'{env.salt}{password}{env.pepper}')


async def verify_password(user: User, possible_password: str) -> bool:
    try:
        password_hasher.verify(user.password, f'{env.salt}{possible_password}{env.pepper}')

        if password_hasher.check_needs_rehash(user.password):
            await user.update(password=create_password(possible_password))

        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
