# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Tracker, TrackerField
from .forms import TrackerForm, TrackerFieldForm
from database import dbsession
from template import render
from sqlalchemy_paginator import Paginator

bp = Blueprint('trackers')

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
