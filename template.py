from jinja2 import Template, Environment, FileSystemLoader
from database import dbsession, executedb, querydb
from users.models import User

jinja_env = Environment(loader=FileSystemLoader('templates'))

def render(request, template_file, *args, **kwargs):
    curuser = None
    if 'user_id' in request['session']:
        curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
    from users import models as users
    from fileLinks import models as fileLinks
    from trackers import models as trackers
    from trees import models as trees
    from pages import models as pages
    from portalsettings.models import Setting
    app = request.app
    app.users = users
    app.fileLinks = fileLinks
    app.trackers = trackers
    app.trees = trees
    app.dbsession = dbsession
    app.executedb = executedb
    app.querydb = querydb
    app.pages = pages
    app.settings = Setting
    return jinja_env.get_template(template_file).render(app=app,request=request,curuser=curuser,*args,**kwargs)

def render_string(request, template_string, *args, **kwargs):
    curuser = None
    if 'user_id' in request['session']:
        curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
    from users import models as users
    from fileLinks import models as fileLinks
    from trackers import models as trackers
    from trees import models as trees
    from pages import models as pages
    from portalsettings.models import Setting
    app = request.app
    app.users = users
    app.fileLinks = fileLinks
    app.trackers = trackers
    app.trees = trees
    app.dbsession = dbsession
    app.executedb = executedb
    app.querydb = querydb
    app.pages = pages
    app.settings = Setting
    return jinja_env.from_string(template_string).render(app=app,request=request,curuser=curuser,*args,**kwargs)

def bare_render_string(template_string, *args, **kwargs):
    return jinja_env.from_string(template_string).render(*args,**kwargs)
