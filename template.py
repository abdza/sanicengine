from jinja2 import Template, Environment, FileSystemLoader
from database import dbsession
from users.models import User

jinja_env = Environment(loader=FileSystemLoader('templates'))

def render(request, template_file, *args, **kwargs):
    curuser = None
    if 'user_id' in request['session']:
        curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
    return jinja_env.get_template(template_file).render(app=request.app,request=request,curuser=curuser,*args,**kwargs)

def render_string(request, template_string, *args, **kwargs):
    curuser = None
    if 'user_id' in request['session']:
        curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
    return jinja_env.from_string(template_string).render(app=request.app,request=request,curuser=curuser,*args,**kwargs)
