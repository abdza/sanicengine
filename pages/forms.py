from wtforms import Form, StringField, TextAreaField, BooleanField, DateField
from wtforms.validators import Optional

class PageForm(Form):
    module = StringField('Module')
    slug = StringField('Slug')
    title = StringField('Title')
    content = TextAreaField('Content')
    published = BooleanField('Published')
    runable = BooleanField('Runable')
    require_login = BooleanField('Require Login')
    allowed_roles = StringField('Allowed Roles')
    publish_date = DateField('Publish Date',validators=(Optional(),))
    expire_date = DateField('Expire Date',validators=(Optional(),))
