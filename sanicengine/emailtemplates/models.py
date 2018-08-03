# -*- coding: utf-8 -*-
"""User models."""
import datetime

from sanicengine.database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date, UniqueConstraint
from sanicengine.template import render_string

class EmailTemplate(ModelBase):
    __tablename__ = 'emailtemplates'
    id = Column(Integer, primary_key=True)
    module = Column(String(100),default='portal')
    title = Column(String(200))
    sendto = Column(Text())
    sendcc = Column(Text())
    content = Column(Text())

    def __str__(self):
        return 'Email:' + self.title

    def rendercontent(self,request,*args,**kwargs):
        return render_string(request,self.content,*args,**kwargs)

    def renderto(self,request,*args,**kwargs):
        return render_string(request,self.sendto,*args,**kwargs)

    def rendercc(self,request,*args,**kwargs):
        return render_string(request,self.sendcc,*args,**kwargs)
