# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from database import ModelBase, dbsession, reference_col
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date
from sqlalchemy.orm import relationship, backref
from sqlalchemy_mptt.mixins import BaseNestedSets
from template import render_string

class Tree(ModelBase):
    __tablename__ = 'trees'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100),unique=True)
    module = Column(String(100),default='pages')
    published = Column(Boolean(),default=False)
    require_login = Column(Boolean(),default=False)
    allowed_roles = Column(String(300))
    publish_date = Column(Date(),nullable=True)
    expire_date = Column(Date(),nullable=True)

    @property
    def rootnode(self):
        return dbsession.query(TreeNode).filter(TreeNode.tree==self,TreeNode.parent_id==None).first()

class TreeNode(ModelBase, BaseNestedSets):
    __tablename__ = 'tree_nodes'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100),unique=True)
    require_login = Column(Boolean(),default=False)
    allowed_roles = Column(String(300))
    published = Column(Boolean(),default=False)
    publish_date = Column(Date(),nullable=True)
    expire_date = Column(Date(),nullable=True)

    tree_id = reference_col('trees')
    tree = relationship('Tree',backref='nodes')

    def copy(self,parent_id,appendslug):
        newcopy = TreeNode(
                title = self.title,
                slug = appendslug + "_" + self.slug,
                require_login = self.require_login,
                allowed_roles = self.allowed_roles,
                published = self.published,
                publish_date = self.publish_date,
                expire_date = self.expire_date,
                tree = self.tree,
                parent_id = parent_id)

        dbsession.add(newcopy)
        dbsession.flush()
        for child in self.children:
            child.copy(newcopy.id,appendslug)
