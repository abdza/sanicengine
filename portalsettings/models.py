# -*- coding: utf-8 -*-
"""User models."""
import datetime

from database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Float, Date, UniqueConstraint
import json

class Setting(ModelBase):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    module = Column(String(100),default='portal')
    name = Column(String(200))
    setting_type = Column(String(10))
    txtdata = Column(Text(),nullable=True)
    intdata = Column(Integer(),nullable=True)
    floatdata = Column(Float(),nullable=True)
    datedata = Column(Date(),nullable=True)

    __table_args__ = (
        UniqueConstraint(module, name, name='setting_module_name_uidx'),
    )

    def __str__(self):
        return 'Setting:' + self.name

    @property
    def value(self):
        if self.setting_type == 'text':
            return self.txtdata
        elif self.setting_type == 'json':
            return json.loads(self.txtdata)
        elif self.setting_type == 'integer':
            return self.intdata
        elif self.setting_type == 'float':
            return self.floatdata
        elif self.setting_type == 'date':
            return self.datedata

    def namedefault(module,name,default):
        dsetting = dbsession.query(Setting).filter_by(module=module,name=name).first()
        if dsetting:
            return dsetting.value
        else:
            return default
