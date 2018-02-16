from wtforms import Form, StringField, PasswordField

class UserForm(Form):
    name = StringField('Name')
    username = StringField('User Name')
    password = PasswordField('Password')
