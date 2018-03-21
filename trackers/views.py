# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json as jsonresponse
from .models import Tracker, TrackerField, TrackerRole, TrackerStatus, TrackerTransition, TrackerDataUpdate
from .forms import TrackerForm, TrackerFieldForm, TrackerRoleForm, TrackerStatusForm, TrackerTransitionForm
from database import dbsession
from template import render
from sqlalchemy_paginator import Paginator
from sqlalchemy import or_
import os
import datetime
import json
from openpyxl import load_workbook

bp = Blueprint('trackers')

@bp.route('/trackers/<slug>/update/run',methods=['GET'])
def runupdate(request,slug=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    updates = dbsession.query(TrackerDataUpdate).filter_by(status='new').all()
    for update in updates:
        update.status = 'in queue'
        dbsession.add(update)
    dbsession.commit()
    for update in updates:
        update.run()
    return redirect('/trackers/view/' + str(tracker.id) + '#dataupdates')

@bp.route('/trackers/<slug>/update/<update_id>/delete',methods=['POST'])
def deleteupdate(request,slug=None,update_id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    if update_id:
        update = dbsession.query(TrackerDataUpdate).get(int(update_id))
        if(update):
            if update.filename and os.path.exists(update.filename):
                os.remove(update.filename)
            if os.path.exists(os.path.join('upload',tracker.slug,'dataupdate',str(update.id))):
                os.rmdir(os.path.join('upload',tracker.slug,'dataupdate',str(update.id)))
            dbsession.delete(update)
            dbsession.commit()
    return redirect('/trackers/view/' + str(tracker.id) + '#dataupdates')

@bp.route('/trackers/<slug>/data_update',methods=['GET','POST'])
def data_update(request,slug=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    columns = []
    dataupdate = None
    if request.method=='POST':
        if request.form.get('dataupdate_id'):
            dataupdate = dbsession.query(TrackerDataUpdate).get(str(request.form.get('dataupdate_id')))
            dataupdate.data_params=json.dumps(request.form)
            dbsession.add(dataupdate)
            dbsession.commit()
            return redirect('/trackers/view/' + str(tracker.id) + '#dataupdates')
        if request.files.get('excelfile'):
            dataupdate = TrackerDataUpdate(status='new',tracker=tracker,created_date=datetime.datetime.now())
            dbsession.add(dataupdate)
            dbsession.commit()
            dfile = request.files.get('excelfile')
            ext = dfile.type.split('/')[1]
            if not os.path.exists(os.path.join('upload',tracker.slug,'dataupdate',str(dataupdate.id))):
                os.makedirs(os.path.join('upload',tracker.slug,'dataupdate',str(dataupdate.id)))
            dst = os.path.join('upload',tracker.slug,'dataupdate',str(dataupdate.id),dfile.name)
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
            dataupdate.filename = dst
            dbsession.add(dataupdate)
            dbsession.commit()
            wb = load_workbook(filename = dst)
            ws = wb.active
            columns.append({'field_val':'ignore','field_name':'Ignore'})
            columns.append({'field_val':'custom','field_name':'Custom'})
            for row in ws.iter_rows(max_row=1):
                for cell in row:
                    if cell.value.lower() != 'id':
                        columns.append({'field_val':cell.column,'field_name':cell.value})
    return html(render(request,'/trackers/data_update.html',tracker=tracker,columns=columns,dataupdate=dataupdate))

@bp.route('/trackers/<slug>/create_from_excel',methods=['POST','GET'])
def create_from_excel(request,slug=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    fields = []
    field_types = []
    if request.method=='POST':
        if request.form.get('field_name'):
            field_names = request.form['field_name']
            field_label = request.form['field_label']
            field_type = request.form['field_type']
            for i,name in enumerate(field_names):
                tfield = TrackerField(tracker=tracker, name=name, label=field_label[i], field_type=field_type[i])
                dbsession.add(tfield)
            tracker.list_fields = ','.join(field_names)
            dbsession.add(tracker)
            dbsession.commit()
            return redirect('/trackers/view/' + str(tracker.id) + '#fields')
        if request.files.get('excelfile'):
            dfile = request.files.get('excelfile')
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
            wb = load_workbook(filename = dst)
            ws = wb.active
            fieldtitles = []
            fieldtypes = []
            for row in ws.iter_rows(max_row=1):
                for cell in row:
                    fieldtitles.append(cell.value)
            for row in ws.iter_rows(max_row=1,row_offset=1):
                for cell in row:
                    fieldtypes.append(cell.data_type)
            for i,title in enumerate(fieldtitles):
                if title.lower()!='id':
                    fields.append({'field_name':title,'field_type':fieldtypes[i]})
            os.remove(dst)
        field_types = [('string','String'),('text','Text'),('integer','Integer'),('number','Number'),('date','Date'),('datetime','Date Time'),('boolean','Boolean'),('object','Object')]
    return html(render(request,'/trackers/create_from_excel.html',tracker=tracker,fields=fields,field_types=field_types))

@bp.route('/trackers/<slug>/addstatus',methods=['POST','GET'])
@bp.route('/trackers/<slug>/editstatus/',methods=['POST','GET'],name='editstatus')
@bp.route('/trackers/<slug>/editstatus/<id>',methods=['POST','GET'],name='editstatus')
def statusform(request,slug=None,id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    title = 'Create Tracker Status'
    form = TrackerStatusForm(request.form)
    trackerstatus = None
    if id:
        trackerstatus = dbsession.query(TrackerStatus).get(int(id))
    if trackerstatus:
        title = 'Edit Tracker Status'
    if request.method=='POST':
        if form.validate():
            if not trackerstatus:
                trackerstatus=TrackerStatus()
            form.populate_obj(trackerstatus)
            trackerstatus.tracker = tracker
            dbsession.add(trackerstatus)
            dbsession.commit()
            return redirect('/trackers/view/' + str(trackerstatus.tracker.id) + '#statuses')
    else:
        if id:
            trackerstatus = dbsession.query(TrackerStatus).get(int(id))
        if trackerstatus:
            form = TrackerStatusForm(obj=trackerstatus)
            title = 'Edit Tracker Status'
    return html(render(request,'generic/form.html',title=title,form=form,enctype='multipart/form-data'))

@bp.route('/trackers/<slug>/status/<status_id>/delete',methods=['POST'])
def deletestatus(request,slug=None,status_id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    if status_id:
        trackerstatus = dbsession.query(TrackerStatus).get(int(status_id))
        if(trackerstatus):
            dbsession.delete(trackerstatus)
            dbsession.commit()
    return redirect('/trackers/view/' + str(trackerstatus.tracker.id) + '#statuses')

@bp.route('/trackers/<slug>/roles/json')
def rolesjson(request,slug=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    trackerroles = dbsession.query(TrackerRole).filter(TrackerRole.tracker==tracker,TrackerRole.name.ilike('%' + request.args['q'][0] + '%')).all() 
    return jsonresponse([ {'id':role.id,'name':role.name} for role in trackerroles ])

@bp.route('/trackers/<slug>/addtransition',methods=['POST','GET'])
@bp.route('/trackers/<slug>/edittransition/',methods=['POST','GET'],name='edittransition')
@bp.route('/trackers/<slug>/edittransition/<id>',methods=['POST','GET'],name='edittransition')
def transitionform(request,slug=None,id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    title = 'Create Tracker Transition'
    form = TrackerTransitionForm(request.form)
    dstatuses = [('','None'),] + [(str(g.id),g.name) for g in dbsession.query(TrackerStatus).filter(TrackerStatus.tracker==tracker).all()]
    form.prev_status_id.choices = dstatuses
    form.next_status_id.choices = dstatuses
    trackertransition = None
    if id:
        trackertransition = dbsession.query(TrackerTransition).get(int(id))
    if trackertransition:
        title = 'Edit Tracker Transition'
    if request.method=='POST':
        if form.validate():
            if not trackertransition:
                trackertransition=TrackerTransition()
            if form.roles.data:
                role_ids = form.roles.data.split(',')
                roles = [ dbsession.query(TrackerRole).get(role_id) for role_id in role_ids ]
                trackertransition.roles = roles
            else:
                trackertransition.roles = []
            del(form['roles'])
            form.populate_obj(trackertransition)
            if form.prev_status_id.data=='':
                trackertransition.prev_status = None
                trackertransition.prev_status_id = None
            if form.next_status_id.data=='':
                trackertransition.next_status = None
                trackertransition.next_status_id = None
            trackertransition.tracker = tracker
            dbsession.add(trackertransition)
            dbsession.commit()
            return redirect('/trackers/view/' + str(trackertransition.tracker.id) + '#transitions')
    else:
        if id:
            trackertransition = dbsession.query(TrackerTransition).get(int(id))
        if trackertransition:
            form = TrackerTransitionForm(obj=trackertransition)
            form.prev_status_id.choices = dstatuses
            form.next_status_id.choices = dstatuses
            title = 'Edit Tracker Transition'
    return html(render(request,'generic/form.html',title=title,rolesdata=trackertransition.roles,form=form,tracker=tracker,enctype='multipart/form-data'))

@bp.route('/trackers/<slug>/transition/<transition_id>/delete',methods=['POST'])
def deletetransition(request,slug=None,transition_id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    if transition_id:
        trackertransition = dbsession.query(TrackerTransition).get(int(transition_id))
        if(trackertransition):
            dbsession.delete(trackertransition)
            dbsession.commit()
    return redirect('/trackers/view/' + str(trackertransition.tracker.id) + '#transitions')

@bp.route('/trackers/<slug>/addrole',methods=['POST','GET'])
@bp.route('/trackers/<slug>/editrole/',methods=['POST','GET'],name='editrole')
@bp.route('/trackers/<slug>/editrole/<id>',methods=['POST','GET'],name='editrole')
def roleform(request,slug=None,id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    title = 'Create Tracker Role'
    form = TrackerRoleForm(request.form)
    trackerrole = None
    if id:
        trackerrole = dbsession.query(TrackerRole).get(int(id))
    if trackerrole:
        title = 'Edit Tracker Role'
    if request.method=='POST':
        if form.validate():
            if not trackerrole:
                trackerrole=TrackerRole()
            form.populate_obj(trackerrole)
            trackerrole.tracker = tracker
            dbsession.add(trackerrole)
            dbsession.commit()
            return redirect('/trackers/view/' + str(trackerrole.tracker.id) + '#roles')
    else:
        if id:
            trackerrole = dbsession.query(TrackerRole).get(int(id))
        if trackerrole:
            form = TrackerRoleForm(obj=trackerrole)
            title = 'Edit Tracker Role'
    return html(render(request,'generic/form.html',title=title,form=form,enctype='multipart/form-data'))

@bp.route('/trackers/<slug>/role/<role_id>/delete',methods=['POST'])
def deleterole(request,slug=None,role_id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    if role_id:
        trackerrole = dbsession.query(TrackerRole).get(int(role_id))
        if(trackerrole):
            dbsession.delete(trackerrole)
            dbsession.commit()
    return redirect('/trackers/view/' + str(trackerrole.tracker.id) + '#roles')

@bp.route('/trackers/<slug>/addfield',methods=['POST','GET'])
@bp.route('/trackers/<slug>/editfield/',methods=['POST','GET'],name='editfield')
@bp.route('/trackers/<slug>/editfield/<id>',methods=['POST','GET'],name='editfield')
def fieldform(request,slug=None,id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    title = 'Create Tracker Field'
    form = TrackerFieldForm(request.form)
    trackerfield = None
    if id:
        trackerfield = dbsession.query(TrackerField).get(int(id))
    if trackerfield:
        title = 'Edit Tracker Field'
    if request.method=='POST':
        if form.validate():
            if not trackerfield:
                trackerfield=TrackerField()
            form.populate_obj(trackerfield)
            trackerfield.tracker = tracker
            dbsession.add(trackerfield)
            dbsession.commit()
            return redirect('/trackers/view/' + str(trackerfield.tracker.id) + '#fields')
    else:
        if id:
            trackerfield = dbsession.query(TrackerField).get(int(id))
        if trackerfield:
            form = TrackerFieldForm(obj=trackerfield)
            title = 'Edit Tracker Field'
    return html(render(request,'generic/form.html',title=title,form=form,enctype='multipart/form-data'))

@bp.route('/trackers/<slug>/field/<field_id>/delete',methods=['POST'])
def deletefield(request,slug=None,field_id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    if field_id:
        trackerfield = dbsession.query(TrackerField).get(int(field_id))
        if(trackerfield):
            dbsession.delete(trackerfield)
            dbsession.commit()
    return redirect('/trackers/view/' + str(trackerfield.tracker.id) + '#fields')

@bp.route('/trackers/<slug>/field/<field_id>/json')
def fieldjson(request,slug=None,field_id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    if field_id:
        trackerfield = dbsession.query(TrackerField).get(int(field_id))
        if(trackerfield):
            sqlq = "select id," + trackerfield.main_obj_field() + " from " + trackerfield.obj_table + " where " + " or ".join([field + " like '%" + request.args['q'][0] + "%' " for field in trackerfield.obj_fields() ])
            results = dbsession.execute(sqlq)
            return jsonresponse([ {'id':result.id,'name':result.name} for result in results ])


@bp.route('/trackers/view/')
@bp.route('/trackers/view/<id>')
def view(request,id=None):
    tracker = dbsession.query(Tracker).get(int(id))
    dataupdates = dbsession.query(TrackerDataUpdate).filter(TrackerDataUpdate.tracker==tracker)
    updatespaginator = Paginator(dataupdates, 10)
    return html(render(request,'trackers/view.html',tracker=tracker,updatespaginator=updatespaginator,curupdatepage=updatespaginator.page(int(request.args['updatepage'][0]) if 'updatepage' in request.args else 1)))

@bp.route('/trackers/updatedb/<id>')
def updatedb(request,id=None):
    tracker = dbsession.query(Tracker).get(int(id))
    tracker.updatedb()
    return redirect('/trackers/view/' + str(id))

@bp.route('/trackers/create',methods=['POST','GET'])
@bp.route('/trackers/edit/',methods=['POST','GET'],name='edit')
@bp.route('/trackers/edit/<id>',methods=['POST','GET'],name='edit')
def form(request,id=None):
    title = 'Create Tracker'
    form = TrackerForm(request.form)
    tracker = None
    if request.method=='POST':
        if id:
            tracker = dbsession.query(Tracker).get(int(id))
        if tracker:
            title = 'Edit Tracker'
        if form.validate():
            if not tracker:
                tracker=Tracker()
            form.populate_obj(tracker)
            dbsession.add(tracker)
            newstatus = TrackerStatus(name='New',tracker=tracker)
            dbsession.add(newstatus)
            adminrole = TrackerRole(name='Admin',role_type='module',tracker=tracker)
            dbsession.add(adminrole)
            statusfield = TrackerField(name='record_status',label='Status',tracker=tracker,field_type='string')
            dbsession.add(statusfield)
            idfield = TrackerField(name='id',label='ID',tracker=tracker,field_type='integer')
            dbsession.add(idfield)
            dbsession.commit()
            return redirect('/trackers/view/' + str(tracker.id))
    else:
        if id:
            tracker = dbsession.query(Tracker).get(int(id))
            if tracker:
                form = TrackerForm(obj=tracker)
                title = 'Edit Tracker'

    return html(render(request,'generic/form.html',title=title,form=form,enctype='multipart/form-data'))

@bp.route('/trackers')
def index(request):
    trackers = dbsession.query(Tracker)
    paginator = Paginator(trackers, 5)
    return html(render(request, 'generic/list.html',title='Trackers',editlink=request.app.url_for('trackers.view'),addlink=request.app.url_for('trackers.form'),fields=[{'label':'Title','name':'title'},{'label':'Slug','name':'slug'},{'label':'List Fields','name':'list_fields'}],paginator=paginator,curpage=paginator.page(int(request.args['page'][0]) if 'page' in request.args else 1)))

@bp.route('/system/<slug>/')
def viewlist(request,slug=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    return html(render(request,'trackers/viewlist.html',tracker=tracker))

@bp.route('/system/<slug>/addrecord',methods=['POST','GET'])
def addrecord(request,slug=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    if request.method=='POST':
        tracker.addrecord(request.form)
        return redirect('/system/' + slug)
    newtransition = dbsession.query(TrackerTransition).filter_by(tracker=tracker,name='new').first()
    return html(render(request,'trackers/formrecord.html',tracker=tracker,transition=newtransition))

@bp.route('/system/<slug>/edit/<transition_id>/<record_id>',methods=['POST','GET'])
def editrecord(request,slug=None,transition_id=None,record_id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    transition = None
    record = None
    if record_id:
        record = tracker.records(record_id)
    if transition_id:
        transition = dbsession.query(TrackerTransition).get(transition_id)
    if request.method=='POST':
        tracker.editrecord(request.form)
        return redirect(request.app.url_for('trackers.viewrecord',slug=tracker.slug,id=record_id))
    return html(render(request,'trackers/formrecord.html',tracker=tracker,transition=transition,record=record))

@bp.route('/system/<slug>/<id>',methods=['POST','GET'])
def viewrecord(request,slug=None,id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    record = None
    if request.method=='POST':
        return redirect('/system/' + slug + '/viewrecord/' + id)
    if(id):
        record = tracker.records(id)
    return html(render(request,'trackers/viewrecord.html',tracker=tracker,record=record))
