import datetime

import orm.exceptions
from asyncpg import UniqueViolationError
from fastapi import FastAPI, Path, Form, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.exceptions import HTTPException
import re

from db import database
import db
import env

app = FastAPI(
    title='Twitter Clone'
)

basic_auth = HTTPBasic()


async def get_user_logged_in(credentials: HTTPBasicCredentials = Depends(basic_auth)):
    handle, password = credentials.username, credentials.password

    try:
        user = await db.User.objects.get(handle=handle)
    except orm.NoMatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='user not found',
            headers={'WWW-Authenticate': 'Basic'}
        )

    if not await db.verify_password(user, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='invalid authentication credentials',
            headers={'WWW-Authenticate': 'Basic'}
        )

    return user


# paths


# users
@app.post('/users/create')
async def create_user(
        name: str = Form(..., title='User nickname', description='You can change this later'),
        handle: str = Form(..., title='User handle', description='You can\'t change this later'),
        password: str = Form(..., title='User password', description='Your password defines the security of your '
                                                                     'account!')
):
    # preconditions
    # name
    if not env.min_name_length < len(name) < env.max_name_length:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'name has to be more than {env.min_name_length} characters and less than {env.max_name_length}'
        )

    if not re.compile(env.name_regex).match(name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'name has to match {env.name_regex}'
        )

    # handle
    if not env.min_handle_length < len(name) < env.max_handle_length:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'handle has to be more than {env.min_handle_length} characters and less than '
                   f'{env.max_handle_length}'
        )

    if not re.compile(env.handle_regex).match(name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'handle has to match {env.handle_regex}'
        )

    # password
    if not env.min_password_length < len(name) < env.max_password_length:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'password has to be more than {env.min_password_length} characters and less than '
                   f'{env.max_password_length}'
        )

    # actually create the user
    try:
        await db.User.objects.create(
            id=await db.User.objects.count() + 1,
            name=name,
            handle=handle,
            timestamp=datetime.datetime.now(),
            password=db.create_password(password)
        )
    except UniqueViolationError as error:
        # TODO: fix this up
        return error

    return await db.User.objects.get(handle=handle)


@app.get('/users/@{handle}')
async def get_user(
        handle: str = Path(..., title='Handle', description='Handle of target user')
):
    try:
        # TODO: exclude password
        return await db.User.objects.get(handle=handle)
    except orm.exceptions.NoMatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='user not found'
        )


@app.get('/users/@{handle}/tweets')
async def get_tweets_by_user(
        handle: str = Path(..., title='Handle', description='Handle of target user')
):
    tweets = await db.Tweet.objects.filter(author=await get_user(handle)).all()

    for tweet in tweets:
        await tweet.author.load()

    return tweets


# tweets
@app.post('/tweet')
async def create_tweet(
        text: str = Form(..., title='Tweet contents', description='The tweet text itself'),
        user_logged_in: db.User = Depends(get_user_logged_in)
):
    tweet = await db.Tweet.objects.create(
        id=await db.Tweet.objects.count() + 1,
        text=text,
        author=user_logged_in,
        timestamp=datetime.datetime.now()
    )

    await tweet.author.load()

    return tweet


@app.on_event('startup')
async def start():
    await database.connect()


@app.on_event('shutdown')
async def stop():
    await database.disconnect()
