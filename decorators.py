from functools import wraps
from sanic.response import json, redirect
from database import dbsession
from users.models import User

def authorized():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            is_authorized = False
            if 'user_id' in request['session']:
                curuser = dbsession.query(User).filter(User.id==request['session']['user_id']).first()
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
