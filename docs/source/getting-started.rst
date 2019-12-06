.. _getting-started:

********************************
Getting Started With SanicEngine
********************************

Getting The Code
================

Git the code
------------

Clone the git repo into your folder of choice then cd into it:

   git clone https://github.com/abdza/sanicengine foodmenu
   cd foodmenu

Set up virtual environment
--------------------------

Run python command to create a virtual environment then activate it:

   python3 -m venv venv
   source venv/bin/activate

Pip install wheel
-----------------

Sometimes you need to update the pip and then install the wheel package

   pip install --upgrade pip
   pip install wheel

Pip install everything
----------------------

Run pip install to install all the required modules

   pip install -r requirements

That should be all the you need to get all the codes required

Setting Up Settings
===================

Next you'll need to setup the settings for your little sanicengine project

Copy settings.py
----------------

To begin your development, first you need to modify the settings. Copy the sample settings file to be used for your project:

   cp sanicengine/settings.sample.py sanicengine/settings.py

Modify the file
---------------

Then edit the sanicengine/settings.py file for your use. At least the database settings (database name, username and password). If you already have settings for a mail server it would also be good to update it now

Run setupall.sh
---------------

To create the database and user, grant the user privileges, initialize alembic and setup the alembic .ini, you can use the script provided with the following command:

   ./setupall.sh

It will ask for your root password to run the command, so that it can sudo as the postgres user

Running It
==========

Run main.py
-----------

Finally just run the following command:

   ./main.py

It should say something like:
    [2018-05-19 10:43:43 +0800] [13411] [INFO] Goin' Fast @ http://0.0.0.0:8000
    [2018-05-19 10:43:43 +0800] [13411] [INFO] Starting worker [13411]

So now you should be able to open your web browser of choice and go to the address http://localhost:8080 and see your system live

The default superuser username is admin with password admin123
