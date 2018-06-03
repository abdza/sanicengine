#!/usr/bin/env python3 
import configparser

try:
    import settings
    config = configparser.ConfigParser()
    config.read('alembic.ini')
    config['alembic']['sqlalchemy.url'] = 'postgresql://' + settings.DATABASE_USERNAME + ':' + settings.DATABASE_PASSWORD + '@localhost/' + settings.DATABASE_NAME
    with open('alembic.ini','w') as configfile:
        config.write(configfile)

except ImportError:
    print("Error importing settings. Please copy settings.sample.py to settings.py and modify the content for your use")
    exit()
