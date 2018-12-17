#!/bin/bash
./dbscripts.py | sudo -u postgres psql
mkdir custom_module
chown -R www-data custom_module
mkdir uploads
chown -R www-data uploads
