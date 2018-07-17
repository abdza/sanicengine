# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Setting
from .forms import SettingForm
from database import dbsession
from template import render
from decorators import authorized
from sqlalchemy_paginator import Paginator
from sqlalchemy.exc import IntegrityError

bp = Blueprint('settings')

@bp.route('/settings/delete/<id>',methods=['POST'])
@authorized(object_type='setting',require_admin=True)
async def delete(request,id):
    setting = dbsession.query(Setting).get(int(id))
    if setting:
        dbsession.delete(setting)
        try:
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
    return redirect(request.app.url_for('settings.index'))

@bp.route('/settings/edit/<id>',methods=['POST','GET'])
@bp.route('/settings/edit/',methods=['POST','GET'],name='edit')
@bp.route('/settings/create',methods=['POST','GET'],name='create')
@authorized(object_type='setting')
async def form(request,id=None):
    title = 'Create Setting'
    form = None
    submitcontinue = False
    setting=None
    if id:
        setting = dbsession.query(Setting).get(id)
    if request.method=='POST':
        form = SettingForm(request.form)
        if form.validate():
            if not setting:
                setting=Setting()
            form.populate_obj(setting)
            dbsession.add(setting)
            success = False
            try:
                dbsession.commit()
                success = True
            except IntegrityError as inst:
                form.name.errors.append('Setting with name ' + form.name.data + ' already exist in module ' + form.module.data + '. It needs to be unique')
                dbsession.rollback()
            except Exception as inst:
                dbsession.rollback()
            if success:
                return redirect('/settings')
    else:
        if setting:
            form = SettingForm(obj=setting)
            title = 'Edit Setting'
            submitcontinue = True
    if not form:
        form = SettingForm()

    return html(render(request,'generic/form.html',title=title,setting=setting,
            form=form,enctype='multipart/form-data',submitcontinue=submitcontinue))

@bp.route('/settings')
@authorized(object_type='setting',require_admin=True)
async def index(request):
    settings = dbsession.query(Setting)
    paginator = Paginator(settings, 50)
    return html(render(request,
        'generic/list.html',title='Settings',deletelink='settings.delete',editlink='settings.edit',addlink='settings.create',fields=[{'label':'Module','name':'module'},{'label':'Name','name':'name'},{'label':'Type','name':'setting_type'},{'label':'Value','name':'value'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))
