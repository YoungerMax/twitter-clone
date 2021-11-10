import asyncio
import sys

import uvicorn
from databases.core import Database

from twitterclone import database
from twitterclone import env
from twitterclone import app


async def ensure_database_exists(db: Database, db_name: str):
    # select the database
    exists = await db.execute(
        'SELECT datname FROM pg_catalog.pg_database WHERE datname = :database', {
            'database': db_name
        })

    # create if it doesn't exist
    if not exists:
        # this is safe because `name` can only be edited by the site admins
        # even so, TODO: make parameterized
        await db.execute('CREATE DATABASE ' + db_name)


async def do_database():
    name = env.db_uri[env.db_uri.rindex('/') + 1:]
    uri = env.db_uri[:env.db_uri.rindex('/')]
    temp_database = Database(uri)

    try:
        await temp_database.connect()

        await ensure_database_exists(temp_database, name)
    except ConnectionError as err:
        print('#!#!#!#!#!#!#!#!#')
        print('Could not connect to database!\n')
        print('Error: ' + str(err))
        print('Database URI: ' + uri + '\n#!#!#!#!#!#!#!#!#')

        sys.exit(-1)

    await temp_database.disconnect()

if __name__ == '__main__':
    asyncio.run(do_database())
    database.registry.create_all()
    uvicorn.run(app)
