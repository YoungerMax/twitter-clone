import asyncio

import uvicorn
from databases.core import Database

import database
import env
from __init__ import app


async def ensure_database_exists():
    name = env.db_uri[env.db_uri.rindex('/') + 1:]
    temp_database = Database(env.db_uri[:env.db_uri.rindex('/')])
    await temp_database.connect()

    # select the database
    exists = await temp_database.execute(
        'SELECT datname FROM pg_catalog.pg_database WHERE datname = :database', {
            'database': name
        })

    # create if it doesn't exist
    if not exists:
        # this is safe because `name` can only be edited by the site admins
        # even so, TODO: make parameterized
        await temp_database.execute('CREATE DATABASE ' + name)

    await temp_database.disconnect()


if __name__ == '__main__':
    asyncio.run(ensure_database_exists())
    database.registry.create_all()
    uvicorn.run(app)
