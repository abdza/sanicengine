# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from template import render
from .forms import UserForm
from .models import User
from database import dbsession
import hashlib

bp = Blueprint('users')

@bp.route('/login',methods=['GET','POST'])
async def login(request):
    curuser = dbsession.query(User).filter(User.username==request.form.get('username')).first()
    if curuser:
        print('curpassword:' + curuser.password)
        print('oripassword:' + hashlib.sha224(request.form.get('password').encode('utf-8')).hexdigest())
        if curuser.password == hashlib.sha224(request.form.get('password').encode('utf-8')).hexdigest():
            request['session']['user_id']=curuser.id
            return redirect('/')
    return html(render(request,'login.html'))

@bp.route('/logout')
async def logout(request):
    if 'user_id' in request['session']:
        del(request['session']['user_id'])
    return redirect('/')

@bp.route('/register',methods=['GET','POST'])
async def register(request):
    form = UserForm(request.form)
    if request.method=='POST' and form.validate():
        user=User()
        form.populate_obj(user)
        user.password = hashlib.sha224(request.form.get('password').encode('utf-8')).hexdigest()
        dbsession.add(user)
        dbsession.commit()
        return redirect('/')
    return html(render(request,'register.html',form=form))
