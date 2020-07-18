# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json as jsonresponse
from .models import EmailTemplate, EmailTrail
from .forms import EmailTemplateForm
from sanicengine.users.models import User
from sanicengine.database import dbsession, executedb, querydb
from sanicengine.template import render
from sanicengine.decorators import authorized
from sqlalchemy_paginator import Paginator
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
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
        emailtemplate.renderemail(request,scheduled_date = datetime.date(2018,2,3),data={'name':'kassim','age':34})
    return redirect(request.app.url_for('emailtemplates.index'))

@bp.route('/emailtemplates/sendemails')
async def sendemails(request):
    emails = dbsession.query(EmailTrail).filter(EmailTrail.status=='New',EmailTrail.scheduled_date < datetime.datetime.today()).all()
    if len(emails):
        from main import send_email
        for email in emails:
            await send_email({'email_to':[email.sendto],'email_cc':[email.sendcc],'subject':email.title,'htmlbody':email.content})
            email.status='Sent'
            dbsession.add(email)
            dbsession.commit()
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

    curuser = User.getuser(request.ctx.session['user_id'])
    modules = curuser.rolemodules('Admin')
    return html(render(request,'generic/form.html',title=title,emailtemplate=emailtemplate,modules=modules,
            form=form,enctype='multipart/form-data',submitcontinue=submitcontinue),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})

@bp.route('/emailtemplates')
@authorized(object_type='emailtemplate',require_admin=True)
async def index(request):
    emailtemplates = dbsession.query(EmailTemplate)
    curuser = User.getuser(request.ctx.session['user_id'])
    modules = []
    donefilter = False
    for m in dbsession.query(EmailTemplate.module).distinct():
        if 'Admin' in curuser.moduleroles(m[0]):
            modules.append(m[0])
            if(request.args.get('module_filter') and request.args.get('module_filter')==m[0]):
                emailtemplates = emailtemplates.filter_by(module=m[0])
                donefilter = True
    if not donefilter:
        emailtemplates = emailtemplates.filter(EmailTemplate.module.in_(modules))
    if request.args.get('q'):
        emailtemplates = emailtemplates.filter(or_(EmailTemplate.title.ilike("%" + request.args.get('q') + "%")))
    paginator = Paginator(emailtemplates, 10)
    return html(render(request,
        'generic/list.html',title='Email Templates',deletelink='emailtemplates.delete',editlink='emailtemplates.edit',actions=[{'label':'Render','actionlink':'emailtemplates.renderemail'},],addlink='emailtemplates.create',filter_fields=[{'field':'module','label':'Module','options':modules},],fields=[{'label':'Module','name':'module'},{'label':'Title','name':'title'}],paginator=paginator,pagelink=[{'link':'emailtemplates.sendemails','title':'Send Emails'}],curpage=paginator.page(int(request.args['emailtemplate'][0]) if 'emailtemplate' in request.args else 1)),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
