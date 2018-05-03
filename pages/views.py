# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Page
from .forms import PageForm
from database import dbsession
from template import render
from sqlalchemy_paginator import Paginator

bp = Blueprint('pages')

@bp.route('/terms')
async def terms(request):
    return html(render(request,'terms.html'))

@bp.route('/run/<slug>',methods=['GET','POST'])
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
async def view(request, slug):
    page = dbsession.query(Page).filter_by(slug=slug).first()
    if page:
        return html(page.render(request))
    else:
        print("No page to view")
        return redirect('/')

@bp.route('/pages/create',methods=['POST','GET'])
@bp.route('/pages/edit/',methods=['POST','GET'],name='edit')
@bp.route('/pages/edit/<slug>',methods=['POST','GET'])
async def form(request,slug=None):
    title = 'Create Page'
    form = PageForm(request.form)
    page=None
    if request.method=='POST':
        page = dbsession.query(Page).filter_by(slug=form.slug.data).first()
        if not page and slug:
            page = dbsession.query(Page).get(int(slug))
        if page:
            title = 'Edit Page'
        if form.validate():
            if not page:
                page=Page()
            form.populate_obj(page)
            dbsession.add(page)
            dbsession.commit()
            if request.form['submit'][0]=='Submit':
                return redirect('/pages')
            else:
                return redirect('/pages/edit/' + page.slug)
    else:
        if slug is not None:
            page = dbsession.query(Page).filter_by(slug=slug).first()
            if not page:
                page = dbsession.query(Page).get(int(slug))
            if page:
                form = PageForm(obj=page)
                title = 'Edit Page'

    return html(render(request,'pages/form.html',title=title,page=page,
            form=form,enctype='multipart/form-data',submitcontinue=True))

@bp.route('/')
async def home(request):
    home = dbsession.query(Page).filter_by(slug='home').first()
    if home:
        return html(home.render(request))
    return html(render(request,'pages/home.html'))


@bp.route('/pages')
async def index(request):
    pages = dbsession.query(Page)
    paginator = Paginator(pages, 5)
    return html(render(request,
        'generic/list.html',title='Pages',editlink=request.app.url_for('pages.edit'),addlink=request.app.url_for('pages.form'),fields=[{'label':'Title','name':'title'},{'label':'Slug','name':'slug'},{'label':'Runable','name':'runable'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))
