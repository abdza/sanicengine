from functools import wraps
from sanic.response import json, redirect
from database import dbsession
from users.models import User
from pages.models import Page

def authorized(object_type=None):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            is_authorized = False
            curuser = None
            if 'user_id' in request['session']:
                curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
            if object_type=='page':
                if 'slug' in kwargs:
                    page = dbsession.query(Page).filter(Page.slug==kwargs['slug']).first()
                    if page:
                        if not page.require_login:
                            is_authorized = True
                        else:
                            if curuser:
                                mroles = curuser.moduleroles(page.module)
                                if any(r in ['admin','Admin'] for r in mroles):
                                    is_authorized = True
                                if page.allowed_roles and len(page.allowed_roles) and any(r in [ ar.strip() for ar in page.allowed_roles.split(',')] for r in mroles):
                                    is_authorized = True
            else:
                if curuser:
                    is_authorized = True
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
