from jinja2 import Template, Environment, FileSystemLoader
from sanicengine.database import dbsession, executedb, querydb, queryobj
import datetime

jinja_env = Environment(loader=FileSystemLoader(['custom_modules/custom_templates','sanicengine/templates']))

def render(request, template_file, *args, **kwargs):
    from sanicengine.users.models import User
    from sanicengine.users import models as users
    from sanicengine.fileLinks import models as fileLinks
    from sanicengine.trackers import models as trackers
    from sanicengine.trees import models as trees
    from sanicengine.pages import models as pages
    from sanicengine.portalsettings.models import Setting
    curuser = None
    if request.ctx.session.get('user_id'):
        curuser = dbsession.query(User).filter(User.id==request.ctx.session.get('user_id')).first()
    app = request.app
    app.users = users
    app.fileLinks = fileLinks
    app.trackers = trackers
    app.Tracker = trackers.Tracker
    app.trees = trees
    app.Tree = trees.Tree
    app.dbsession = dbsession
    app.executedb = executedb
    app.querydb = querydb
    app.queryobj = queryobj
    app.pages = pages
    app.settings = Setting
    try:
        return jinja_env.get_template(template_file).render(app=app,request=request,curuser=curuser,datetime=datetime,*args,**kwargs)
    except Exception as exp:
        from sanicengine.portalerrors.models import Error
        Error.capture("Error rendering page at " + request.url,str(exp))
        return None


def render_string(request, template_string, *args, **kwargs):
    from sanicengine.users.models import User
    from sanicengine.users import models as users
    from sanicengine.fileLinks import models as fileLinks
    from sanicengine.trackers import models as trackers
    from sanicengine.trees import models as trees
    from sanicengine.pages import models as pages
    from sanicengine.portalsettings.models import Setting
    curuser = None
    if request.ctx.session.get('user_id'):
        curuser = dbsession.query(User).filter(User.id==request.ctx.session.get('user_id')).first()
    app = request.app
    app.users = users
    app.fileLinks = fileLinks
    app.trackers = trackers
    app.Tracker = trackers.Tracker
    app.trees = trees
    app.Tree = trees.Tree
    app.dbsession = dbsession
    app.executedb = executedb
    app.querydb = querydb
    app.queryobj = queryobj
    app.pages = pages
    app.settings = Setting
    try:
        return jinja_env.from_string(template_string).render(app=app,request=request,curuser=curuser,datetime=datetime,*args,**kwargs)
    except Exception as exp:
        from sanicengine.portalerrors.models import Error
        Error.capture("Error rendering string at " + request.url,str(exp))
        return None

def bare_render_string(template_string, *args, **kwargs):
    try:
        return jinja_env.from_string(template_string).render(*args,**kwargs)
    except Exception as exp:
        from sanicengine.portalerrors.models import Error
        Error.capture("Error rendering bare string",str(exp))
        return None
