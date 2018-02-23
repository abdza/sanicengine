from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, Column, ForeignKey

ModelBase = declarative_base()
dbengine = create_engine('postgresql://sanic:sanic123@localhost/sanictest')
dbsessionmaker = sessionmaker(bind=dbengine)
dbsession = dbsessionmaker()

def reference_col(tablename, nullable=False, pk_name='id', **kwargs):
    """Column that adds primary key foreign key reference.

    Usage: ::

        category_id = reference_col('category')
        category = relationship('Category', backref='categories')
    """
    return Column(
        ForeignKey('{0}.{1}'.format(tablename, pk_name)),
        nullable=nullable, **kwargs)
