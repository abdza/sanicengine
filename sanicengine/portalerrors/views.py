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
from sanicengine.template import render
from sqlalchemy_paginator import Paginator
import os
import json
import shutil 

bp = Blueprint('errors')

@bp.route('/errors')
@authorized(require_superuser=True)
async def index(request):
    errors = dbsession.query(Error)
    paginator = Paginator(errors, 10)
    return html(render(request, 'generic/list.html',title='Errors',fields=[{'label':'Title','name':'title'},{'label':'Date Created','name':'date_created'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
