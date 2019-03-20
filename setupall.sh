#!/bin/bash
./dbscripts.py | sudo -u postgres psql
mkdir custom_modules
sudo chown -R www-data custom_modules
mkdir uploads
sudo chown -R www-data uploads
