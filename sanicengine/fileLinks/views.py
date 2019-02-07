# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, file_stream
from .models import FileLink
from .forms import FileLinkForm
from sanicengine.users.models import User
from sanicengine.database import dbsession
from sanicengine.template import render
from sanicengine.decorators import authorized
from sqlalchemy_paginator import Paginator
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
import os
import time

bp = Blueprint('fileLinks')

@bp.route('/download/<module>/<slug>')
@bp.route('/download/<module>')
@authorized(object_type='filelink')
async def download(request, module, slug=None):
    if slug == None:
        if 'slug' in request.args:
            slug = request.args['slug']
        else:
            slug = module
            module = 'portal'
    filelink = dbsession.query(FileLink).filter_by(
        module=module, slug=slug).first()
    if filelink:
        return await file_stream(filelink.filepath, filename=filelink.filename)

@bp.route('/files/delete/<id>', methods=['POST'])
@authorized(require_admin=True)
async def delete(request, id):
    filelink = dbsession.query(FileLink).get(int(id))
    if filelink:
        if os.path.exists(filelink.filepath):
            os.remove(filelink.filepath)
        dbsession.delete(filelink)
        try:
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
    return redirect(request.app.url_for('fileLinks.index'))

@bp.route('/files/edit/<id>',methods=['POST','GET'])
@bp.route('/files/edit/',methods=['POST','GET'],name='edit')
@bp.route('/files/create',methods=['POST','GET'],name='create')
@authorized(object_type='filelink',require_admin=True)
async def form(request,id=None):
    title = 'Create File Link'
    form = FileLinkForm(request.form)
    filelink = None
    if id:
        filelink = dbsession.query(FileLink).get(int(id))
    if filelink:
        title = 'Edit File'
    if request.method=='POST':
        if form.validate():
            dst = None
            if not filelink:
                filelink=FileLink()
            if request.files.get('filename') and request.files.get('filename').name:
                dfile = request.files.get('filename')
                ext = dfile.type.split('/')[1]
                if not os.path.exists(os.path.join('uploads',request.form.get('module'))):
                    os.makedirs(os.path.join('uploads',request.form.get('module')))
                dst = os.path.join('uploads',request.form.get('module'),str(int(time.time())) + dfile.name)
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
                filelink.filename = dfile.name
                filelink.filepath = dst
            del(form['filename'])
            form.populate_obj(filelink)
            if dst:
                filelink.filepath = dst
            success = False
            dbsession.add(filelink)
            try:
                dbsession.commit()
                success=True
            except IntegrityError as inst:
                form.slug.errors.append('File with slug ' + form.slug.data + ' already exist in module ' + form.module.data + '. It needs to be unique')
                dbsession.rollback()
                if os.path.exists(dst):
                    os.remove(dst)
            except Exception as inst:
                dbsession.rollback()
                if os.path.exists(dst):
                    os.remove(dst)

            if success:
                return redirect('/files')
    else:
        if filelink:
            form = FileLinkForm(obj=filelink)
    curuser = User.getuser(request['session']['user_id'])
    modules = curuser.rolemodules('Admin')
    return html(render(request, 'generic/form.html', title=title, form=form, modules=modules, enctype='multipart/form-data'))


@bp.route('/files')
@authorized(object_type='filelink', require_admin=True)
async def index(request):
    curuser = User.getuser(request['session']['user_id'])
    filelinks = dbsession.query(FileLink)
    modules = []
    donefilter = False
    for m in dbsession.query(FileLink.module).distinct():
        if 'Admin' in curuser.moduleroles(m[0]):
            modules.append(m[0])
            if(request.args.get('module_filter') and request.args.get('module_filter')==m[0]):
                filelinks = filelinks.filter_by(module=m[0])
                donefilter = True
    if not donefilter:
        filelinks = filelinks.filter(FileLink.module.in_(modules))
    if request.args.get('q'):
        filelinks = filelinks.filter(or_(FileLink.title.ilike("%" + request.args.get('q') + "%"),FileLink.slug.ilike("%" + request.args.get('q') + "%"),FileLink.filename.ilike("%" + request.args.get('q') + "%")))
    paginator = Paginator(filelinks, 10)
    return html(render(request, 'generic/list.html', title='Files', deletelink='fileLinks.delete', editlink='fileLinks.edit', addlink='fileLinks.create',filter_fields=[{'field':'module','label':'Module','options':modules},], fields=[{'label': 'Module', 'name': 'module'}, {'label': 'Slug', 'name': 'slug'}, {'label': 'Title', 'name': 'title'}, {'label': 'File', 'name': 'filename'}], paginator=paginator, curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))
