# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html
from template import render

bp = Blueprint('user_bp')

@bp.route('/login')
async def login(request):
    return html(render('login.html'))

@bp.route('/register')
async def register(request):
    return html(render('register.html'))
