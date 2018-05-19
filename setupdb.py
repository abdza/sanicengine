#!/usr/bin/env python3 

try:
    import settings
except ImportError:
    print("Error importing settings. Please copy settings.sample.py to settings.py and modify the content for your use")
    exit()

print("create database " + settings.DATABASE_NAME)
print("create role " + settings.DATABASE_USERNAME + " with password " + settings.DATABASE_PASSWORD)
print("grant all on database " + settings.DATABASE_NAME + " to " + settings.DATABASE_USERNAME)
print("flush privileges")

