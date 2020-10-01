from wtforms import Form, StringField, TextAreaField, BooleanField, DateField
from wtforms.validators import Optional

class PageForm(Form):
    module = StringField('Module')
    slug = StringField('Slug')
    title = StringField('Title')
    content = TextAreaField('Content')
    runable = BooleanField('Runable')
    script = BooleanField('Script')
    require_login = BooleanField('Require Login')
    published = BooleanField('Published')
    allowed_roles = StringField('Allowed Roles')
    publish_date = DateField('Publish Date',validators=(Optional(),))
    expire_date = DateField('Expire Date',validators=(Optional(),))
