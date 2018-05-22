from database import ModelBase, dbsession
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean, Date, UniqueConstraint

class FileLink(ModelBase):
    __tablename__ = 'file_links'
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    slug = Column(String(100),unique=True)
    module = Column(String(100),default='pages')
    filename = Column(String(200))
    filepath = Column(String(200))
    require_login = Column(Boolean(),default=False)
    allowed_roles = Column(String(300))

    __table_args__ = (
        UniqueConstraint(module, slug, name='file_module_slug_uidx'),
    )

    def __str__(self):
        return 'File: ' + self.title
