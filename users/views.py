# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json
from template import render
from .forms import UserForm, ModuleRoleForm
from .models import User, ModuleRole
from database import dbsession
from sqlalchemy_paginator import Paginator
from sqlalchemy import or_
import hashlib

bp = Blueprint('users')

@bp.route('/login',methods=['GET','POST'])
async def login(request):
    curuser = dbsession.query(User).filter(User.username==request.form.get('username')).first()
    if curuser:
        if curuser.password == hashlib.sha224(request.form.get('password').encode('utf-8')).hexdigest():
            request['session']['user_id']=curuser.id
            return redirect('/')
    return html(render(request,'login.html'))

@bp.route('/logout')
async def logout(request):
    if 'user_id' in request['session']:
        del(request['session']['user_id'])
    return redirect('/')

@bp.route('/module_roles/create',methods=['POST','GET'])
@bp.route('/module_roles/edit/',methods=['POST','GET'],name='module_role_edit')
@bp.route('/module_roles/edit/<module_role_id>',methods=['POST','GET'])
async def module_role_form(request,module_role_id=None):
    title = 'Create ModuleRole'
    form = ModuleRoleForm(request.form)
    module_role = None
    userdata = None
    if request.method=='POST':
        if module_role_id:
            module_role = dbsession.query(ModuleRole).get(int(module_role_id))
        if module_role:
            title = 'Edit ModuleRole'
        if form.validate():
            if not module_role:
                module_role=ModuleRole()
            if form.user.data:
                curuser = dbsession.query(User).get(form.user.data)
                form.user.data = curuser
            form.populate_obj(module_role)
            dbsession.add(module_role)
            dbsession.commit()
            return redirect('/module_roles')
    else:
        if module_role_id is not None:
            module_role = dbsession.query(ModuleRole).get(int(module_role_id))
            if module_role:
                form = ModuleRoleForm(obj=module_role)
                form.user.data = module_role.user.id
                title = 'Edit ModuleRole'
                userdata = {'id':module_role.user.id,'name':module_role.user.name}

    return html(render(request,'generic/form.html',title=title,form=form,userdata=userdata,enctype='multipart/form-data'))

@bp.route('/module_roles')
async def module_roles(request):
    module_roles = dbsession.query(ModuleRole)
    paginator = Paginator(module_roles, 5)
    return html(render(request, 'generic/list.html',title='Module Roles',editlink=request.app.url_for('users.module_role_edit'),addlink=request.app.url_for('users.module_role_form'),fields=[{'label':'User','name':'user'},{'label':'Module','name':'module'},{'label':'Role','name':'role'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))

@bp.route('/users/json/')
async def userjson(request):
    searchval = ''
    if 'q' in request.args:
        searchval = request.args['q'][0]
    users = dbsession.query(User).filter(or_(User.name.ilike("%" + searchval + "%"),User.username.ilike("%" + searchval + "%"))).all()
    return json([ {'id':user.id,'name':user.name} for user in users ])

@bp.route('/users')
async def index(request):
    users = dbsession.query(User)
    paginator = Paginator(users, 5)
    return html(render(request, 'generic/list.html',title='Users',fields=[{'label':'Name','name':'name'},],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))

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
