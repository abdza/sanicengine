# -*- coding: utf-8 -*-
"""User models."""
import datetime as dt

from database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date
from template import render_string

class Module(ModelBase):
    __tablename__ = 'modules'
    id = Column(Integer, primary_key=True)
    title = Column(String(200),unique=True)
