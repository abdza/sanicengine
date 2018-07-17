# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect, json as jsonresponse
from .models import Tree, TreeNode, TreeNodeUser
from .forms import TreeForm, TreeNodeForm, TreeNodeUserForm
from sanicengine.database import dbsession
from sanicengine.template import render
from sanicengine.decorators import authorized
from sqlalchemy_paginator import Paginator
from sqlalchemy.exc import IntegrityError

bp = Blueprint('trees')

@bp.route('/trees/view/<slug>',methods=['GET','POST'])
@authorized(object_type='tree')
async def view(request, slug):
    tree = dbsession.query(Tree).filter_by(slug=slug).first()
    if tree:
        if not tree.rootnode:
            tree.create_rootnode()
            try:
                dbsession.commit()
            except Exception as inst:
                dbsession.rollback()
        return html(render(request,'trees/view.html',tree=tree))
    else:
        request['session']['flashmessage'] = 'No tree to view'
        return redirect('/')

@bp.route('/trees/nodeview/<node_id>')
@bp.route('/trees/nodeview/',name='treenodeview')
@authorized(object_type='tree',require_admin=True)
async def nodeview(request,node_id=None):
    node = None
    if node_id and not node_id=='null':
        node = dbsession.query(TreeNode).get(node_id)
    return html(render(request,'trees/nodeview.html',node=node))

@bp.route('/trees/nodejson/<module>/<slug>/<node_id>',methods=['GET'])
@bp.route('/trees/nodejson/<module>/<slug>',methods=['GET'],name='treenodejson')
@authorized(object_type='tree',require_admin=True)
async def nodejson(request, module, slug, node_id=None):
    tree = dbsession.query(Tree).filter_by(module=module,slug=slug).first()
    if node_id:
        curnode = dbsession.query(TreeNode).get(node_id)
        return jsonresponse([ { 'text': cnode.title, 'state':{ 'opened':False }, 'children':True if cnode.children else False, 'data':{ 'dbid':cnode.id } } for cnode in curnode.children ])
    else:
        return jsonresponse([{ 'text':tree.rootnode.title , 'state':{ 'opened':False }, 'children':True, 'data':{ 'dbid':tree.rootnode.id } }])

@bp.route('/trees/editnode/<node_id>',methods=['GET','POST'])
@bp.route('/trees/editnode',name='treeeditnode')
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

@bp.route('/trees/deletenodeuser/<node_id>/<nodeuser_id>',methods=['GET','POST'])
@bp.route('/trees/deletenodeuser',name='treedeletenodeuser')
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

@bp.route('/trees/nodeuserform/<node_id>/<nodeuser_id>',methods=['GET','POST'])
@bp.route('/trees/nodeuserform/<node_id>',methods=['GET','POST'],name='treenodeusernode')
@bp.route('/trees/nodeuserform',name='treenodeuserform')
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

@bp.route('/trees/addnode/<parent_id>',methods=['GET','POST'])
@bp.route('/trees/addnode',name='treeaddnode')
@authorized(object_type='tree',require_admin=True)
async def addnode(request, parent_id):
    parentnode = dbsession.query(TreeNode).get(parent_id)
    form = TreeNodeForm(request.form)
    if request.method=='POST':
        treenode = TreeNode()
        form.populate_obj(treenode)
        treenode.parent_id = int(request.form.get('parent_id'))
        treenode.sanictree = parentnode.sanictree
        dbsession.add(treenode)
        try:
            dbsession.commit()
        except BaseException as exp:
            dbsession.rollback()
        return jsonresponse([{ 'id':treenode.id , 'title':treenode.title }])
    return html(render(request,'trees/nodeform.html',form=form,parentnode=parentnode))

@bp.route('/trees/renamenode/<node_id>',methods=['POST'])
@bp.route('/trees/renamenode',name='treerenamenode')
@authorized(object_type='tree',require_admin=True)
async def renamenode(request, node_id=None):
    if node_id:
        nnode = dbsession.query(TreeNode).get(node_id)
        if nnode and request.method=='POST' and request.form:
            nnode.title = request.form.get('title')
            dbsession.add(nnode)
            dbsession.commit()
    return jsonresponse([{ 'id':nnode.id if nnode else False }])

@bp.route('/trees/pastenode/<node_id>/<paste_mode>',methods=['POST'])
@bp.route('/trees/pastenode',name='treepastenode')
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

@bp.route('/trees/deletenode/<node_id>',methods=['POST'])
@bp.route('/trees/deletenode',name='treedeletenode')
@authorized(object_type='tree',require_admin=True)
async def deletenode(request, node_id):
    nnode = dbsession.query(TreeNode).get(node_id)
    if request.method=='POST':
        dbsession.delete(nnode)
        dbsession.commit()
    return jsonresponse([{ 'status':'done' }])

@bp.route('/trees/delete/<id>',methods=['POST'])
@authorized(object_type='tree',require_admin=True)
async def delete(request,id):
    if id==1:
        request['session']['flashmessage'] = 'Cannot delete the first tree. That is a system critical tree'
        return redirect(request.app.url_for('trees.index'))
    tree = dbsession.query(Tree).get(int(id))
    if tree:
        if tree.rootnode:
            dbsession.delete(tree.rootnode)
        dbsession.delete(tree)
        try:
            dbsession.commit()
        except Exception as inst:
            dbsession.rollback()
    return redirect(request.app.url_for('trees.index'))

@bp.route('/trees/edit/<id>',methods=['POST','GET'])
@bp.route('/trees/edit/',methods=['POST','GET'],name='edit')
@bp.route('/trees/create',methods=['POST','GET'],name='create')
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
        newtree = False
        if not tree:
            tree=Tree()
            newtree = True
        form.populate_obj(tree)
        dbsession.add(tree)
        success = False
        try:
            dbsession.commit()
            success = True
        except IntegrityError as inst:
            form.slug.errors.append('Tree with slug ' + form.slug.data + ' already exist in module ' + form.module.data + '. It needs to be unique')
            dbsession.rollback()
        except Exception as inst:
            dbsession.rollback()
        if success and newtree:
            tree.create_rootnode()
            try:
                dbsession.commit()
            except Exception as inst:
                dbsession.rollback()
        if success:
            if request.form['submit'][0]=='Submit':
                return redirect('/trees')
            else:
                return redirect('/trees/edit/' + tree.slug)
    else:
        if tree:
            form = TreeForm(obj=tree)

    return html(render(request,'generic/form.html',title=title,tree=tree, form=form,enctype='multipart/form-data',acefield=['datastr'],acetype={'datastr':'json'}))

@bp.route('/trees')
@authorized(object_type='tree',require_admin=True)
async def index(request):
    trees = dbsession.query(Tree)
    paginator = Paginator(trees, 50)
    return html(render(request,
        'trees/list.html',title='Trees',deletelink='trees.delete',editlink='trees.edit',addlink='trees.create',fields=[{'label':'Module','name':'module'},{'label':'Slug','name':'slug'},{'label':'Title','name':'title'}],paginator=paginator,curpage=paginator.page(int(request.args['tree'][0]) if 'tree' in request.args else 1)))
