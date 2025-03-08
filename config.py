# config.py
import os

from pytz import timezone


class Config:
    DEBUG = True
    # TESTING = True
    SECRET_KEY = 'fifa 2022'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///strava.sqlite3'
    PARIS = timezone('Europe/Paris')
    BASE_PATH = os.path.dirname(__file__)
    MAPBOX_API_KEY = 'pk.eyJ1IjoicG1vdXJleSIsImEiOiJjbHZ4dnJ3bGMwNDBzMmlxeXBnZDJtYzVrIn0.yxrohiV1L6c89UY6PvPHGw'


class DevelopmentConfig(Config):
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = True
    ENV = 'development'

