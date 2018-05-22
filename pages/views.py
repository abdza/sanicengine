# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Page
from .forms import PageForm
from database import dbsession
from template import render
from decorators import authorized
from sqlalchemy_paginator import Paginator
from sqlalchemy.exc import IntegrityError

bp = Blueprint('pages')

@bp.route('/terms')
async def terms(request):
    return html(render(request,'terms.html'))

@bp.route('/run/<slug>',methods=['GET','POST'])
@authorized(object_type='page')
async def run(request, slug):
    page = dbsession.query(Page).filter_by(slug=slug).first()
    if page and page.runable:
        redirecturl=None
        results=None
        ldict = locals()
        exec(page.content,globals(),ldict)
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

@bp.route('/view/<slug>',methods=['GET','POST'])
@authorized(object_type='page')
async def view(request, slug):
    page = dbsession.query(Page).filter_by(slug=slug).first()
    if page:
        return html(page.render(request))
    else:
        print("No page to view")
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

@bp.route('/pages/create',methods=['POST','GET'])
@bp.route('/pages/edit/',methods=['POST','GET'],name='edit')
@bp.route('/pages/edit/<id>',methods=['POST','GET'])
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
            title = 'Edit Page'
            submitcontinue = True

    return html(render(request,'pages/form.html',title=title,page=page,
            form=form,enctype='multipart/form-data',submitcontinue=submitcontinue))

@bp.route('/')
async def home(request):
    home = dbsession.query(Page).filter_by(slug='home').first()
    if home:
        return html(home.render(request))
    return html(render(request,'pages/home.html'))


@bp.route('/pages')
@authorized(object_type='page',require_admin=True)
async def index(request):
    pages = dbsession.query(Page)
    paginator = Paginator(pages, 5)
    return html(render(request,
        'generic/list.html',title='Pages',deletelink='pages.delete',editlink='pages.edit',addlink='pages.form',fields=[{'label':'Module','name':'module'},{'label':'Slug','name':'slug'},{'label':'Title','name':'title'},{'label':'Runable','name':'runable'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))
