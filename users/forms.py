from wtforms import Form, StringField, PasswordField
from wtforms.fields.html5 import EmailField

class UserForm(Form):
    name = StringField('Name')
    username = StringField('User Name')
    password = PasswordField('Password')
    email = EmailField('Email')

class ModuleRoleForm(Form):
    user = StringField('User')
    role = StringField('Role')
    module = StringField('Module')
