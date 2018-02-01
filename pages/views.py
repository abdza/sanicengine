# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Page
from .forms import PageForm
from database import dbsession
from template import render

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
@bp.route('/pages/edit/<slug>',methods=['POST','GET'])
def form(request,slug=None):
    title = 'Create Page'
    form = PageForm(request.form)
    if request.method=='POST' and form.validate():
        page = dbsession.query(Page).filter_by(slug=form.slug.data).first()
        if not page:
            page=Page()
        form.populate_obj(page)
        dbsession.add(page)
        dbsession.commit()
    else:
        if slug is not None:
            page = dbsession.query(Page).filter_by(slug=slug).first()
            if page:
                form = PageForm(obj=page)
                title = 'Edit Page'
    return html(render('generic/form.html',title=title,form=form))
