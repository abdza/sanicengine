# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json as jsonresponse
from .models import Tree, TreeNode, TreeNodeUser
from .forms import TreeForm, TreeNodeForm, TreeNodeUserForm
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

@bp.route('/trees/nodeview/')
@bp.route('/trees/nodeview/<node_id>')
@authorized(object_type='tree',require_admin=True)
async def nodeview(request,node_id=None):
    node = None
    if node_id:
        node = dbsession.query(TreeNode).get(node_id)
    return html(render(request,'trees/nodeview.html',node=node))

@bp.route('/trees/nodejson/<slug>',methods=['GET'])
@bp.route('/trees/nodejson/<slug>/<node_id>',methods=['GET'])
@authorized(object_type='tree',require_admin=True)
async def nodejson(request, slug, node_id=None):
    tree = dbsession.query(Tree).filter_by(slug=slug).first()
    if node_id:
        curnode = dbsession.query(TreeNode).get(node_id)
        return jsonresponse([ { 'text': cnode.title, 'state':{ 'opened':False }, 'children':True if cnode.children else False, 'data':{ 'dbid':cnode.id } } for cnode in curnode.children ])
    else:
        return jsonresponse([{ 'text':tree.rootnode.title , 'state':{ 'opened':False }, 'children':True, 'data':{ 'dbid':tree.rootnode.id } }])

@bp.route('/trees/editnode')
@bp.route('/trees/editnode/<node_id>',methods=['GET','POST'])
@authorized(object_type='tree',require_admin=True)
async def editnode(request, node_id):
    curnode = dbsession.query(TreeNode).get(node_id)
    parentnode = curnode.parent
    if request.method=='POST':
        form = TreeNodeForm(request.form)
        treenode = dbsession.query(TreeNode).get(request.form.get('id'))
        form.populate_obj(treenode)
        if 'parent_id' in request.form:
            treenode.parent_id = int(request.form.get('parent_id'))
        dbsession.add(treenode)
        try:
            dbsession.commit()
        except BaseException as exp:
            dbsession.rollback()
        return jsonresponse([{ 'id':treenode.id , 'title':treenode.title }])
    else:
        form = TreeNodeForm(obj=curnode)

    return html(render(request,'trees/nodeform.html',node=curnode,form=form,parentnode=parentnode))

@bp.route('/trees/deletenodeuser')
@bp.route('/trees/deletenodeuser/<node_id>/<nodeuser_id>',methods=['GET','POST'])
@authorized(object_type='tree',require_admin=True)
async def deletenodeuser(request, node_id=None, nodeuser_id=None):
    nodeuser = None
    treenode = dbsession.query(TreeNode).get(node_id)
    if nodeuser_id:
        nodeuser = dbsession.query(TreeNodeUser).get(nodeuser_id)
        if request.method=='POST':
            dbsession.delete(nodeuser)
            try:
                dbsession.commit()
            except BaseException as exp:
                dbsession.rollback()
            return jsonresponse([{ 'id':treenode.id , 'title':treenode.title }])

@bp.route('/trees/nodeuserform')
@bp.route('/trees/nodeuserform/<node_id>',methods=['GET','POST'])
@bp.route('/trees/nodeuserform/<node_id>/<nodeuser_id>',methods=['GET','POST'])
@authorized(object_type='tree',require_admin=True)
async def nodeuserform(request, node_id=None, nodeuser_id=None):
    nodeuser = None
    if nodeuser_id:
        nodeuser = dbsession.query(TreeNodeUser).get(nodeuser_id)
    else:
        nodeuser = TreeNodeUser()
    curnode = dbsession.query(TreeNode).get(node_id)
    parentnode = curnode.parent
    if request.method=='POST':
        form = TreeNodeUserForm(request.form)
        treenode = dbsession.query(TreeNode).get(request.form.get('id'))
        nodeuser.node = treenode
        nodeuser.user_id = int(request.form.get('user'))
        nodeuser.role = request.form.get('role')
        dbsession.add(nodeuser)
        try:
            dbsession.commit()
        except BaseException as exp:
            dbsession.rollback()
        return jsonresponse([{ 'id':treenode.id , 'title':treenode.title }])
    else:
        form = TreeNodeUserForm(obj=nodeuser)

    return html(render(request,'trees/nodeform.html',node=curnode,form=form,parentnode=parentnode,nodeuser=nodeuser))

@bp.route('/trees/addnode')
@bp.route('/trees/addnode/<parent_id>',methods=['GET','POST'])
@authorized(object_type='tree',require_admin=True)
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
@authorized(object_type='tree',require_admin=True)
async def renamenode(request, node_id=None):
    if node_id:
        nnode = dbsession.query(TreeNode).get(node_id)
        if request.method=='POST' and request.form:
            nnode.title = request.form.get('title')
            dbsession.add(nnode)
            dbsession.commit()
    return jsonresponse([{ 'id':nnode.id if nnode else False }])

@bp.route('/trees/pastenode')
@bp.route('/trees/pastenode/<node_id>/<paste_mode>',methods=['POST'])
@authorized(object_type='tree',require_admin=True)
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
@authorized(object_type='tree',require_admin=True)
async def deletenode(request, node_id):
    nnode = dbsession.query(TreeNode).get(node_id)
    if request.method=='POST':
        dbsession.delete(nnode)
        dbsession.commit()
    return jsonresponse([{ 'status':'done' }])

@bp.route('/trees/create',methods=['POST','GET'],name='create')
@bp.route('/trees/edit/',methods=['POST','GET'],name='edit')
@bp.route('/trees/edit/<id>',methods=['POST','GET'])
@authorized(object_type='tree',require_admin=True)
async def form(request,id=None):
    title = 'Create Tree'
    form = TreeForm(request.form)
    tree=None
    if id:
        tree = dbsession.query(Tree).get(int(id))
        title = 'Edit Tree'
    if request.method=='POST' and form.validate():
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
        if tree:
            form = TreeForm(obj=tree)

    return html(render(request,'generic/form.html',title=title,tree=tree, form=form,enctype='multipart/form-data'))

@bp.route('/trees')
@authorized(object_type='tree',require_admin=True)
async def index(request):
    trees = dbsession.query(Tree)
    paginator = Paginator(trees, 5)
    return html(render(request,
        'trees/list.html',title='Trees',editlink='trees.edit',addlink='trees.create',fields=[{'label':'Module','name':'module'},{'label':'Title','name':'title'},{'label':'Slug','name':'slug'}],paginator=paginator,curpage=paginator.page(int(request.args['tree'][0]) if 'tree' in request.args else 1)))
