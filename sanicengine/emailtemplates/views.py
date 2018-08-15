# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json as jsonresponse
from .models import EmailTemplate
from .forms import EmailTemplateForm
from sanicengine.database import dbsession, executedb, querydb
from sanicengine.template import render
from sanicengine.decorators import authorized
from sqlalchemy_paginator import Paginator
from sqlalchemy.exc import IntegrityError
import datetime

bp = Blueprint('emailtemplates')

@bp.route('/emailtemplates/<module>/json')
async def jsonlist(request,module):
    emailtemplates = dbsession.query(EmailTemplate).filter(EmailTemplate.module==module,EmailTemplate.title.ilike('%' + request.args['q'][0] + '%')).all()
    return jsonresponse([ {'id':etemp.id,'name':etemp.title} for etemp in emailtemplates ])

@bp.route('/emailtemplates/render/<id>',methods=['POST'])
@authorized(object_type='emailtemplate')
async def renderemail(request,id):
    emailtemplate = dbsession.query(EmailTemplate).get(int(id))
    if emailtemplate:
        print("rq:" + str(request['session']))
        emailtemplate.renderemail(request,scheduled_date = datetime.date(2018,2,3),data={'name':'kassim','age':34})
    return redirect(request.app.url_for('emailtemplates.index'))

@bp.route('/emailtemplates/delete/<id>',methods=['POST'])
@authorized(object_type='emailtemplate',require_admin=True)
async def delete(request,id):
    emailtemplate = dbsession.query(EmailTemplate).get(int(id))
    if emailtemplate:
        dbsession.delete(emailtemplate)
        try:
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
    return redirect(request.app.url_for('emailtemplates.index'))

@bp.route('/emailtemplates/edit/<id>',methods=['POST','GET'])
@bp.route('/emailtemplates/edit/',methods=['POST','GET'],name='edit')
@bp.route('/emailtemplates/create',methods=['POST','GET'],name='create')
@authorized(object_type='emailtemplate')
async def form(request,id=None):
    title = 'Create EmailTemplate'
    form = EmailTemplateForm(request.form)
    submitcontinue = False
    emailtemplate=None
    if id:
        emailtemplate = dbsession.query(EmailTemplate).get(id)
    if request.method=='POST' and form.validate():
        if not emailtemplate:
            emailtemplate=EmailTemplate()
        form.populate_obj(emailtemplate)
        dbsession.add(emailtemplate)
        success = False
        try:
            dbsession.commit()
            success = True
        except IntegrityError as inst:
            form.title.errors.append('EmailTemplate with title ' + form.title.data + ' already exist in module ' + form.module.data + '. It needs to be unique')
            dbsession.rollback()
        except Exception as inst:
            dbsession.rollback()
        if success:
            if request.form['submit'][0]=='Submit':
                return redirect('/emailtemplates')
            else:
                return redirect('/emailtemplates/edit/' + str(emailtemplate.id))
    else:
        if emailtemplate:
            form = EmailTemplateForm(obj=emailtemplate)
            title = emailtemplate.title + '-Edit'
            submitcontinue = True

    return html(render(request,'generic/form.html',title=title,emailtemplate=emailtemplate,
            form=form,enctype='multipart/form-data',submitcontinue=submitcontinue))

@bp.route('/emailtemplates')
@authorized(object_type='emailtemplate',require_admin=True)
async def index(request):
    emailtemplates = dbsession.query(EmailTemplate)
    paginator = Paginator(emailtemplates, 50)
    return html(render(request,
        'generic/list.html',title='Email Templates',deletelink='emailtemplates.delete',editlink='emailtemplates.edit',actions=[{'label':'Render','actionlink':'emailtemplates.renderemail'},],addlink='emailtemplates.create',fields=[{'label':'Module','name':'module'},{'label':'Title','name':'title'}],paginator=paginator,curpage=paginator.page(int(request.args['emailtemplate'][0]) if 'emailtemplate' in request.args else 1)))
