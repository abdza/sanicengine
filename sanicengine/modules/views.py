# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Module
from sanicengine.pages.models import Page
from sanicengine.trackers.models import Tracker,TrackerField,TrackerRole,TrackerStatus,TrackerTransition
from sanicengine.fileLinks.models import FileLink
from sanicengine.trees.models import Tree, TreeNode, TreeNodeUser
from .forms import ModuleForm
from sanicengine.database import dbsession
from sanicengine.decorators import authorized
from sanicengine.template import render
from sqlalchemy_paginator import Paginator
import os
import json
import shutil 

bp = Blueprint('modules')
modulepath = 'custom_module'

def readarray(arrayvar,arraykey,default=''):
    if arraykey in arrayvar:
        return arrayvar[arraykey]
    else:
        return default

@bp.route('/modules/import/<slug>')
@authorized(require_superuser=True)
async def importmodule(request,slug=None):
    if(os.path.exists(os.path.join(modulepath,slug))):


        """ Import pages """
        curfile = open(os.path.join(modulepath,slug,'pagelist.json'),'r')
        pagesarray = json.loads(curfile.read())
        curfile.close()
        for cpage in pagesarray:
            page = dbsession.query(Page).filter_by(module=slug,slug=cpage['slug']).first()
            if not page:
                page = Page()

            page.title = readarray(cpage,'title')
            page.slug = readarray(cpage,'slug')
            page.module = readarray(cpage,'module')
            page.published = readarray(cpage,'published',False)
            page.runable = readarray(cpage,'runable',False)
            page.require_login = readarray(cpage,'require_login',False)
            page.allowed_roles = readarray(cpage,'allowed_roles',False)
            page.publish_date = readarray(cpage,'publish_date',None)
            page.expire_date = readarray(cpage,'expire_date',None)
            try:
                cfile = open(os.path.join(modulepath,slug,'pages',cpage['slug']),'r')
                page.content = cfile.read()
                cfile.close()
            except:
                print("Error importing page content for " + cpage['slug'])
            dbsession.add(page)
        
        """ Import fileLinks """
        curfile = open(os.path.join(modulepath,slug,'filelist.json'),'r')
        filearray = json.loads(curfile.read())
        curfile.close()
        for cfile in filearray:
            filelink = dbsession.query(FileLink).filter_by(module=slug,slug=cfile['slug']).first()
            if not filelink:
                filelink = FileLink()

            filelink.title = readarray(cfile,'title')
            filelink.slug = readarray(cfile,'slug')
            filelink.module = readarray(cfile,'module')
            filelink.published = readarray(cfile,'published',False)
            filelink.filename = readarray(cfile,'filename')
            filelink.filepath = readarray(cfile,'filepath')
            filelink.require_login = readarray(cfile,'require_login',False)
            filelink.allowed_roles = readarray(cfile,'allowed_roles',False)
            filelink.published_date = readarray(cfile,'published_date',None)
            filelink.expire_date = readarray(cfile,'expire_date',None)
            try:
                shutil.copy2(os.path.join(modulepath,slug,'files',os.path.basename(filelink.filepath)),filelink.filepath)
            except:
                print("Error copying file to import file " + cfile['slug'])
            dbsession.add(filelink)

        """ Import trees """
        curfile = open(os.path.join(modulepath,slug,'treelist.json'),'r')
        treearray = json.loads(curfile.read())
        curfile.close()
        for ctree in treearray:
            tree = dbsession.query(Tree).filter_by(module=slug,slug=ctree['slug']).first()
            if not tree:
                tree = Tree()

            tree.title = readarray(ctree,'title')
            tree.slug = readarray(ctree,'slug')
            tree.module = readarray(ctree,'module')
            tree.datastr = readarray(ctree,'datastr')
            tree.published = readarray(ctree,'published',False)
            tree.require_login = readarray(ctree,'require_login',False)
            tree.allowed_roles = readarray(ctree,'allowed_roles',False)
            tree.publish_date = readarray(ctree,'publish_date',None)
            tree.expire_date = readarray(ctree,'expire_date',None)
            dbsession.add(tree)
            dbsession.commit()
            dbsession.flush()
            TreeNode.treeload(tree,ctree['nodes'],None)

        """ Import trackers """
        curfile = open(os.path.join(modulepath,slug,'trackerlist.json'),'r')
        trackersarray = json.loads(curfile.read())
        curfile.close()
        for ctracker in trackersarray:
            tracker = dbsession.query(Tracker).filter_by(module=slug,slug=ctracker['slug']).first()
            if not tracker:
                tracker = Tracker()

            tracker.title = readarray(ctracker,'title')
            tracker.slug = readarray(ctracker,'slug')
            tracker.module = readarray(ctracker,'module')
            tracker.list_fields = readarray(ctracker,'list_fields')
            tracker.search_fields = readarray(ctracker,'search_fields')
            tracker.filter_fields = readarray(ctracker,'filter_fields')
            tracker.excel_fields = readarray(ctracker,'excel_fields')
            tracker.detail_fields = readarray(ctracker,'detail_fields')
            tracker.published = readarray(ctracker,'published',False)
            tracker.pagelimit = readarray(ctracker,'pagelimit')
            tracker.require_login = readarray(ctracker,'require_login',False)
            tracker.allowed_roles = readarray(ctracker,'allowed_roles',False)
            tracker.publish_date = readarray(ctracker,'publish_date',None)
            tracker.expire_date = readarray(ctracker,'expire_date',None)
            tracker.data_table_name = readarray(ctracker,'data_table_name')
            tracker.update_table_name = readarray(ctracker,'update_table_name')
            dbsession.add(tracker)

            for cfield in ctracker['fields']:
                field = dbsession.query(TrackerField).filter_by(tracker=tracker,name=cfield['name']).first()
                if not field:
                    field = TrackerField()
                field.tracker = tracker
                field.name = readarray(cfield,'name')
                field.label = readarray(cfield,'label')
                field.field_type = readarray(cfield,'field_type')
                field.obj_table = readarray(cfield,'obj_table')
                field.obj_field = readarray(cfield,'obj_field')
                field.default = readarray(cfield,'default')
                dbsession.add(field)

            for crole in ctracker['roles']:
                role = dbsession.query(TrackerRole).filter_by(tracker=tracker,name=crole['name']).first()
                if not role:
                    role = TrackerRole()
                role.tracker = tracker
                role.name = readarray(crole,'name')
                role.role_type = readarray(crole,'role_type')
                role.compare = readarray(crole,'compare')
                dbsession.add(role)

            for cstatus in ctracker['statuses']:
                status = dbsession.query(TrackerStatus).filter_by(tracker=tracker,name=cstatus['name']).first()
                if not status:
                    status = TrackerStatus()

                status.tracker = tracker
                status.name = readarray(cstatus,'name')
                status.display_fields = readarray(cstatus,'display_fields')
                dbsession.add(status)

            for ctransition in ctracker['transitions']:
                transition = dbsession.query(TrackerTransition).filter_by(tracker=tracker,name=ctransition['name']).first()
                if not transition:
                    transition = TrackerTransition()
                transition.tracker = tracker
                transition.name = readarray(ctransition,'name')
                transition.display_fields = readarray(ctransition,'display_fields')
                transition.edit_fields = readarray(ctransition,'edit_fields')
                transition.postpage = readarray(ctransition,'postpage')

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
    request['session']['flashmessage'] = 'Module ' + slug + ' has been imported'
    return redirect(request.app.url_for('modules.index'))

@bp.route('/modules/export/<slug>')
@authorized(require_superuser=True)
async def export(request,slug=None):
    if slug:
        print("curpath:" + str(os.path.join(modulepath,slug)))
        if not os.path.exists(os.path.join(modulepath,slug)):
            os.makedirs(os.path.join(modulepath,slug))
        if not os.path.exists(os.path.join(modulepath,slug,'pages')):
            os.makedirs(os.path.join(modulepath,slug,'pages'))
        if not os.path.exists(os.path.join(modulepath,slug,'trackers')):
            os.makedirs(os.path.join(modulepath,slug,'trackers'))
        if not os.path.exists(os.path.join(modulepath,slug,'files')):
            os.makedirs(os.path.join(modulepath,slug,'files'))

        """ Export pages """
        pages = dbsession.query(Page).filter_by(module=slug).all()
        pagesarray = []
        for page in pages:
            curfile = open(os.path.join(modulepath,slug,'pages',page.slug),'w')
            curfile.write(page.content)
            curfile.close()
            pagesarray.append({
                'title':page.title,
                'slug':page.slug,
                'module':page.module,
                'published':page.published,
                'runable':page.runable,
                'require_login':page.require_login,
                'allowed_roles':page.allowed_roles,
                'publish_date':page.publish_date.strftime('%Y-%m-%d') if page.publish_date else None,
                'expire_date':page.expire_date.strftime('%Y-%m-%d') if page.expire_date else None 
                })
        curfile = open(os.path.join(modulepath,slug,'pagelist.json'),'w')
        curfile.write(json.dumps(pagesarray))
        curfile.close()

        """ Export fileLinks """
        filelinks = dbsession.query(FileLink).filter_by(module=slug).all()
        filesarray = []
        for filelink in filelinks:
            if os.path.exists(filelink.filepath):
                shutil.copy2(filelink.filepath,os.path.join(modulepath,slug,'files',os.path.basename(filelink.filepath)))
                filesarray.append({
                    'title':filelink.title,
                    'slug':filelink.slug,
                    'module':filelink.module,
                    'published':filelink.published,
                    'filename':filelink.filename,
                    'filepath':filelink.filepath,
                    'require_login':filelink.require_login,
                    'allowed_roles':filelink.allowed_roles,
                    'publish_date':filelink.publish_date.strftime('%Y-%m-%d') if filelink.publish_date else None,
                    'expire_date':filelink.expire_date.strftime('%Y-%m-%d') if filelink.expire_date else None 
                    })
        curfile = open(os.path.join(modulepath,slug,'filelist.json'),'w')
        curfile.write(json.dumps(filesarray))
        curfile.close()

        """ Export trackers """
        trackers = dbsession.query(Tracker).filter_by(module=slug).all()
        trackersarray = []
        for tracker in trackers:
            fields = []
            for field in tracker.fields:
                fields.append({
                    'name':field.name,
                    'label':field.label,
                    'field_type':field.field_type,
                    'obj_table':field.obj_table,
                    'obj_field':field.obj_field,
                    'default':field.default
                    })
            roles = []
            for role in tracker.roles:
                roles.append({
                    'name':role.name,
                    'role_type':role.role_type,
                    'compare':role.compare
                    })
            statuses = []
            for status in tracker.statuses:
                statuses.append({
                    'name':status.name,
                    'display_fields':status.display_fields
                    })
            transitions = []
            for transition in tracker.transitions:
                transitions.append({
                    'name':transition.name,
                    'display_fields':transition.display_fields,
                    'edit_fields':transition.edit_fields,
                    'prev_status':transition.prev_status.name if transition.prev_status else None,
                    'next_status':transition.next_status.name if transition.next_status else None,
                    'roles':','.join([ role.name for role in transition.roles ]),
                    'postpage':transition.postpage
                    })


            trackersarray.append({
                'title':tracker.title,
                'slug':tracker.slug,
                'module':tracker.module,
                'list_fields':tracker.list_fields,
                'search_fields':tracker.search_fields,
                'filter_fields':tracker.filter_fields,
                'excel_fields':tracker.excel_fields,
                'detail_fields':tracker.detail_fields,
                'published':tracker.published,
                'pagelimit':tracker.pagelimit,
                'require_login':tracker.require_login,
                'allowed_roles':tracker.allowed_roles,
                'publish_date':tracker.publish_date.strftime('%Y-%m-%d') if tracker.publish_date else None,
                'expire_date':tracker.expire_date.strftime('%Y-%m-%d') if tracker.expire_date else None,
                'data_table_name':tracker.data_table_name,
                'update_table_name':tracker.update_table_name,
                'fields':fields,
                'roles':roles,
                'statuses':statuses,
                'transitions':transitions
                })


        curfile = open(os.path.join(modulepath,slug,'trackerlist.json'),'w')
        curfile.write(json.dumps(trackersarray))
        curfile.close()


        """ Export Trees """
        trees = dbsession.query(Tree).filter_by(module=slug).all()
        treearray = []
        for tree in trees:
            treearray.append({
                'title':tree.title,
                'slug':tree.slug,
                'module':tree.module,
                'datastr':tree.datastr,
                'published':tree.published,
                'require_login':tree.require_login,
                'allowed_roles':tree.allowed_roles,
                'publish_date':tree.publish_date.strftime('%Y-%m-%d') if tree.publish_date else None,
                'expire_date':tree.expire_date.strftime('%Y-%m-%d') if tree.expire_date else None,
                'nodes':tree.rootnode.treedump()
                })

        curfile = open(os.path.join(modulepath,slug,'treelist.json'),'w')
        curfile.write(json.dumps(treearray))
        curfile.close()


    request['session']['flashmessage'] = 'Module ' + slug + ' has been exported'
    return redirect(request.app.url_for('modules.index'))

@bp.route('/modules/updatelist')
@authorized(require_superuser=True)
async def updatelist(request):
    dbsession.execute("delete from modules");
    dbsession.commit()
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
    if os.path.exists(modulepath):
        moduledirs = os.listdir(modulepath)
        for md in moduledirs:
            if md.lower() not in modules and md.lower() not in ['templates'] and not md[0]=='.':
                modules.append(md.lower())
    for module in modules:
        try:
            dbsession.execute("insert into modules (title) values ('" + module + "')");
            dbsession.commit()
        except:
            print("Got error inserting module")
            dbsession.rollback()

    return redirect(request.app.url_for('modules.index'))

@bp.route('/modules')
@authorized(require_superuser=True)
async def index(request):
    modules = dbsession.query(Module)
    paginator = Paginator(modules, 10)
    return html(render(request, 'modules/list.html',title='Modules',fields=[{'label':'Title','name':'title'}],addtitle='Update List',addlink=request.app.url_for('modules.updatelist'),paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)),headers={'X-Frame-Options':'deny','X-Content-Type-Options':'nosniff'})
