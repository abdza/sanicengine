# -*- coding: utf-8 -*-
"""User models."""
import datetime

from database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date, UniqueConstraint
from template import render_string

class Page(ModelBase):
    __tablename__ = 'pages'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100))
    module = Column(String(100),default='pages')
    content = Column(Text())
    published = Column(Boolean(),default=False)
    runable = Column(Boolean(),default=False)
    require_login = Column(Boolean(),default=False)
    allowed_roles = Column(String(300))
    publish_date = Column(Date(),nullable=True)
    expire_date = Column(Date(),nullable=True)

    __table_args__ = (
        UniqueConstraint(module, slug, name='page_module_slug_uidx'),
    )

    def __str__(self):
        return 'Page:' + self.title

    def render(self,request,*args,**kwargs):
        return render_string(request,self.content,*args,**kwargs)

    @property
    def is_published(self):
        if not self.published:
            return False
        else:
            toret = True
            curdate = datetime.date.today()
            if self.publish_date and self.publish_date>curdate:
                toret = False
            if self.expire_date and self.expire_date<curdate:
                toret = False
            return toret
