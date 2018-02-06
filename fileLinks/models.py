from database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date

class FileLink(ModelBase):
    __tablename__ = 'file_links'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100),unique=True)
    module = Column(String(100),default='pages')
    filename = Column(String(200))
