from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

ModelBase = declarative_base()
dbengine = create_engine('postgresql://sanic:sanic123@localhost/sanictest')
dbsessionmaker = sessionmaker(bind=dbengine)
dbsession = dbsessionmaker()
