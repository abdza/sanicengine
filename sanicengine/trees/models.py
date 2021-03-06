# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from sanicengine.database import ModelBase, dbsession, reference_col
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy_mptt.mixins import BaseNestedSets
from sanicengine.template import render_string
import json

def readarray(arrayvar,arraykey,default=''):
    if arraykey in arrayvar:
        return arrayvar[arraykey]
    else:
        return default

class Tree(ModelBase):
    __tablename__ = 'trees'

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100))
    module = Column(String(100),default='pages')
    datastr = Column(Text)
    published = Column(Boolean(),default=False)
    require_login = Column(Boolean(),default=False)
    allowed_roles = Column(String(300))
    publish_date = Column(Date(),nullable=True)
    expire_date = Column(Date(),nullable=True)

    __table_args__ = (
        UniqueConstraint(module, slug, name='tree_module_slug_uidx'),
    )

    def __str__(self):
        return 'Tree: ' + self.title

    def load(slug,module=None):
        tree = dbsession.query(Tree).filter_by(slug=slug)
        if module:
            tree = tree.filter_by(module=module)
        return tree.first()

    @property
    def data(self):
        if self.datastr:
            return json.loads(self.datastr)
        else:
            return []

    def getdata(self,key=None,default=None):
        dat = json.loads(self.datastr)
        if key:
            if key in dat:
                return dat[key]
            elif default:
                return default
            else:
                return None
        else:
            return dat

    @property
    def rootnode(self):
        return dbsession.query(TreeNode).filter(TreeNode.sanictree==self,TreeNode.parent_id==None).first()

    def create_rootnode(self):
        rootnode=TreeNode(sanictree=self)
        rootnode.title = self.title
        rootnode.module = self.module
        rootnode.slug = self.slug
        rootnode.require_login = self.require_login
        rootnode.allowed_roles = self.allowed_roles
        rootnode.published = self.published
        rootnode.publish_date = self.publish_date
        rootnode.expire_date = self.expire_date
        dbsession.add(rootnode)

    def addnodes(self, titles, node=None):
        for title in titles:
            self.addnode(title,node)

    def addnode(self, title, node=None):
        if node:
            node.addnode(title)
        else:
            if not self.rootnode:
                self.create_rootnode()
            self.rootnode.addnode(title)

    def findnode(self, q, fromnode=None):
        if not fromnode and self.rootnode:
            fromnode = self.rootnode
        qq = "%" + "%".join(q.replace(" ","")) + "%"
        if fromnode:
            sqlq = "select id,titleagg from (select nleaf.id,nleaf.lft,nleaf.rgt,string_agg(cnode.title,'/' order by cnode.lft) titleagg from tree_nodes cnode,(select id,lft,rgt,tree_id from tree_nodes where rgt<=:right and lft>=:left and sanictree_id=:tree_id) nleaf where cnode.lft<=nleaf.lft and cnode.rgt>=nleaf.rgt and cnode.tree_id=nleaf.tree_id group by nleaf.lft, nleaf.rgt, nleaf.id) combtitle where titleagg ilike :qq limit 1"
            qparam = {"right":fromnode.right,"left":fromnode.left,"tree_id":self.id,"qq":qq}
        else:
            sqlq = "select id,titleagg from (select nleaf.id,nleaf.lft,nleaf.rgt,string_agg(cnode.title,'/' order by cnode.lft) titleagg from tree_nodes cnode,(select id,lft,rgt,tree_id from tree_nodes where sanictree_id=:tree_id) nleaf where cnode.lft<=nleaf.lft and cnode.rgt>=nleaf.rgt and cnode.tree_id=nleaf.tree_id group by nleaf.lft, nleaf.rgt, nleaf.id) combtitle where titleagg ilike :qq limit 1"
            qparam = {"tree_id":self.id,"qq":qq}
        return dbsession.query(TreeNode).get(dbsession.execute(sqlq,qparam).first()['id'])

    def allnodesleaf(self, q, fromnode=None):
        if not fromnode and self.rootnode:
            fromnode = self.rootnode
        qq = "%" + "%".join(q.replace(" ","")) + "%"
        if fromnode:
            sqlq = "select id,titleagg from (select nleaf.id,nleaf.lft,nleaf.rgt,string_agg(cnode.title,'/' order by cnode.lft) titleagg from tree_nodes cnode,(select id,lft,rgt,tree_id from tree_nodes where rgt-lft=1 and sanictree_id=:tree_id and lft>=:left and rgt<=:right) nleaf where cnode.lft<=nleaf.lft and cnode.rgt>=nleaf.rgt and cnode.tree_id=nleaf.tree_id group by nleaf.lft, nleaf.rgt, nleaf.id) combtitle where titleagg ilike :qq"
            qparam = {"right":fromnode.right,"left":fromnode.left,"tree_id":self.id,"qq":qq}
        else:
            sqlq = "select id,titleagg from (select nleaf.id,nleaf.lft,nleaf.rgt,string_agg(cnode.title,'/' order by cnode.lft) titleagg from tree_nodes cnode,(select id,lft,rgt,tree_id from tree_nodes where rgt-lft=1 and sanictree_id=:tree_id) nleaf where cnode.lft<=nleaf.lft and cnode.rgt>=nleaf.rgt and cnode.tree_id=nleaf.tree_id group by nleaf.lft, nleaf.rgt, nleaf.id) combtitle where titleagg ilike :qq"
            qparam = {"tree_id":self.id,"qq":qq}
        return [ dbsession.query(TreeNode).get(result['id']) for result in dbsession.execute(sqlq,qparam) ]

    def allnodes(self, q, fromnode=None):
        if not fromnode and self.rootnode:
            fromnode = self.rootnode
        qq = "%" + "%".join(q.replace(" ","")) + "%"
        if fromnode:
            sqlq = "select id,titleagg from (select nleaf.id,nleaf.lft,nleaf.rgt,string_agg(cnode.title,'/' order by cnode.lft) titleagg from tree_nodes cnode,(select id,lft,rgt,tree_id from tree_nodes where rgt<=:right and lft>=:left and sanictree_id=:tree_id) nleaf where cnode.lft<=nleaf.lft and cnode.rgt>=nleaf.rgt and cnode.tree_id=nleaf.tree_id group by nleaf.lft, nleaf.rgt, nleaf.id) combtitle where titleagg ilike :qq"
            qparam = {"right":fromnode.right,"left":fromnode.left,"tree_id":self.id,"qq":qq}
        else:
            sqlq = "select id,titleagg from (select nleaf.id,nleaf.lft,nleaf.rgt,string_agg(cnode.title,'/' order by cnode.lft) titleagg from tree_nodes cnode,(select id,lft,rgt,tree_id from tree_nodes where sanictree_id=:tree_id) nleaf where cnode.lft<=nleaf.lft and cnode.rgt>=nleaf.rgt and cnode.tree_id=nleaf.tree_id group by nleaf.lft, nleaf.rgt, nleaf.id) combtitle where titleagg ilike :qq"
            qparam = {"tree_id":self.id,"qq":qq}
        return [ dbsession.query(TreeNode).get(result['id']) for result in dbsession.execute(sqlq,qparam) ]

class TreeNode(ModelBase, BaseNestedSets):
    __tablename__ = 'tree_nodes'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    module = Column(String(100),default='portal')
    slug = Column(String(100))
    require_login = Column(Boolean(),default=False)
    allowed_roles = Column(String(300))
    published = Column(Boolean(),default=False)
    publish_date = Column(Date(),nullable=True)
    expire_date = Column(Date(),nullable=True)
    node_category = Column(String(100))
    node_type = Column(String(100))
    datastr = Column(Text)

    sanictree_id = reference_col('trees')
    sanictree = relationship('Tree',backref='nodes')

    def treedump(self):
        return { 
                'title':self.title,
                'module':self.module,
                'slug':self.slug,
                'require_login':self.require_login,
                'allowed_roles':self.allowed_roles,
                'published':self.published,
                'publish_date':self.publish_date.strftime('%Y-%m-%d') if self.publish_date else None,
                'expire_date':self.expire_date.strftime('%Y-%m-%d') if self.expire_date else None,
                'node_category':self.node_category,
                'node_type':self.node_type,
                'datastr':self.datastr,
                'sanictree':self.sanictree.slug,
                'users': [ user.treedump() for user in self.users ],
                'children':[ child.treedump() for child in self.children ] 
                }

    @staticmethod
    def treeload(tree,nodearray,parentnode=None):
        newnode = dbsession.query(TreeNode).filter_by(parent=parentnode,title=readarray(nodearray,'title')).first()
        if not newnode:
            newnode = TreeNode()

        newnode.parent=parentnode
        newnode.sanictree=tree
        newnode.title=readarray(nodearray,'title')
        newnode.module=readarray(nodearray,'module')
        newnode.slug=readarray(nodearray,'slug')
        newnode.require_login=readarray(nodearray,'require_login',False)
        newnode.allowed_roles=readarray(nodearray,'allowed_roles')
        newnode.published=readarray(nodearray,'published',False)
        newnode.publish_date=readarray(nodearray,'publish_date',None)
        newnode.expire_date=readarray(nodearray,'expire_date',None)
        newnode.node_category=readarray(nodearray,'node_category')
        newnode.node_type=readarray(nodearray,'node_type')
        newnode.datastr=readarray(nodearray,'datastr')

        dbsession.add(newnode)
        from sanicengine.users.models import User
        for cuser in nodearray['users']:
            newuser = dbsession.query(TreeNodeUser).filter_by(node=newnode,role=readarray(cuser,'role'),user=dbsession.query(User).filter_by(username=readarray(cuser,'user')).first()).first()
            if not newuser:
                newuser = TreeNodeUser(
                        node=newnode,
                        role=readarray(cuser,'role'),
                        user=dbsession.query(User).filter_by(username=readarray(cuser,'user')).first()
                        )
                dbsession.add(newuser)

        dbsession.flush()
        for cnode in nodearray['children']:
            TreeNode.treeload(tree,cnode,newnode)

    def copy(self,parent_id,appendslug):
        newcopy = TreeNode(
                title = self.title,
                slug = appendslug + "_" + self.slug,
                module = self.module,
                require_login = self.require_login,
                allowed_roles = self.allowed_roles,
                published = self.published,
                publish_date = self.publish_date,
                expire_date = self.expire_date,
                node_category = self.node_category,
                node_type = self.node_type,
                datastr = self.datastr,
                sanictree = self.sanictree,
                parent_id = parent_id)

        dbsession.add(newcopy)
        dbsession.flush()
        for child in self.children:
            child.copy(newcopy.id,appendslug)

    @property
    def data(self):
        if self.datastr:
            return json.loads(self.datastr)
        else:
            return []

    def addnodes(self, titles):
        for title in titles:
            self.addnode(title)

    def addnode(self, title):
        newchild = TreeNode(sanictree=self.sanictree,title=title,parent=self)
        dbsession.add(newchild)
        try:
            dbsession.commit()
        except BaseException as exp:
            dbsession.rollback()

    def getdata(self,key=None,default=None):
        dat = json.loads(self.datastr)
        if key:
            if key in dat:
                return dat[key]
            elif default:
                return default
            else:
                return None
        else:
            return dat

    def childquery(self):
        return dbsession.query(TreeNode).filter(TreeNode.rgt>=self.rgt,TreeNode.lft<=self.lft,TreeNode.sanictree==self.sanictree)

class TreeNodeUser(ModelBase):
    __tablename__ = 'tree_node_users'
    id = Column(Integer, primary_key=True)
    role = Column(String(100))

    node_id = reference_col('tree_nodes')
    node = relationship('TreeNode', backref='users')

    user_id = reference_col('users')
    user = relationship('User', backref='treeroles', order_by='User.name')

    __mapper_args__ = {
        "order_by":[role,]
    }

    def treedump(self):
        return { 
                'user':self.user.username,
                'role':self.role 
                }
