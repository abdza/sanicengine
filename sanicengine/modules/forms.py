from wtforms import Form, StringField, TextAreaField, BooleanField, DateField

class ModuleForm(Form):
    title = StringField('Title')
