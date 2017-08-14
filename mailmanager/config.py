import os

class Config(object) :
    DEBUG = False
    TESTING = False
    DATABASE = 'mailmanager/db/mailmanager.db'
    SECRET_KEY = 'development-key'

class DebugConfig(Config) :
    DEBUG = True

class TestConfig(Config) :
    TESTING = True
