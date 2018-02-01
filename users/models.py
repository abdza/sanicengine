from database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String

class User(ModelBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    username = Column(String(50))
    password = Column(String(100))
