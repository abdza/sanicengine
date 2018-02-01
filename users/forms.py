from wtforms import Form, StringField

class UserForm(Form):
    name = StringField('Name')
    username = StringField('User Name')
    password = StringField('Password')
