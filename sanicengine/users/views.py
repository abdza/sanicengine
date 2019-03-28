# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json as jsonresponse
from sanicengine.template import render
from .forms import UserForm, ModuleRoleForm, ProfileForm
from .models import User, ModuleRole
from sanicengine.pages.models import Page
from sanicengine.database import dbsession
from sanicengine.decorators import authorized
from sqlalchemy_paginator import Paginator
from sqlalchemy import or_
from main import send_email
import hashlib
import json
import datetime

from google.oauth2 import id_token
from google.auth.transport import requests as googlerequest

bp = Blueprint('users')

@bp.route('/googlesignin',methods=['GET','POST'])
async def googlesignin(request):
    print("Output gsignin")
    print(str(request))
    if 'idtoken' in request.form:
        print("Token:" + str(request.form['idtoken']))
        try:
            idinfo = id_token.verify_oauth2_token(request.form['idtoken'][0],googlerequest.Request(), request.app.config.GOOGLE_OAUTH_ID)
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            userid = idinfo['sub']

            print("idinfo:" + str(userid))
            print("email:" + str(idinfo['email']))
            print("name:" + str(idinfo['name']))
            print("picture:" + str(idinfo['picture']))
            print("given_name:" + str(idinfo['given_name']))
            print("family_name:" + str(idinfo['family_name']))

            curuser = dbsession.query(User).filter(User.email==idinfo['email']).first()
            if curuser:
                print("Logging in " + str(curuser))
            else:
                print("Need to register user")
                curuser = User(name=idinfo['name'],email=idinfo['email'],avatar=idinfo['picture'])
                dbsession.add(curuser)
                dbsession.commit()
                print("Registered " + str(curuser))
            if curuser:
                request['session']['user_id']=curuser.id
        except Exception as err:
            print("error:" + str(err))
    return jsonresponse({'output':'done'})

@bp.route('/login',methods=['GET','POST'])
async def login(request):
    if 'authorization' in request.headers:
        if 'user_id' in request['session']:
            curuser = dbsession.query(User).get(request['session']['user_id'])
            return jsonresponse({'authtoken':curuser.authhash})
        else:
            return jsonresponse({'message':'Login required'},status=401)

    if request.method=='POST':
        curuser = dbsession.query(User).filter(User.username==request.form.get('username')).first()
        if not curuser:
            curuser = dbsession.query(User).filter(User.email==request.form.get('username')).first()
        if curuser:
            if curuser.password == curuser.hashpassword(request.form.get('password')):
                request['session']['user_id']=curuser.id
                if 'targeturl' in request.form:
                    return redirect(request.form['targeturl'][0])
                else:
                    return redirect('/')
            else:
                request['session']['flashmessage']='Wrong username or password'
        else:
            request['session']['flashmessage']='Wrong username or password'
        if 'currentpage' in request.form:
            return redirect(request.form['currentpage'][0])
        else:
            return redirect('/')
        return redirect('/')

    return html(render(request,'users/login.html'),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/logout')
async def logout(request):
    if 'user_id' in request['session']:
        del(request['session']['user_id'])
    return redirect('/')

@bp.route('/module_roles/delete/<id>',methods=['POST'])
@authorized(require_superuser=True)
async def module_role_delete(request,id):
    module_role = dbsession.query(ModuleRole).get(int(id))
    if module_role:
        dbsession.delete(module_role)
        try:
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
    return redirect(request.app.url_for('users.module_roles'))


@bp.route('/module_roles/edit/<module_role_id>',methods=['POST','GET'])
@bp.route('/module_roles/edit/',methods=['POST','GET'],name='module_role_edit')
@bp.route('/module_roles/create',methods=['POST','GET'],name='module_role_create')
@authorized(require_admin=True)
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

    curuser = User.getuser(request['session']['user_id'])
    modules = []
    for m in dbsession.query(ModuleRole.module).distinct():
        if 'Admin' in curuser.moduleroles(m[0]):
            modules.append(m[0])

    return html(render(request,'generic/form.html',title=title,form=form,userdata=userdata,modules=modules,enctype='multipart/form-data'),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/module_roles')
@authorized(require_admin=True)
async def module_roles(request):
    curuser = User.getuser(request['session']['user_id'])
    module_roles = dbsession.query(ModuleRole)
    modules = []
    donefilter = False
    for m in dbsession.query(ModuleRole.module).distinct():
        if 'Admin' in curuser.moduleroles(m[0]):
            modules.append(m[0])
            if(request.args.get('module_filter') and request.args.get('module_filter')==m[0]):
                module_roles = module_roles.filter_by(module=m[0])
                donefilter = True
    if not donefilter:
        module_roles = module_roles.filter(ModuleRole.module.in_(modules))
    if request.args.get('q'):
        module_roles = module_roles.filter(or_(ModuleRole.role.ilike("%" + request.args.get('q') + "%")))
    paginator = Paginator(module_roles, 10)
    return html(render(request, 'generic/list.html',title='Module Roles',deletelink='users.module_role_delete',editlink='users.module_role_edit',addlink='users.module_role_create',filter_fields=[{'field':'module','label':'Module','options':modules},],fields=[{'label':'User','name':'user'},{'label':'Module','name':'module'},{'label':'Role','name':'role'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/users/json/')
async def userjson(request):
    searchval = ''
    if 'q' in request.args:
        searchval = request.args['q'][0]
    users = dbsession.query(User).filter(or_(User.name.ilike("%" + searchval + "%"),User.username.ilike("%" + searchval + "%"))).all()
    return jsonresponse([ {'id':user.id,'name':user.name} for user in users ])

@bp.route('/users/delete/<id>',methods=['POST'])
@authorized(object_type='setting',require_admin=True)
async def delete(request,id):
    user = dbsession.query(User).get(int(id))
    if user:
        dbsession.delete(user)
        try:
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
    return redirect(request.app.url_for('users.index'))

@bp.route('/users/edit/<id>',methods=['POST','GET'])
@bp.route('/users/edit/',methods=['POST','GET'],name='edit')
@bp.route('/users/create',methods=['POST','GET'],name='create')
@authorized(object_type='user')
async def form(request,id=None):
    title = 'Create User'
    form = None
    submitcontinue = False
    user=None
    if id:
        user = dbsession.query(User).get(id)
    if request.method=='POST':
        form = UserForm(request.form)
        if form.validate():
            if not user:
                user=User()
            form.populate_obj(user)
            if request.form.get('password'):
                user.password = hashlib.sha224(request.form.get('password').encode('utf-8')).hexdigest()
            dbsession.add(user)
            success = False
            try:
                dbsession.commit()
                success = True
            except IntegrityError as inst:
                form.name.errors.append('User with name ' + form.name.data + ' already exist in module ' + form.module.data + '. It needs to be unique')
                dbsession.rollback()
            except Exception as inst:
                dbsession.rollback()
            if success:
                return redirect(request.app.url_for('users.index'))
    else:
        if user:
            form = UserForm(obj=user)
            title = 'Edit User'
            submitcontinue = True
    if not form:
        form = UserForm()

    return html(render(request,'generic/form.html',title=title,user=user,
            form=form,enctype='multipart/form-data',submitcontinue=submitcontinue),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/users')
@authorized(require_admin=True)
async def index(request):
    users = dbsession.query(User)
    paginator = Paginator(users, 10)
    return html(render(request, 'generic/list.html',title='Users',deletelink='users.delete',editlink='users.edit',addlink='users.create',fields=[{'label':'Name','name':'name'},],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/profile',methods=['GET','POST'])
@authorized()
async def profile(request):
    curuser = dbsession.query(User).get(request['session']['user_id'])
    form = ProfileForm(request.form)
    if request.method=='POST' and form.validate():
        curuser.name = form.name.data
        curuser.email = form.email.data
        dbsession.add(curuser)
        dbsession.commit()
        request['session']['flashmessage']='Updated profile'
        return redirect('/')
    else:
        form.name.data = curuser.name
        form.email.data = curuser.email
    return html(render(request,'users/profile.html',form=form),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/user/register',methods=['GET','POST'])
async def register(request):
    form = UserForm(request.form)
    if request.method=='POST' and form.validate():
        user=User()
        form.populate_obj(user)
        user.password = user.hashpassword(request.form.get('password'))
        user.username = user.email
        dbsession.add(user)
        dbsession.commit()
        return redirect('/')
    return html(render(request,'users/register.html',form=form),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/changepassword',methods=['GET','POST'])
async def changepassword(request):
    user = dbsession.query(User).get(request['session']['user_id'])
    if request.method=='POST':
        if request.form.get('password')==request.form.get('passwordrepeat'):
            user.password = hashlib.sha224(request.form.get('password').encode('utf-8')).hexdigest()
            dbsession.add(user)
            dbsession.commit()
            return redirect(request.app.url_for('pages.home'))
        else:
            request['session']['flashmessage']='Repeated password need to be the same password'
            return redirect(request.app.url_for('users.changepassword'))
    return html(render(request,'users/changepassword.html',user=user),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/resetpassword/<resethash>',methods=['GET','POST'])
async def resetpassword(request,resethash=None):
    user=dbsession.query(User).filter_by(resethash=resethash).first()
    if request.method=='POST':
        if request.form.get('password')==request.form.get('passwordrepeat'):
            if datetime.datetime.today() < user.resetexpire:
                user.password = hashlib.sha224(request.form.get('password').encode('utf-8')).hexdigest()
                dbsession.add(user)
                dbsession.commit()
                return redirect(request.app.url_for('users.login'))
            else:
                request['session']['flashmessage']='Sorry but the link has already expired. Please resubmit request to rest password'
                return redirect(request.app.url_for('users.forgotpassword'))
        else:
            request['session']['flashmessage']='Repeated password need to be the same password'
            return redirect(request.app.url_for('users.resetpassword',resethash=resethash))

    return html(render(request,'users/resetpassword.html',user=user),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/forgot-password',methods=['GET','POST'])
async def forgotpassword(request):
    if request.method=='POST':
        user=dbsession.query(User).filter_by(email=request.form.get('email')).first()
        if user:
            resethash = user.email + str(datetime.datetime.now())
            user.resethash = hashlib.sha224(resethash.encode('utf-8')).hexdigest()
            user.resetexpire = datetime.datetime.now() + datetime.timedelta(hours=1)
            dbsession.add(user)
            dbsession.commit()
            resetemail = dbsession.query(Page).filter_by(slug='resetemail').first()
            if resetemail:
                request['session']['flashmessage']='Password reset email sent to ' + user.email
                await send_email({'email_to':[user.email],'subject':resetemail.title,'htmlbody':resetemail.render(request,user=user)})
            else:
                request['session']['flashmessage']='Password reset email sent to ' + user.email
                await send_email({'email_to':[user.email],'subject':'Reset password link','htmlbody':render(request,'users/reset_email.html',user=user)})
        else:
            request['session']['flashmessage']='User with email ' + request.form.get('email') + ' was not found'
    return html(render(request,'users/forgot-password.html'),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
