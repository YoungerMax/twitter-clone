import re
from datetime import datetime

# argon2 is argon2-cffi
import argon2
import orm.exceptions
from fastapi import FastAPI, Path, Form, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from twitterclone import env
from twitterclone import database
from twitterclone.database import User, UserSchema, TweetSchema

from starlette.middleware.cors import CORSMiddleware

app = FastAPI(
    title='Twitter Clone'
)

app.add_middleware(CORSMiddleware, allow_origins=['*'])

basic_auth = HTTPBasic()

password_hasher = argon2.PasswordHasher(
    time_cost=env.time_cost,
    memory_cost=env.memory_cost,
    parallelism=env.parallelism
)


async def get_user_logged_in(credentials: HTTPBasicCredentials = Depends(basic_auth)) -> User:
    handle, password = credentials.username, credentials.password

    try:
        user = await database.User.objects.get(handle=handle)

        try:
            password_hasher.verify(user.password, f'{env.salt}{password}{env.pepper}')

            if password_hasher.check_needs_rehash(user.password):
                await user.update(password=password_hasher.hash(f'{env.salt}{password}{env.pepper}'))

        except argon2.exceptions.VerificationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='invalid authentication credentials',
                headers={'WWW-Authenticate': 'Basic'}
            )

        return user
    except orm.NoMatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='user not found',
            headers={'WWW-Authenticate': 'Basic'}
        )


# paths


# users
@app.post('/users/create')
async def create_user(
        name: str = Form(..., title='User nickname', description='You can change this later'),
        handle: str = Form(..., title='User handle', description='You can\'t change this later'),
        password: str = Form(..., title='User password', description='Your password defines the security of your '
                                                                     'account!'),
):
    # preconditions
    if not env.min_name_length < len(name) < env.max_name_length:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'name has to be more than {env.min_name_length} characters and less than '
                   f'{env.max_name_length}'
        )

    if not re.search(env.name_regex, name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'name has to match {env.name_regex}'
        )

    # handle
    if not env.min_handle_length < len(handle) < env.max_handle_length:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'handle has to be more than {env.min_handle_length} characters and less than '
                   f'{env.max_handle_length}'
        )

    if not re.search(env.handle_regex, handle):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'handle has to match {env.handle_regex}'
        )

    # password
    if not env.min_password_length < len(password) < env.max_password_length:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'password has to be more than {env.min_password_length} characters and less than '
                   f'{env.max_password_length}'
        )

    # does user exist already?
    if len(await database.User.objects.filter(handle=handle).all()) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'user with that handle already exists'
        )

    # create the user
    password = password_hasher.hash(f'{env.salt}{password}{env.pepper}')
    user_id = await database.User.objects.count() + 1

    user = await database.User.objects.create(
        id=user_id,
        name=name,
        handle=handle,
        timestamp=datetime.now(),
        password=password
    )

    return UserSchema(**user.__dict__)


@app.get('/users/@{handle}')
async def get_user_by_handle(
        handle: str = Path(..., title='Handle', description='Handle of target user')
):
    try:
        user = await database.User.objects.get(handle=handle)

        return UserSchema(**user.__dict__)
    except orm.NoMatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='user not found'
        )


@app.get('/users/@{handle}/tweets')
async def get_tweets_by_user(
        handle: str = Path(..., title='Handle', description='Handle of target user')
):
    try:
        author = await database.User.objects.get(handle=handle)
        tweets = await database.Tweet.objects.filter(author=author).all()

        schema_tweets = []

        for tweet in tweets:
            await tweet.author.load()
            tweet.__dict__['author'] = tweet.author.__dict__
            schema_tweets.append(TweetSchema(**tweet.__dict__))

        return schema_tweets
    except orm.NoMatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='user not found'
        )


# tweets
@app.post('/tweet')
async def create_tweet(
        text: str = Form(..., title='Tweet contents', description='The tweet text itself'),
        user_logged_in: User = Depends(get_user_logged_in)
):
    # preconditions
    if len(text) > env.tweet_max_length:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'tweet must be less than {env.tweet_max_length} characters'
        )

    tweet_id = await database.Tweet.objects.count() + 1

    tweet = await database.Tweet.objects.create(
        id=tweet_id,
        text=text,
        author=user_logged_in,
        timestamp=datetime.now()
    )

    await tweet.author.load()
    tweet.__dict__['author'] = tweet.author.__dict__

    return TweetSchema(**tweet.__dict__)


@app.get('/tweet/{id}')
async def get_tweet_by_id(
        id: int = Path(..., title='Tweet ID', description='ID of the Tweet')
):
    try:
        tweet = await database.Tweet.objects.get(id=id)

        await tweet.author.load()
        tweet.__dict__['author'] = tweet.author.__dict__

        return TweetSchema(**tweet.__dict__)
    except orm.NoMatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='tweet not found'
        )


@app.delete('/tweet/{id}')
async def delete_tweet_by_id(
        id: int = Path(..., title='Tweet ID', description='ID of the Tweet to delete'),
        currently_logged_in_as: User = Depends(get_user_logged_in)
):
    try:
        tweet = await database.Tweet.objects.get(id=id, author=currently_logged_in_as)

        await tweet.author.load()
        tweet.__dict__['author'] = tweet.author.__dict__
        return_dict = tweet.__dict__

        await tweet.delete()

        return TweetSchema(**return_dict)
    except orm.NoMatch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'tweet #{id} by @{currently_logged_in_as.handle} not found'
        )


@app.on_event('startup')
async def start():
    await database.database.connect()


@app.on_event('shutdown')
async def stop():
    await database.database.disconnect()
