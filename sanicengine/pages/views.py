# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json as jsonresponse
from .models import Page
from .forms import PageForm
from sanicengine.trackers.models import Tracker
from sanicengine.trees.models import Tree
from sanicengine.emailtemplates.models import EmailTemplate, EmailTrail
from sanicengine.portalsettings.models import Setting
from sanicengine.database import dbsession, executedb, querydb, queryobj
from sanicengine.template import render
from sanicengine.decorators import authorized
from sanicengine.users.models import User
from sqlalchemy_paginator import Paginator
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
import sys
import traceback
import datetime

bp = Blueprint('pages')
#modulepath = Setting.namedefault('portal','modulepath','custom_modules')
modulepath = 'custom_modules'

@bp.route('/terms')
async def terms(request):
    return html(render(request,'terms.html'),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/run/<module>/<slug>/<arg1>/<arg2>/<arg3>/<arg4>/<arg5>',methods=['GET','POST'],name='run5args')
@bp.route('/run/<module>/<slug>/<arg1>/<arg2>/<arg3>/<arg4>',methods=['GET','POST'],name='run4args')
@bp.route('/run/<module>/<slug>/<arg1>/<arg2>/<arg3>',methods=['GET','POST'],name='run3args')
@bp.route('/run/<module>/<slug>/<arg1>/<arg2>',methods=['GET','POST'],name='run2args')
@bp.route('/run/<module>/<slug>/<arg1>',methods=['GET','POST'],name='run1args')
@bp.route('/run/<module>/<slug>',methods=['GET','POST'])
@bp.route('/run/<module>',methods=['GET','POST'],name='runportal')
@authorized(object_type='page')
async def run(request, module, slug=None, arg1=None, arg2=None, arg3=None, arg4=None, arg5=None):
    if slug==None:
        slug = module
        module = 'portal'
    page = dbsession.query(Page).filter_by(module=module,slug=slug).first()
    if page and page.runable:

        def formvalue(field,default=None):
            if field in request.form:
                return request.form[field][0]
            elif default is not None:
                return default
            else:
                ''

        def argvalue(field,default=None):
            if field in request.args:
                return request.args[field][0]
            elif default is not None:
                return default
            else:
                ''

        redirecturl=None
        results=None
        ldict = locals()
        try:
            exec(page.content,globals(),ldict)
        except Exception as e:
            print("Got error running commands from page:" + str(page))
            print("Page content:" + str(page.content))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type,exc_value,exc_traceback)
            from sanicengine.portalerrors.models import Error
            Error.capture("Error running page at " + request.url,str(page.content).replace("<","&lt;").replace(">","&gt;").replace("\n","<br>") + "<br><br>Error<br>==========<br>" + traceback.format_exc().replace("<","&lt;").replace(">","&gt;").replace("\n","<br>"))
        if 'redirecturl' in ldict:
            redirecturl=ldict['redirecturl']
        if 'results' in ldict:
            results=ldict['results']
        if redirecturl:
            return redirect(redirecturl)
        elif results:
            return results
        else:
            return redirect('/')
    else:
        print("No page to view")
        return redirect('/')

@bp.route('/view/<module>/<slug>/<arg1>/<arg2>/<arg3>/<arg4>/<arg5>',methods=['GET','POST'],name='page5args')
@bp.route('/view/<module>/<slug>/<arg1>/<arg2>/<arg3>/<arg4>',methods=['GET','POST'],name='page4args')
@bp.route('/view/<module>/<slug>/<arg1>/<arg2>/<arg3>',methods=['GET','POST'],name='page3args')
@bp.route('/view/<module>/<slug>/<arg1>/<arg2>',methods=['GET','POST'],name='page2args')
@bp.route('/view/<module>/<slug>/<arg1>',methods=['GET','POST'],name='page1args')
@bp.route('/view/<module>/<slug>',methods=['GET','POST'])
@bp.route('/view/<module>',methods=['GET','POST'],name='portalpage')
@authorized(object_type='page')
async def view(request, module, slug=None, arg1=None, arg2=None, arg3=None, arg4=None, arg5=None):
    if slug==None:
        slug = module
        module = 'portal'
    page = dbsession.query(Page).filter_by(module=module,slug=slug).first()
    if page:
        headers = {'X-Frame-Options':'deny'}
        if not page.script:
            headers['X-Content-Type-Options'] = 'nosniff'
        return html(page.render(request,title=page.title,arg1=arg1,arg2=arg2,arg3=arg3,arg4=arg4,arg5=arg5),headers=headers)
    else:
        request.ctx.session['flashmessage'] = 'Sorry but page was not found'
        return redirect('/')

@bp.route('/pages/delete/<id>',methods=['POST'])
@authorized(object_type='page',require_admin=True)
async def delete(request,id):
    page = dbsession.query(Page).get(int(id))
    if page:
        dbsession.delete(page)
        try:
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
    return redirect(request.app.url_for('pages.index'))

@bp.route('/pages/edit/<id>',methods=['POST','GET'])
@bp.route('/pages/edit/',methods=['POST','GET'],name='edit')
@bp.route('/pages/create',methods=['POST','GET'],name='create')
@authorized(object_type='page')
async def form(request,id=None):
    title = 'Create Page'
    form = PageForm(request.form)
    submitcontinue = False
    page=None
    if id:
        page = dbsession.query(Page).get(id)
    if request.method=='POST' and form.validate():
        if not page:
            page=Page()
        form.populate_obj(page)
        dbsession.add(page)
        success = False
        try:
            dbsession.commit()
            success = True
        except IntegrityError as inst:
            form.slug.errors.append('Page with slug ' + form.slug.data + ' already exist in module ' + form.module.data + '. It needs to be unique')
            dbsession.rollback()
        except Exception as inst:
            dbsession.rollback()
        if success:
            if request.form['submit'][0]=='Submit':
                return redirect('/pages')
            else:
                return redirect('/pages/edit/' + str(page.id))
    else:
        if page:
            form = PageForm(obj=page)
            title = page.title + '-Edit'
            submitcontinue = True

    curuser = User.getuser(request.ctx.session['user_id'])
    modules = curuser.rolemodules('Admin')
    return html(render(request,'pages/form.html',title=title,page=page,modules=modules,
            form=form,enctype='multipart/form-data',submitcontinue=submitcontinue),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/')
async def home(request):
    home = dbsession.query(Page).filter_by(module='portal',slug='home').first()
    if home:
        return html(home.render(request),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
    return html(render(request,'pages/home.html'),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/admin')
async def admin(request):
    home = dbsession.query(Page).filter_by(module='portal',slug='admin').first()
    if home:
        return html(home.render(request),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
    return html(render(request,'pages/admin.html'),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/loginrequired')
async def loginrequired(request):
    if 'authorization' in request.headers:
        return jsonresponse({'message':'Login required'},status=401)
    loginrequired = dbsession.query(Page).filter_by(module='portal',slug='loginrequired').first()
    if loginrequired:
        return html(loginrequired.render(request),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
    return html(render(request,'pages/loginrequired.html',targeturl=request.ctx.session.pop('targeturl',None)),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/pages')
@authorized(object_type='page',require_admin=True)
async def index(request):
    curuser = User.getuser(request.ctx.session['user_id'])
    pages = dbsession.query(Page)
    modules = []
    donefilter = False
    runables = ['True','False']
    for m in dbsession.query(Page.module).distinct():
        if 'Admin' in curuser.moduleroles(m[0]):
            modules.append(m[0])
            if(request.args.get('module_filter') and request.args.get('module_filter')==m[0]):
                pages = pages.filter_by(module=m[0])
                donefilter = True
    if request.args.get('runable_filter'):
        if request.args.get('runable_filter')=='True':
            pages = pages.filter(Page.runable == True)
        elif request.args.get('runable_filter')=='False':
            pages = pages.filter(Page.runable == False)
    if not donefilter:
        pages = pages.filter(Page.module.in_(modules))
    if request.args.get('q'):
        pages = pages.filter(or_(Page.title.ilike("%" + request.args.get('q') + "%"),Page.slug.ilike("%" + request.args.get('q') + "%")))
    paginator = Paginator(pages, 10)
    return html(render(request,
        'generic/list.html',title='Pages',linktitle=True,deletelink='pages.delete',editlink='pages.edit',addlink='pages.create',filter_fields=[{'field':'module','label':'Module','options':modules},{'field':'runable','label':'Runable','options':runables}],fields=[{'label':'Module','name':'module'},{'label':'Slug','name':'slug'},{'label':'Title','name':'title'},{'label':'Runable','name':'runable'},{'label':'Login','name':'require_login'},{'label':'Published','name':'is_published'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
