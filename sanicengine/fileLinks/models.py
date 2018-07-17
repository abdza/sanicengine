import datetime
from sanicengine.database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date, UniqueConstraint

class FileLink(ModelBase):
    __tablename__ = 'file_links'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100))
    module = Column(String(100),default='pages')
    published = Column(Boolean(),default=False)
    filename = Column(String(200))
    filepath = Column(String(200))
    require_login = Column(Boolean(),default=False)
    allowed_roles = Column(String(300))
    publish_date = Column(Date(),nullable=True)
    expire_date = Column(Date(),nullable=True)

    __table_args__ = (
        UniqueConstraint(module, slug, name='file_module_slug_uidx'),
    )

    def __str__(self):
        return 'File: ' + self.title

    @property
    def is_published(self):
        if not self.published:
            return False
        else:
            toret = True
            curdate = datetime.date.today()
            if self.publish_date and self.publish_date>curdate:
                toret = False
            if self.expire_date and self.expire_date<curdate:
                toret = False
            return toret
