# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Module
from pages.models import Page
from trackers.models import Tracker,TrackerField,TrackerRole,TrackerStatus,TrackerTransition
from fileLinks.models import FileLink
from .forms import ModuleForm
from database import dbsession
from template import render
from sqlalchemy_paginator import Paginator
import os
import json

bp = Blueprint('modules')
modulepath = 'custom_module'

@bp.route('/modules/import/<slug>')
async def importmodule(request,slug=None):
    if(os.path.exists(os.path.join(modulepath,slug))):
        curfile = open(os.path.join(modulepath,slug,'pagelist.json'),'r')
        pagesarray = json.loads(curfile.read())
        curfile.close()
        for cpage in pagesarray:
            page = dbsession.query(Page).filter_by(module=slug,slug=cpage['slug']).first()
            if page:
                page.title = cpage['title']
                page.published = cpage['published']
                page.require_login = cpage['require_login']
                page.publish_date = cpage['publish_date']
                page.expire_date = cpage['expire_date']
            else:
                page = Page(title=cpage['title'],module=cpage['module'],slug=cpage['slug'],published=cpage['published'],require_login=cpage['require_login'],publish_date=cpage['publish_date'],expire_date=cpage['expire_date'])
            try:
                cfile = open(os.path.join(modulepath,slug,'pages',cpage['slug']),'r')
                page.content = cfile.read()
                cfile.close()
            except c:
                print("Error importing page content for " + cpage['slug'])
            dbsession.add(page)

        curfile = open(os.path.join(modulepath,slug,'trackerlist.json'),'r')
        trackersarray = json.loads(curfile.read())
        curfile.close()
        for ctracker in trackersarray:
            tracker = dbsession.query(Tracker).filter_by(module=slug,slug=ctracker['slug']).first()
            if tracker:
                tracker.title = ctracker['title']
                tracker.list_fields = ctracker['list_fields']
            else:
                tracker = Tracker(title=ctracker['title'],module=ctracker['module'],slug=ctracker['slug'],list_fields=ctracker['list_fields'])
            dbsession.add(tracker)

            for cfield in ctracker['fields']:
                field = dbsession.query(TrackerField).filter_by(tracker=tracker,name=cfield['name']).first()
                if field:
                    field.label = cfield['label']
                    field.field_type = cfield['field_type']
                    field.obj_table = cfield['obj_table']
                    field.obj_field = cfield['obj_field']
                    field.default = cfield['default']
                else:
                    field = TrackerField(tracker=tracker,name=cfield['name'],label=cfield['label'],field_type=cfield['field_type'],obj_table=cfield['obj_table'],obj_field=cfield['obj_table'],default=cfield['default'])
                dbsession.add(field)

            for crole in ctracker['roles']:
                role = dbsession.query(TrackerRole).filter_by(tracker=tracker,name=crole['name']).first()
                if role:
                    role.role_type = crole['role_type']
                    role.compare = crole['compare']
                else:
                    role = TrackerRole(tracker=tracker,name=crole['name'],role_type=crole['role_type'],compare=crole['compare'])
                dbsession.add(role)

            for cstatus in ctracker['statuses']:
                status = dbsession.query(TrackerStatus).filter_by(tracker=tracker,name=cstatus['name']).first()
                if status:
                    status.display_fields = cstatus['display_fields']
                else:
                    status = TrackerStatus(tracker=tracker,name=cstatus['name'],display_fields=cstatus['display_fields'])
                dbsession.add(status)

            for ctransition in ctracker['transitions']:
                transition = dbsession.query(TrackerTransition).filter_by(tracker=tracker,name=ctransition['name']).first()
                if transition:
                    transition.display_fields = ctransition['display_fields']
                    transition.edit_fields = ctransition['edit_fields']
                    transition.postpage = ctransition['postpage']
                else:
                    transition = TrackerTransition(tracker=tracker,name=ctransition['name'],postpage=ctransition['postpage'],display_fields=ctransition['display_fields'],edit_fields=ctransition['edit_fields'])

                if ctransition['prev_status']:
                    transition.prev_status = dbsession.query(TrackerStatus).filter_by(name=ctransition['prev_status'],tracker=tracker).first()
                if ctransition['next_status']:
                    transition.next_status = dbsession.query(TrackerStatus).filter_by(name=ctransition['next_status'],tracker=tracker).first()
                if ctransition['roles']:
                    allroles = []
                    for role in ctransition['roles'].split(','):
                        drole = dbsession.query(TrackerRole).filter_by(tracker=tracker,name=role).first()
                        if drole:
                            allroles.append(drole)
                    transition.roles = allroles

                dbsession.add(transition)
        dbsession.commit()
    return redirect(request.app.url_for('modules.index'))

@bp.route('/modules/export/<slug>')
async def export(request,slug=None):
    if slug:
        if not os.path.exists(os.path.join(modulepath,slug)):
            os.makedirs(os.path.join(modulepath,slug))
    if not os.path.exists(os.path.join(modulepath,slug,'pages')):
        os.makedirs(os.path.join(modulepath,slug,'pages'))
    if not os.path.exists(os.path.join(modulepath,slug,'trackers')):
        os.makedirs(os.path.join(modulepath,slug,'trackers'))
    if not os.path.exists(os.path.join(modulepath,slug,'files')):
        os.makedirs(os.path.join(modulepath,slug,'files'))

    pages = dbsession.query(Page).filter_by(module=slug).all()
    pagesarray = []
    for page in pages:
        curfile = open(os.path.join(modulepath,slug,'pages',page.slug),'w')
        curfile.write(page.content)
        curfile.close()
        pagesarray.append({'title':page.title,'slug':page.slug,'module':page.module,'published':page.published,'require_login':page.require_login,'publish_date':page.publish_date.strftime('%Y-%m-%d'),'expire_date':page.expire_date.strftime('%Y-%m-%d')})
    curfile = open(os.path.join(modulepath,slug,'pagelist.json'),'w')
    curfile.write(json.dumps(pagesarray))
    curfile.close()

    filelinks = dbsession.query(FileLink).filter_by(module=slug).all()
    filesarray = []
    for filelink in filelinks:
        filesarray.append({'title':filelink.title,'slug':filelink.slug,'module':filelink.module,'filename':filelink.filename})
    curfile = open(os.path.join(modulepath,slug,'filelist.json'),'w')
    curfile.write(json.dumps(filesarray))
    curfile.close()

    trackers = dbsession.query(Tracker).filter_by(module=slug).all()
    trackersarray = []
    for tracker in trackers:
        fields = []
        for field in tracker.fields:
            fields.append({'name':field.name,'label':field.label,'field_type':field.field_type,'obj_table':field.obj_table,'obj_field':field.obj_field,'default':field.default})
        roles = []
        for role in tracker.roles:
            roles.append({'name':role.name,'role_type':role.role_type,'compare':role.compare})
        statuses = []
        for status in tracker.statuses:
            statuses.append({'name':status.name,'display_fields':status.display_fields})
        transitions = []
        for transition in tracker.transitions:
            transitions.append({'name':transition.name,'display_fields':transition.display_fields,'edit_fields':transition.edit_fields,'prev_status':transition.prev_status.name if transition.prev_status else None,'next_status':transition.next_status.name if transition.next_status else None,'roles':','.join([ role.name for role in transition.roles ]),'post_page':transition.postpage})


        trackersarray.append({'title':tracker.title,'slug':tracker.slug,'module':tracker.module,'list_fields':tracker.list_fields,'fields':fields,'roles':roles,'statuses':statuses,'transitions':transitions})


    curfile = open(os.path.join(modulepath,slug,'trackerlist.json'),'w')
    curfile.write(json.dumps(trackersarray))
    curfile.close()

    return redirect(request.app.url_for('modules.index'))

@bp.route('/modules/updatelist')
async def updatelist(request):
    modules = []
    pagemodule = dbsession.execute("select distinct module from pages")
    trackermodule = dbsession.execute("select distinct module from trackers")
    filemodule = dbsession.execute("select distinct module from file_links")
    rolemodule = dbsession.execute("select distinct module from module_roles")
    for pm in pagemodule:
        if pm.module.lower() not in modules:
            modules.append(pm.module.lower())
    for tm in trackermodule:
        if tm.module.lower() not in modules:
            modules.append(tm.module.lower())
    for fm in filemodule:
        if fm.module.lower() not in modules:
            modules.append(fm.module.lower())
    for rm in rolemodule:
        if rm.module.lower() not in modules:
            modules.append(rm.module.lower())
    moduledirs = os.listdir(modulepath)
    for md in moduledirs:
        if md.lower() not in modules:
            modules.append(md.lower())
    print("l:" + str(moduledirs))
    for module in modules:
        dbsession.execute("insert into modules (title) values ('" + module + "') on conflict(title) do nothing");
    dbsession.commit()

    return redirect(request.app.url_for('modules.index'))

@bp.route('/modules')
async def index(request):
    modules = dbsession.query(Module)
    paginator = Paginator(modules, 5)
    return html(render(request, 'modules/list.html',title='Modules',fields=[{'label':'Title','name':'title'}],addtitle='Update List',addlink=request.app.url_for('modules.updatelist'),paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))
