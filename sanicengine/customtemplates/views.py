# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json as jsonresponse
from sanicengine.database import dbsession, executedb, querydb
from sanicengine.template import render
from sanicengine.decorators import authorized
from sqlalchemy_paginator import Paginator
from sqlalchemy.exc import IntegrityError
import datetime

bp = Blueprint('customtemplates')

@bp.route('/customtemplates/delete/<id>',methods=['POST'])
@authorized(object_type='customtemplate',require_admin=True)
async def delete(request,id):
    customtemplate = dbsession.query(CustomTemplate).get(int(id))
    if customtemplate:
        dbsession.delete(customtemplate)
        try:
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
    return redirect(request.app.url_for('customtemplates.index'))

@bp.route('/customtemplates/edit/<id>',methods=['POST','GET'])
@bp.route('/customtemplates/edit/',methods=['POST','GET'],name='edit')
@bp.route('/customtemplates/create',methods=['POST','GET'],name='create')
@authorized(object_type='customtemplate')
async def form(request,id=None):
    title = 'Create CustomTemplate'
    form = CustomTemplateForm(request.form)
    submitcontinue = False
    customtemplate=None
    if id:
        customtemplate = dbsession.query(CustomTemplate).get(id)
    if request.method=='POST' and form.validate():
        if not customtemplate:
            customtemplate=CustomTemplate()
        form.populate_obj(customtemplate)
        dbsession.add(customtemplate)
        success = False
        try:
            dbsession.commit()
            success = True
        except IntegrityError as inst:
            form.title.errors.append('CustomTemplate with title ' + form.title.data + ' already exist in module ' + form.module.data + '. It needs to be unique')
            dbsession.rollback()
        except Exception as inst:
            dbsession.rollback()
        if success:
            if request.form['submit'][0]=='Submit':
                return redirect('/customtemplates')
            else:
                return redirect('/customtemplates/edit/' + str(customtemplate.id))
    else:
        if customtemplate:
            form = CustomTemplateForm(obj=customtemplate)
            title = customtemplate.title + '-Edit'
            submitcontinue = True

    return html(render(request,'generic/form.html',title=title,customtemplate=customtemplate,
            form=form,enctype='multipart/form-data',submitcontinue=submitcontinue))

@bp.route('/customtemplates')
@authorized(object_type='customtemplate',require_admin=True)
async def index(request):
    return html(render(request,
        'customtemplates/index.html'))
