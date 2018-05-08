# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json as jsonresponse
from .models import Tree, TreeNode
from .forms import TreeForm, TreeNodeForm
from database import dbsession
from template import render
from decorators import authorized
from sqlalchemy_paginator import Paginator

bp = Blueprint('trees')

@bp.route('/trees/view/<slug>',methods=['GET','POST'])
@authorized(object_type='tree')
async def view(request, slug):
    tree = dbsession.query(Tree).filter_by(slug=slug).first()
    if tree:
        return html(render(request,'trees/view.html',tree=tree))
    else:
        print("No tree to view")
        session['flashmessage'] = 'No tree to view'
        return redirect('/')

@bp.route('/trees/nodejson/<slug>',methods=['GET'])
@bp.route('/trees/nodejson/<slug>/<node_id>',methods=['GET'])
@authorized(object_type='tree')
async def nodejson(request, slug, node_id=None):
    tree = dbsession.query(Tree).filter_by(slug=slug).first()
    if node_id:
        curnode = dbsession.query(TreeNode).get(node_id)
        if curnode:
            print('children:' + str(curnode.children))
        return jsonresponse([ { 'text': cnode.title, 'state':{ 'opened':False }, 'children':True if cnode.children else False, 'data':{ 'dbid':cnode.id } } for cnode in curnode.children ])
    else:
        return jsonresponse([{ 'text':tree.rootnode.title , 'state':{ 'opened':False }, 'children':True, 'data':{ 'dbid':tree.rootnode.id } }])

@bp.route('/trees/addnode')
@bp.route('/trees/addnode/<parent_id>',methods=['GET','POST'])
@authorized(object_type='tree')
async def addnode(request, parent_id):
    parentnode = dbsession.query(TreeNode).get(parent_id)
    form = TreeNodeForm(request.form)
    if request.method=='POST':
        treenode = TreeNode()
        form.populate_obj(treenode)
        treenode.parent_id = int(request.form.get('parent_id'))
        dbsession.add(treenode)
        try:
            dbsession.commit()
        except BaseException as exp:
            dbsession.rollback()
        return jsonresponse([{ 'id':treenode.id , 'title':treenode.title }])
    return html(render(request,'trees/nodeform.html',form=form,parentnode=parentnode))

@bp.route('/trees/renamenode')
@bp.route('/trees/renamenode/<node_id>',methods=['POST'])
@authorized(object_type='tree')
async def renamenode(request, node_id):
    nnode = dbsession.query(TreeNode).get(node_id)
    if request.method=='POST':
        nnode.title = request.form.get('title')
        dbsession.add(nnode)
        dbsession.commit()
    return jsonresponse([{ 'id':nnode.id }])

@bp.route('/trees/pastenode')
@bp.route('/trees/pastenode/<node_id>/<paste_mode>',methods=['POST'])
@authorized(object_type='tree')
async def pastenode(request, node_id, paste_mode):
    parentnode = dbsession.query(TreeNode).get(node_id)
    if request.method=='POST':
        currentnode = dbsession.query(TreeNode).get(request.form['node[0][data][dbid]'][0])
        if currentnode:
            if paste_mode=='move_node':
                currentnode.parent_id = node_id
                dbsession.add(currentnode)
                dbsession.commit()
            else:
                currentnode.copy(node_id,parentnode.slug)
                dbsession.commit()
    return jsonresponse([{ 'status':'done' }])

@bp.route('/trees/deletenode')
@bp.route('/trees/deletenode/<node_id>',methods=['POST'])
@authorized(object_type='tree')
async def deletenode(request, node_id):
    nnode = dbsession.query(TreeNode).get(node_id)
    if request.method=='POST':
        dbsession.delete(nnode)
        dbsession.commit()
    return jsonresponse([{ 'status':'done' }])

@bp.route('/trees/create',methods=['POST','GET'])
@bp.route('/trees/edit/',methods=['POST','GET'],name='edit')
@bp.route('/trees/edit/<slug>',methods=['POST','GET'])
@authorized(object_type='tree')
async def form(request,slug=None):
    title = 'Create Tree'
    form = TreeForm(request.form)
    tree=None
    if request.method=='POST':
        tree = dbsession.query(Tree).filter_by(slug=form.slug.data).first()
        if not tree and slug:
            tree = dbsession.query(Tree).get(int(slug))
        if tree:
            title = 'Edit Tree'
        if form.validate():
            newtree = False
            rootnode = None
            if not tree:
                newtree = True
                tree=Tree()
            form.populate_obj(tree)
            dbsession.add(tree)
            dbsession.commit()
            if newtree:
                rootnode=TreeNode(tree=tree)
                rootnode.title = tree.title
                rootnode.slug = tree.slug
                rootnode.require_login = tree.require_login
                rootnode.allowed_roles = tree.allowed_roles
                rootnode.published = tree.published
                rootnode.publish_date = tree.publish_date
                rootnode.expire_date = tree.expire_date
                dbsession.add(rootnode)
                dbsession.commit()
            if request.form['submit'][0]=='Submit':
                return redirect('/trees')
            else:
                return redirect('/trees/edit/' + tree.slug)
    else:
        if slug is not None:
            tree = dbsession.query(Tree).filter_by(slug=slug).first()
            if not tree:
                tree = dbsession.query(Tree).get(int(slug))
            if tree:
                form = TreeForm(obj=tree)
                title = 'Edit Tree'

    return html(render(request,'generic/form.html',title=title,tree=tree, form=form,enctype='multipart/form-data'))

@bp.route('/trees')
@authorized(object_type='tree')
async def index(request):
    trees = dbsession.query(Tree)
    paginator = Paginator(trees, 5)
    return html(render(request,
        'trees/list.html',title='Trees',editlink=request.app.url_for('trees.edit'),addlink=request.app.url_for('trees.form'),fields=[{'label':'Module','name':'module'},{'label':'Title','name':'title'},{'label':'Slug','name':'slug'}],paginator=paginator,curpage=paginator.page(int(request.args['tree'][0]) if 'tree' in request.args else 1)))
