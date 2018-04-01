# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, file_stream
from .models import FileLink
from .forms import FileLinkForm
from database import dbsession
from template import render
from sqlalchemy_paginator import Paginator
import os

bp = Blueprint('fileLinks')

@bp.route('/files/download/<slug>')
async def download(request,slug):
    filelink = dbsession.query(FileLink).filter_by(slug=slug).first()
    if filelink:
        return await file_stream(filelink.filename)

@bp.route('/files/create',methods=['POST','GET'])
@bp.route('/files/edit/',methods=['POST','GET'],name='edit')
@bp.route('/files/edit/<slug>',methods=['POST','GET'])
async def form(request,slug=None):
    title = 'Create File Link'
    form = FileLinkForm(request.form)
    if request.method=='POST':
        filelink = dbsession.query(FileLink).filter_by(slug=form.slug.data).first()
        if not filelink:
            filelink = dbsession.query(FileLink).get(int(form.slug.data))
        if filelink:
            title = 'Edit File'
        if form.validate():
            dst = None
            if not filelink:
                filelink=FileLink()
            if request.files.get('filename'):
                dfile = request.files.get('filename')
                ext = dfile.type.split('/')[1]
                dst = os.path.join('upload',dfile.name)

                try:
                    # extract starting byte from Content-Range header string
                    range_str = request.headers['Content-Range']
                    start_bytes = int(range_str.split(' ')[1].split('-')[0])
                    with open(dst, 'ab') as f:
                        f.seek(start_bytes)
                        f.write(dfile.body)
                except KeyError:
                    with open(dst, 'wb') as f:
                        f.write(dfile.body)
                filelink.filename = dst
            form.populate_obj(filelink)
            if dst:
                filelink.filename = dst
            dbsession.add(filelink)
            dbsession.commit()
            return redirect('/files')
    else:
        if slug is not None:
            filelink = dbsession.query(FileLink).filter_by(slug=slug).first()
            if not filelink:
                filelink = dbsession.query(FileLink).get(int(slug))
            if filelink:
                form = FileLinkForm(obj=filelink)
                title = 'Edit File'
    return html(render(request,'generic/form.html',title=title,form=form,enctype='multipart/form-data'))

@bp.route('/files')
async def index(request):
    filelinks = dbsession.query(FileLink)
    paginator = Paginator(filelinks, 5)
    return html(render(request, 'generic/list.html',title='Files',editlink=request.app.url_for('fileLinks.edit'),addlink=request.app.url_for('fileLinks.form'),fields=[{'label':'Title','name':'title'},{'label':'Slug','name':'slug'},{'label':'Module','name':'module'},{'label':'File','name':'filename'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))
