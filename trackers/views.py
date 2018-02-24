# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Tracker, TrackerField, TrackerRole, TrackerStatus, TrackerTransition
from .forms import TrackerForm, TrackerFieldForm, TrackerRoleForm, TrackerStatusForm, TrackerTransitionForm
from database import dbsession
from template import render
from sqlalchemy_paginator import Paginator

bp = Blueprint('trackers')

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

@bp.route('/trackers/<slug>/addtransition',methods=['POST','GET'])
@bp.route('/trackers/<slug>/edittransition/',methods=['POST','GET'],name='edittransition')
@bp.route('/trackers/<slug>/edittransition/<id>',methods=['POST','GET'],name='edittransition')
def transitionform(request,slug=None,id=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    title = 'Create Tracker Transition'
    form = TrackerTransitionForm(request.form)
    trackertransition = None
    if id:
        trackertransition = dbsession.query(TrackerTransition).get(int(id))
    if trackertransition:
        title = 'Edit Tracker Transition'
    if request.method=='POST':
        if form.validate():
            if not trackertransition:
                trackertransition=TrackerTransition()
            form.populate_obj(trackertransition)
            trackertransition.tracker = tracker
            dbsession.add(trackertransition)
            dbsession.commit()
            return redirect('/trackers/view/' + str(trackertransition.tracker.id) + '#transitions')
    else:
        if id:
            trackertransition = dbsession.query(TrackerTransition).get(int(id))
        if trackertransition:
            form = TrackerTransitionForm(obj=trackertransition)
            title = 'Edit Tracker Transition'
    return html(render(request,'generic/form.html',title=title,form=form,enctype='multipart/form-data'))

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

@bp.route('/trackers/view/')
@bp.route('/trackers/view/<id>')
def view(request,id=None):
    tracker = dbsession.query(Tracker).get(int(id))
    return html(render(request,'trackers/view.html',tracker=tracker))

@bp.route('/trackers/updatedb/<id>')
def updatedb(request,id=None):
    tracker = dbsession.query(Tracker).get(int(id))
    tracker.updatedb()
    return redirect('/trackers/view/' + str(id))

@bp.route('/trackers/create',methods=['POST','GET'])
@bp.route('/trackers/edit/',methods=['POST','GET'],name='edit')
@bp.route('/trackers/edit/<slug>',methods=['POST','GET'])
def form(request,slug=None):
    title = 'Create Tracker'
    form = TrackerForm(request.form)
    if request.method=='POST':
        tracker = dbsession.query(Tracker).filter_by(slug=form.slug.data).first()
        if not tracker and slug:
            tracker = dbsession.query(Tracker).get(int(slug))
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
            dbsession.commit()
            return redirect('/trackers')
    else:
        if slug is not None:
            tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
            if not tracker:
                tracker = dbsession.query(Tracker).get(int(slug))
            if tracker:
                form = TrackerForm(obj=tracker)
                title = 'Edit Tracker'

    return html(render(request,'generic/form.html',title=title,form=form,enctype='multipart/form-data'))

@bp.route('/trackers')
def index(request):
    trackers = dbsession.query(Tracker)
    paginator = Paginator(trackers, 5)
    return html(render(request, 'generic/list.html',title='Trackers',editlink=request.app.url_for('trackers.view'),addlink=request.app.url_for('trackers.form'),fields=[{'label':'Title','name':'title'},{'label':'Slug','name':'slug'}],paginator=paginator,curpage=paginator.page(int(request.args['tracker'][0]) if 'tracker' in request.args else 1)))

@bp.route('/system/<slug>/')
def viewlist(request,slug=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    return html(render(request,'trackers/viewlist.html',tracker=tracker))

@bp.route('/system/<slug>/addrecord',methods=['POST','GET'])
def addrecord(request,slug=None):
    tracker = dbsession.query(Tracker).filter_by(slug=slug).first()
    if request.method=='POST':
        tracker.addrecord(request.form)
    newtransition = dbsession.query(TrackerTransition).filter_by(tracker=tracker,name='new').first()
    return html(render(request,'trackers/addrecord.html',tracker=tracker,newtransition=newtransition))
