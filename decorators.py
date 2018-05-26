from functools import wraps
from sanic.response import json, redirect
from database import dbsession


def authorized(object_type=None, require_admin=False, require_superuser=False):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            is_authorized = False
            curuser = None
            if 'user_id' in request['session']:
                from users.models import User
                curuser = dbsession.query(User).filter(
                    User.id == request['session']['user_id']).first()

            if 'slug' in request.args:
                kwargs['slug'] = request.args['slug'][0]

            if object_type in ['page', 'filelink', 'tracker'] and ('slug' in kwargs or 'module' in kwargs):
                curobj = None
                if object_type == 'page':
                    from pages.models import Page
                    if not 'slug' in kwargs:
                        kwargs['slug'] = kwargs['module']
                        kwargs['module'] = 'portal'
                    curobj = dbsession.query(Page).filter(
                        Page.module == kwargs['module'], Page.slug == kwargs['slug']).first()
                elif object_type == 'filelink':
                    from fileLinks.models import FileLink
                    if not 'slug' in kwargs:
                        kwargs['slug'] = kwargs['module']
                        kwargs['module'] = 'portal'
                    curobj = dbsession.query(FileLink).filter(
                        FileLink.module == kwargs['module'], FileLink.slug == kwargs['slug']).first()
                elif object_type == 'tracker':
                    from trackers.models import Tracker
                    if not 'slug' in kwargs:
                        kwargs['slug'] = kwargs['module']
                        kwargs['module'] = 'portal'
                    curobj = dbsession.query(Tracker).filter(
                        Tracker.module == kwargs['module'], Tracker.slug == kwargs['slug']).first()
                if curobj:
                    mroles = []
                    if curuser:
                        mroles = curuser.moduleroles(curobj.module)
                        if any(r in ['admin', 'Admin'] for r in mroles):
                            is_authorized = True
                    if not is_authorized and curobj.is_published:
                        if not curobj.require_login:
                            is_authorized = True
                        else:
                            if not require_admin and curobj.allowed_roles and len(curobj.allowed_roles) and any(r in [ar.strip() for ar in curobj.allowed_roles.split(',')] for r in mroles):
                                is_authorized = True
            elif require_admin:
                if curuser:
                    mroles = curuser.moduleroles()
                    if any(r in ['admin', 'Admin'] for r in mroles):
                        is_authorized = True
                    else:
                        is_authorized = bool(curuser.superuser)
            else:
                if curuser:
                    is_authorized = True
            if curuser and require_superuser:
                is_authorized = bool(curuser.superuser)
            if curuser and not is_authorized and bool(curuser.superuser):
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
