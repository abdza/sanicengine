# -*- coding: utf-8 -*-
"""User models."""
import datetime

from sanicengine.database import ModelBase, dbsession, reference_col
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship, backref
from sanicengine.template import render_string

class EmailTemplate(ModelBase):
    __tablename__ = 'emailtemplates'
    id = Column(Integer, primary_key=True)
    module = Column(String(100),default='portal')
    title = Column(String(200))
    emailtitle = Column(Text())
    sendto = Column(Text())
    sendcc = Column(Text())
    content = Column(Text())

    __table_args__ = (
        UniqueConstraint(module, title, name='emailtemplate_module_title_uidx'),
    )

    def __str__(self):
        return 'Email:' + self.title

    def rendertitle(self,request,*args,**kwargs):
        return render_string(request,self.emailtitle,*args,**kwargs)

    def rendercontent(self,request,*args,**kwargs):
        return render_string(request,self.content,*args,**kwargs)

    def renderto(self,request,*args,**kwargs):
        return render_string(request,self.sendto,*args,**kwargs)

    def rendercc(self,request,*args,**kwargs):
        return render_string(request,self.sendcc,*args,**kwargs)

    def renderemail(self,request,*args,**kwargs):
        scheduled_date = datetime.datetime.today()
        if 'scheduled_date' in kwargs:
            scheduled_date = kwargs['scheduled_date']

        email = EmailTrail(module=self.module,created_date=datetime.datetime.today(),status='New',scheduled_date=scheduled_date,template=self)
        email.title = self.rendertitle(request,*args,**kwargs)
        email.sendto = self.renderto(request,*args,**kwargs)
        email.sendcc = self.rendercc(request,*args,**kwargs)
        email.content = self.rendercontent(request,*args,**kwargs)
        dbsession.add(email)
        dbsession.commit()

class EmailTrail(ModelBase):
    __tablename__ = 'emailtrail'
    id = Column(Integer, primary_key=True)
    module = Column(String(100),default='portal')
    title = Column(String(200))
    sendto = Column(Text())
    sendcc = Column(Text())
    content = Column(Text())
    created_date = Column(DateTime(),nullable=True)
    scheduled_date = Column(DateTime(),nullable=True)
    status = Column(String(20))

    template_id = reference_col('emailtemplates')
    template = relationship('EmailTemplate',backref='trails')
