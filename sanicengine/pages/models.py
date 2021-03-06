# -*- coding: utf-8 -*-
"""User models."""
import traceback
import datetime
import sys
from sanic.exceptions import NotFound,ServerError

from sanicengine.database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date, UniqueConstraint
from sanicengine.template import render_string

class Page(ModelBase):
    __tablename__ = 'pages'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100))
    module = Column(String(100),default='portal')
    content = Column(Text())
    published = Column(Boolean(),default=False)
    runable = Column(Boolean(),default=False)
    script = Column(Boolean(),default=False)
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
        try:
            return render_string(request,self.content,*args,**kwargs)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type,exc_value,exc_traceback)
            raise ServerError("Something bad happened", status_code=500)

    def load(slug,module=None):
        page = dbsession.query(Page).filter_by(slug=slug)
        if module:
            page = page.filter_by(module=module)
        return page.first()

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
