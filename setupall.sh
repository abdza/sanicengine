#!/bin/bash
./dbscripts.py | sudo -u postgres psql
alembic init alembic
./setalembicini.py
