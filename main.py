#!/usr/bin/env python3
from sanic import Sanic
from sanic.response import json, html, redirect
from sanic_session import InMemorySessionInterface
import users, pages, fileLinks, trackers, modules
from template import render
from database import dbsession, ModelBase, dbengine
import asyncio
import aiosmtplib
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from email.mime.text import MIMEText
from email.message import EmailMessage
from email.utils import make_msgid
import settings

app = Sanic()
app.static('/static','./static')
app.config.from_object(settings)

session_interface = InMemorySessionInterface()


@app.middleware('request')
async def add_session_to_request(request):
    # before each request initialize a session
    # using the client's request
    await session_interface.open(request)

@app.middleware('request')
async def access_permission(request):
    print("got to access permission")
    print("session:" + str(request['session']))

@app.middleware('response')
async def save_session(request, response):
    # after each request save the session,
    # pass the response to set client cookies
    await session_interface.save(request, response)

@app.listener('before_server_start')
async def setup_db(app, loop):
    ModelBase.metadata.create_all(dbengine)

@app.listener('before_server_start')
async def register_bp(app, loop):
    app.blueprint(users.views.bp)
    app.blueprint(pages.views.bp)
    app.blueprint(fileLinks.views.bp)
    app.blueprint(trackers.views.bp)
    app.blueprint(modules.views.bp)

async def send_email(data):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_send_email,args=[data])
    scheduler.start()  #run one-off job, so the client not need to wait

async def _send_email(data):

    #Thanks: https://github.com/cole/aiosmtplib/issues/1
    host = os.environ.get('MAIL_SERVER_HOST') if os.environ.get('MAIL_SERVER_HOST') else settings.MAIL_HOST 
    port = os.environ.get('MAIL_SERVER_PORT') if os.environ.get('MAIL_SERVER_PORT') else settings.MAIL_PORT
    user = os.environ.get('MAIL_SERVER_USER') if os.environ.get('MAIL_SERVER_USER') else settings.MAIL_USERNAME
    password = os.environ.get('MAIL_SERVER_PASSWORD') if os.environ.get('MAIL_SERVER_PASSWORD') else settings.MAIL_PASSWORD


    loop = asyncio.get_event_loop()

    server = aiosmtplib.SMTP(host, port, loop=loop, use_tls=False)
    await server.connect()

    await server.starttls()
    await server.login(user, password)

    async def send_a_message():
        message = EmailMessage()
        message['From'] = os.environ.get('MAIL_SERVER_USER') if os.environ.get('MAIL_SERVER_USER') else settings.MAIL_USERNAME
        message['To'] = ','.join(data['email_to'])
        message['Subject'] = data['subject']
        if 'body' in data:
            message.set_content(data['body'])
        if 'htmlbody' in data:
            asparagus_cid = make_msgid()
            message.add_alternative(data['htmlbody'].format(asparagus_cid=asparagus_cid[1:-1]), subtype='html')
        await server.send_message(message)

    await send_a_message()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
