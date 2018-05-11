from wtforms import Form, StringField, TextAreaField, BooleanField, DateField

class TreeForm(Form):
    title = StringField('Title')
    slug = StringField('Slug')
    module = StringField('Module')
    published = BooleanField('Published')
    require_login = BooleanField('Require Login')
    allowed_roles = StringField('Allowed Roles')
    publish_date = DateField('Publish Date')
    expire_date = DateField('Expire Date')

class TreeNodeForm(Form):
    title = StringField('Title')
    slug = StringField('Slug')
    node_category = StringField('Category')
    node_type = StringField('Type')
    published = BooleanField('Published')
    require_login = BooleanField('Require Login')
    allowed_roles = StringField('Allowed Roles')
    publish_date = DateField('Publish Date')
    expire_date = DateField('Expire Date')

class TreeNodeUserForm(Form):
    user = StringField('User')
    role = StringField('Role')
