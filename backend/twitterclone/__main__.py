import asyncio

from __init__ import app
import db
import uvicorn

if __name__ == '__main__':
    asyncio.run(db.ensure_database_exists())

    db.models.create_all()
    uvicorn.run(app)
