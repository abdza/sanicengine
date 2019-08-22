#!/usr/bin/env python3
from sanic import Sanic
from sanic.response import html, redirect
from sanic.exceptions import NotFound,ServerError
from sanic_session import InMemorySessionInterface
from sanicengine import users, pages, fileLinks, trackers, modules, trees, portalsettings, emailtemplates, customtemplates, portalerrors
from sanicengine import settings
from sanicengine.template import render
from sanicengine.database import dbsession, ModelBase, dbengine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from email.mime.text import MIMEText
from email.message import EmailMessage
from email.utils import make_msgid
import asyncio, aiosmtplib, os, json, sys, getopt, getpass
import hashlib, base64, datetime
import sys,traceback

from sqlalchemy import MetaData

app = Sanic()
app.static('/static','./sanicengine/static')
app.config.from_object(settings)

session_interface = InMemorySessionInterface()

@app.exception(NotFound)
async def pagenotfound(request,exception):
    notpage = dbsession.query(pages.models.Page).filter_by(module='portal',slug='error_404').first()
    if notpage:
        return html(notpage.render(request,title=notpage.title),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
    else:
        return html(render(request,'errors/404.html',title='Page not found'))

@app.exception(ServerError)
async def servererror(request,exception):
    print("Error is")
    print(str(dir(exception)))
    print("Tb")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
    notpage = dbsession.query(pages.models.Page).filter_by(module='portal',slug='error_500').first()
    if notpage:
        return html(notpage.render(request,title=notpage.title),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
    else:
        return html(render(request,'errors/500.html',title='Server Error'))

@app.middleware('request')
async def add_session_to_request(request):
    # before each request initialize a session
    # using the client's request
    await session_interface.open(request)

@app.middleware('request')
async def user_from_request(request):
    if 'authorization' in request.headers:
        if request.headers['authorization'][0:6]=='Basic ':
            authtoken = []
            try:
                authtoken = base64.standard_b64decode(request.headers['authorization'][6:]).decode('utf-8').split(':')
            except Exception as inst:
                print("Exception authenticating: " + str(inst))
            if len(authtoken)==2:
                curuser = dbsession.query(users.models.User).filter_by(username=authtoken[0]).first()
                if curuser:
                    if curuser.password == curuser.hashpassword(authtoken[1]):
                        request['session']['user_id']=curuser.id
                        authhash = curuser.email + str(datetime.datetime.now())
                        curuser.authhash = hashlib.sha224(authhash.encode('utf-8')).hexdigest()
                        curuser.authexpire = datetime.datetime.now() + datetime.timedelta(minutes=5)
                        dbsession.add(curuser)
                        dbsession.commit()
        else:
            curuser=dbsession.query(users.models.User).filter_by(authhash=request.headers['authorization']).first()
            if curuser and datetime.datetime.today() < curuser.authexpire:
                request['session']['user_id']=curuser.id
                curuser.authexpire = datetime.datetime.now() + datetime.timedelta(minutes=5)
                dbsession.add(curuser)
                dbsession.commit()

@app.middleware('response')
async def save_session(request, response):
    # after each request save the session,
    # pass the response to set client cookies
    await session_interface.save(request, response)

@app.listener('before_server_start')
async def setup_db(app, loop):
    metadata = MetaData()
    metadata.reflect(bind=dbengine)
    ModelBase.metadata.create_all(dbengine)
    for t in ModelBase.metadata.sorted_tables:
        if not str(t) in metadata.tables.keys():
            print("Not found table " + str(t))
        else:
            for c in t.c:
                if not c.name in metadata.tables[str(t)].c:
                    print("Not found column:" + str(c) + " in db")
                    coltype = str(c.type)
                    if coltype=='DATETIME':
                        coltype='TIMESTAMP'
                    addsql = "alter table " + str(t) + " add column " + c.name + " " + coltype
                    dbsession.execute(addsql)
                    dbsession.commit()

@app.listener('before_server_start')
async def register_bp(app, loop):
    app.blueprint(users.views.bp)
    app.blueprint(pages.views.bp)
    app.blueprint(fileLinks.views.bp)
    app.blueprint(trackers.views.bp)
    app.blueprint(modules.views.bp)
    app.blueprint(trees.views.bp)
    app.blueprint(portalsettings.views.bp)
    app.blueprint(portalerrors.views.bp)
    app.blueprint(emailtemplates.views.bp)
    app.blueprint(customtemplates.views.bp)

@app.listener('before_server_start')
async def default_data(app, loop):
    site_tree = dbsession.query(trees.models.Tree).filter_by(slug='site',module='portal').first()
    if not site_tree:
        data={'type_selection':['page','file','tracker']}
        site_tree = trees.models.Tree(title='Site Tree',slug='site',module='portal',published=True,require_login=False,datastr=json.dumps(data))
        dbsession.add(site_tree)
        site_tree.create_rootnode()

    super_user = dbsession.query(users.models.User).filter_by(superuser=True).first()
    if not super_user:
        super_user = dbsession.query(users.models.User).filter_by(username='admin').first()
        if super_user:
            super_user.superuser=True
        else:
            super_user = users.models.User(name='Admin Dude',username='admin',email='admin@sanicengine.com',superuser=True)
            super_user.password = hashlib.sha224('admin123'.encode('utf-8')).hexdigest()

        adminmodulerole = users.models.ModuleRole(user=super_user,role='Admin',module='portal')
        dbsession.add(super_user)
        dbsession.add(adminmodulerole)

    dbsession.commit()

async def returnfunction(request,arg1=None,arg2=None,arg3=None,arg4=None,arg5=None):
    custom_routes = portalsettings.models.Setting.namedefault('portal','customurl',[])
    croute = custom_routes[request.uri_template]
    if croute['type']=='page':
        return await pages.views.view(request,module=croute['module'],slug=croute['slug'],arg1=arg1,arg2=arg2,arg3=arg3,arg4=arg4,arg5=arg5)
    elif croute['type']=='file':
        return await fileLinks.views.download(request,module=croute['module'],slug=croute['slug'])
    elif croute['type']=='tracker':
        if 'method' in croute and croute['method']=='addrecord':
            return await trackers.views.addrecord(request,module=croute['module'],slug=croute['slug'])
        else:
            return await trackers.views.viewlist(request,module=croute['module'],slug=croute['slug'])

@app.listener('before_server_start')
async def custom_routes(app, loop):
    custom_routes = portalsettings.models.Setting.namedefault('portal','customurl',[])
    if custom_routes:
        for cr in custom_routes:
            if not cr=='/':
                app.add_route(returnfunction,cr,methods=['GET','POST'])

@app.listener('before_server_start')
async def custom_static(app, loop):
    custom_static = portalsettings.models.Setting.namedefault('portal','customstatic',[])
    if custom_static:
        print(str(custom_static))
        for cr in custom_static:
            print(str(cr))
            if os.path.exists(custom_static[cr]['path']):
                app.static(cr,custom_static[cr]['path'])

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
    startserver = True
    try:
        host = settings.LISTEN_ON
    except:
        host = "0.0.0.0"
    try:
        port = settings.PORT
    except:
        port = 8000
    try:
        workers = settings.WORKERS
    except:
        workers = 1
    if len(sys.argv)>1:
        try:
            opts, args = getopt.getopt(sys.argv[1:],"h:p:w:",["host=","port=","workers=","setpassword="])
        except getopt.GetoptError:
            print('main.py -h <host> -p <port> -w <workers> --setpassword <user email>')
            sys.exit(2)
        for opt, arg in opts:
            if opt in ('-h','--host'):
                host = arg
            elif opt in ('-p','--port'):
                port = arg
            elif opt in ('-w','--workers'):
                workers = arg
            elif opt in ('-w','--workers'):
                workers = arg
            elif opt == "--setpassword":
                startserver = False
                curuser = dbsession.query(users.models.User).filter_by(email=arg).first()
                if curuser:
                    cpass = getpass.getpass('Please key in the new password for ' + curuser.name + ':')
                    curuser.password = hashlib.sha224(cpass.encode('utf-8')).hexdigest()
                    dbsession.add(curuser)
                    dbsession.commit()
                    print('Updated the user password')
                else:
                    print('User with email:' + arg + ' was not found')

    if startserver:
        app.run(host=host, port=port, workers=workers)
