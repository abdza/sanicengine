# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from database import ModelBase, dbsession, reference_col
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy_mptt.mixins import BaseNestedSets
from template import render_string
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
        newnode = TreeNode(
                parent=parentnode,
                sanictree=tree,
                title=readarray(nodearray,'title'),
                module=readarray(nodearray,'module'),
                slug=readarray(nodearray,'slug'),
                require_login=readarray(nodearray,'require_login',False),
                allowed_roles=readarray(nodearray,'allowed_roles'),
                published=readarray(nodearray,'published',False),
                publish_date=readarray(nodearray,'publish_date',None),
                expire_date=readarray(nodearray,'expire_date',None),
                node_category=readarray(nodearray,'node_category'),
                node_type=readarray(nodearray,'node_type'),
                datastr=readarray(nodearray,'datastr')
                )
        dbsession.add(newnode)
        from users.models import User
        for cuser in nodearray['users']:
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
