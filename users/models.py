from database import ModelBase, dbsession, reference_col
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship, backref

class User(ModelBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    username = Column(String(50))
    password = Column(String(300))
    email = Column(String(300))
    resethash = Column(String(300))
    resetexpire = Column(DateTime)
    superuser = Column(Boolean(),default=False)

    def getuser(self, userid):
        return dbsession.query(User).get(userid)

    def moduleroles(self,module):
        mroles = dbsession.query(ModuleRole).filter(ModuleRole.user==self,ModuleRole.module==module).all()
        return [ r.role for r in mroles ]

class ModuleRole(ModelBase):
    __tablename__ = 'module_roles'
    id = Column(Integer, primary_key=True)

    user_id = reference_col('users')
    user = relationship('User',backref='roles')

    role = Column(String(100))
    module = Column(String(200))

    def __str__(self):
        return str(self.user) + '-' + str(self.module) + '-' + str(self.role)
