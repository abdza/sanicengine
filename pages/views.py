# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Page
from .forms import PageForm
from database import dbsession
from template import render
from sqlalchemy_paginator import Paginator

bp = Blueprint('pages')

@bp.route('/view/<slug>')
def view(request, slug):
    page = dbsession.query(Page).filter_by(slug=slug).first()
    if page:
        return html(page.render())
    else:
        print("No page to view")
        return redirect('/')

@bp.route('/pages/create',methods=['POST','GET'])
@bp.route('/pages/edit/',methods=['POST','GET'],name='edit')
@bp.route('/pages/edit/<slug>',methods=['POST','GET'])
def form(request,slug=None):
    title = 'Create Page'
    form = PageForm(request.form)
    if request.method=='POST':
        page = dbsession.query(Page).filter_by(slug=form.slug.data).first()
        if not page:
            page = dbsession.query(Page).get(int(slug))
        if page:
            title = 'Edit Page'
        if form.validate():
            if not page:
                page=Page()
            form.populate_obj(page)
            dbsession.add(page)
            dbsession.commit()
            return redirect('/pages')
    else:
        if slug is not None:
            page = dbsession.query(Page).filter_by(slug=slug).first()
            if not page:
                page = dbsession.query(Page).get(int(slug))
            if page:
                form = PageForm(obj=page)
                title = 'Edit Page'

    return html(render(request,'generic/form.html',title=title,form=form,enctype='multipart/form-data'))

@bp.route('/pages')
def index(request):
    pages = dbsession.query(Page)
    paginator = Paginator(pages, 5)
    return html(render(request, 'generic/list.html',title='Pages',editlink=request.app.url_for('pages.edit'),addlink=request.app.url_for('pages.form'),fields=[{'label':'Title','name':'title'},{'label':'Slug','name':'slug'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))
