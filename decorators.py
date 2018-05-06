from functools import wraps
from sanic.response import json, redirect
from database import dbsession

def authorized(object_type=None,require_superuser=False):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            is_authorized = False
            curuser = None
            if 'user_id' in request['session']:
                from users.models import User
                curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
            if object_type in ['page','filelink','tracker']:
                if 'slug' in kwargs:
                    curobj = None
                    if object_type=='page':
                        from pages.models import Page
                        curobj = dbsession.query(Page).filter(Page.slug==kwargs['slug']).first()
                    elif object_type=='filelink':
                        from fileLinks.models import FileLink
                        curobj = dbsession.query(FileLink).filter(FileLink.slug==kwargs['slug']).first()
                    elif object_type=='tracker':
                        from trackers.models import Tracker
                        curobj = dbsession.query(Tracker).filter(Tracker.slug==kwargs['slug']).first()
                    if curobj:
                        if not curobj.require_login:
                            is_authorized = True
                        else:
                            if curuser:
                                mroles = curuser.moduleroles(curobj.module)
                                if any(r in ['admin','Admin'] for r in mroles):
                                    is_authorized = True
                                if curobj.allowed_roles and len(curobj.allowed_roles) and any(r in [ ar.strip() for ar in curobj.allowed_roles.split(',')] for r in mroles):
                                    is_authorized = True
            else:
                if curuser:
                    is_authorized = True
            if curuser and require_superuser:
                is_authorized = bool(curuser.superuser)
            if is_authorized:
                # the user is authorized.
                # run the handler method and return the response
                response = await f(request, *args, **kwargs)
                return response
            else:
                # the user is not authorized. 
                request['session']['flashmessage'] = 'You are not authorized to view that page'
                return redirect(request.app.url_for('pages.home'))
        return decorated_function
    return decorator
