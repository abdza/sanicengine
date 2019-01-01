#!/bin/bash
./dbscripts.py | sudo -u postgres psql
mkdir custom_module
sudo chown -R www-data custom_module
mkdir uploads
sudo chown -R www-data uploads
