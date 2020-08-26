# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Error
from sanicengine.pages.models import Page
from sanicengine.portalsettings.models import Setting
from sanicengine.trackers.models import Tracker,TrackerField,TrackerRole,TrackerStatus,TrackerTransition
from sanicengine.fileLinks.models import FileLink
from sanicengine.trees.models import Tree, TreeNode, TreeNodeUser
from sanicengine.database import dbsession
from sanicengine.decorators import authorized
from sqlalchemy_paginator import Paginator
from sanicengine.template import render, render_string
import os
import json
import shutil 

bp = Blueprint('errors')

@bp.route('/errors')
@authorized(require_superuser=True)
async def index(request):
    from sanicengine.template import render
    errors = dbsession.query(Error)
    paginator = Paginator(errors, 10)
    return html(render(request, 'generic/list.html',editlink='errors.index',title='Errors',fields=[{'label':'Title','name':'title'},{'label':'Date Created','name':'date_created'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/errors/<id>',methods=['GET'])
@authorized(require_superuser=True)
async def view(request,id=None):
    error = None
    if id:
        error = dbsession.query(Error).get(id)
    return html(render(request, 'generic/view.html',item=error,title='Errors',fields=[{'label':'Title','name':'title'},{'label':'Date Created','name':'date_created'},{'label':'Description','name':'description'}]),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
    
