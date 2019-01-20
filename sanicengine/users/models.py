from sanicengine.database import ModelBase, dbsession, reference_col
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship, backref
import hashlib

class User(ModelBase):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    username = Column(String(50))
    password = Column(String(300))
    avatar = Column(String(300))
    email = Column(String(300))
    resethash = Column(String(300))
    resetexpire = Column(DateTime)
    superuser = Column(Boolean(),default=False)
    authhash = Column(String(300))
    authexpire = Column(DateTime)

    def __str__(self):
        return self.name

    @staticmethod
    def getuser(userid):
        return dbsession.query(User).get(userid)

    def hashpassword(self,passinput):
        return hashlib.sha224(passinput.encode('utf-8')).hexdigest()

    def moduleroles(self,module=None):
        if module:
            mroles = dbsession.query(ModuleRole).filter(ModuleRole.user==self,ModuleRole.module==module).all()
        else:
            mroles = dbsession.query(ModuleRole).filter(ModuleRole.user==self).all()
        return [ r.role for r in mroles ]

    @property
    def isadmin(self):
        if self.superuser:
            return True
        for crole in self.roles:
            if crole.role.lower()=='admin':
                return True

        for trole in self.treeroles:
            if trole.role.lower()=='admin':
                return True

class ModuleRole(ModelBase):
    __tablename__ = 'module_roles'
    id = Column(Integer, primary_key=True)

    user_id = reference_col('users')
    user = relationship('User',backref='roles')

    role = Column(String(100))
    module = Column(String(200))

    def __str__(self):
        return 'Role:' + str(self.user) + ' as ' + str(self.role) + ' in ' + str(self.module) + ' module' 
