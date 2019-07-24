# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from sanicengine.database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date, DateTime
from sqlalchemy.sql import func
from sanicengine.template import render_string

class Error(ModelBase):
    __tablename__ = 'errors'
    id = Column(Integer, primary_key=True)
    title = Column(String(200),unique=True)
    description = Column(Text())
    date_created = Column(DateTime(timezone=True),server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())