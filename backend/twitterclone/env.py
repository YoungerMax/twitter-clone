import os
from configparser import ConfigParser
from pathlib import Path

cfg = ConfigParser()
cfg.read(os.path.join(str(Path(os.path.abspath(__file__)).parent.parent), 'twitterclone.ini'))

# values
db_uri = cfg.get('database', 'uri')

# name
name_regex = cfg.get('user', 'name_regex')
min_name_length = cfg.getint('user', 'min_name_length')
max_name_length = cfg.getint('user', 'max_name_length')

# handle
handle_regex = cfg.get('user', 'handle_regex')
min_handle_length = cfg.getint('user', 'min_handle_length')
max_handle_length = cfg.getint('user', 'max_handle_length')

# password
min_password_length = cfg.getint('user', 'min_password_length')
max_password_length = cfg.getint('user', 'max_password_length')

salt = cfg.get('security', 'salt_change_me_immediately'),
pepper = cfg.get('security', 'pepper_change_me_immediately')

time_cost = cfg.getint('security', 'time_cost')
memory_cost = cfg.getint('security', 'memory_cost')
parallelism = cfg.getint('security', 'parallelism')

tweet_max_length = cfg.getint('tweets', 'max_length')
