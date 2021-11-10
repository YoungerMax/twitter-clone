# Self-host procedure

All following directions assume that you are in the root of this repository.

## Preparation

1. Make sure you have Python 3 installed
2. Edit `backend/twitterclone.ini`, change
   1. `uri` to your database URI
   2. `salt_change_me_immediately` and `pepper_change_me_immediately` to a bunch of random characters
3. (*optional, **highly** recommended for development environments*) Create a Python virtual environment
   1. Use `virtualenv venv`
   2. Then, enter it with
      1. (MacOS/Linux) `source venv/bin/activate`
      2. (Windows) `venv\bin\activate`
4. Install required Python libraries with `pip install -r backend/requirements.txt`

## Run it
1. Start your PostgreSQL server
2. Change your working directory to `backend/`
3. Run `python3 -m twitterclone`
4. Visit http://127.0.0.1:8000/docs