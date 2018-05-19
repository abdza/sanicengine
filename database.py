from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, Column, ForeignKey
try:
    import settings
except ImportError:
    print("Error importing settings. Please copy settings.sample.py to settings.py and modify the content for your use")
    exit()

ModelBase = declarative_base()
dbengine = create_engine('postgresql://' + settings.DATABASE_USERNAME + ':' + settings.DATABASE_PASSWORD + '@localhost/' + settings.DATABASE_NAME)
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
