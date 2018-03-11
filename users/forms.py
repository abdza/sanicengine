from wtforms import Form, StringField, PasswordField

class UserForm(Form):
    name = StringField('Name')
    username = StringField('User Name')
    password = PasswordField('Password')

class ModuleRoleForm(Form):
    user = StringField('User')
    role = StringField('Role')
    module = StringField('Module')
