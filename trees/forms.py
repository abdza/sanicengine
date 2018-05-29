from wtforms import Form, StringField, TextAreaField, BooleanField, DateField
from wtforms.validators import Optional

class TreeForm(Form):
    module = StringField('Module')
    slug = StringField('Slug')
    title = StringField('Title')
    published = BooleanField('Published')
    require_login = BooleanField('Require Login')
    allowed_roles = StringField('Allowed Roles')
    publish_date = DateField('Publish Date',validators=(Optional(),))
    expire_date = DateField('Expire Date',validators=(Optional(),))

class TreeNodeForm(Form):
    title = StringField('Title')
    module = StringField('Module')
    slug = StringField('Slug')
    node_type = StringField('Type')
    node_category = StringField('Category')
    datastr = TextAreaField('Data')
    published = BooleanField('Published')
    require_login = BooleanField('Require Login')
    allowed_roles = StringField('Allowed Roles')
    publish_date = DateField('Publish Date',validators=(Optional(),))
    expire_date = DateField('Expire Date',validators=(Optional(),))

class TreeNodeUserForm(Form):
    user = StringField('User')
    role = StringField('Role')
