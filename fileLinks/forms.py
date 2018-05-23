from wtforms import Form, StringField, TextAreaField, BooleanField, DateField, FileField
from wtforms.validators import Optional

class FileLinkForm(Form):
    module = StringField('Module')
    slug = StringField('Slug')
    title = StringField('Title')
    filename = FileField('File')
    require_login = BooleanField('Require Login')
    published = BooleanField('Published')
    allowed_roles = StringField('Allowed Roles')
    publish_date = DateField('Publish Date',validators=(Optional(),))
    expire_date = DateField('Expire Date',validators=(Optional(),))
