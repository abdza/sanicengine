from jinja2 import Template, Environment, FileSystemLoader
from sanicengine.database import dbsession, executedb, querydb, queryobj
from sanicengine.users.models import User
import datetime

jinja_env = Environment(loader=FileSystemLoader(['custom_modules/custom_templates','sanicengine/templates']))

def render(request, template_file, *args, **kwargs):
    curuser = None
    if 'user_id' in request['session']:
        curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
    from sanicengine.users import models as users
    from sanicengine.fileLinks import models as fileLinks
    from sanicengine.trackers import models as trackers
    from sanicengine.trees import models as trees
    from sanicengine.pages import models as pages
    from sanicengine.portalsettings.models import Setting
    app = request.app
    app.users = users
    app.fileLinks = fileLinks
    app.trackers = trackers
    app.trees = trees
    app.dbsession = dbsession
    app.executedb = executedb
    app.querydb = querydb
    app.queryobj = queryobj
    app.pages = pages
    app.settings = Setting
    return jinja_env.get_template(template_file).render(app=app,request=request,curuser=curuser,datetime=datetime,*args,**kwargs)

def render_string(request, template_string, *args, **kwargs):
    curuser = None
    if 'user_id' in request['session']:
        curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
    from sanicengine.users import models as users
    from sanicengine.fileLinks import models as fileLinks
    from sanicengine.trackers import models as trackers
    from sanicengine.trees import models as trees
    from sanicengine.pages import models as pages
    from sanicengine.portalsettings.models import Setting
    app = request.app
    app.users = users
    app.fileLinks = fileLinks
    app.trackers = trackers
    app.trees = trees
    app.dbsession = dbsession
    app.executedb = executedb
    app.querydb = querydb
    app.queryobj = queryobj
    app.pages = pages
    app.settings = Setting
    return jinja_env.from_string(template_string).render(app=app,request=request,curuser=curuser,datetime=datetime,*args,**kwargs)

def bare_render_string(template_string, *args, **kwargs):
    return jinja_env.from_string(template_string).render(*args,**kwargs)
