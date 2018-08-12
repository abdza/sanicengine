from wtforms import Form, StringField, TextAreaField, BooleanField, DateField
from wtforms.validators import Optional

class EmailTemplateForm(Form):
    module = StringField('Module')
    title = StringField('Title')
    emailtitle = TextAreaField('Title Template')
    sendto = TextAreaField('Send To')
    sendcc = TextAreaField('Send Cc')
    content = TextAreaField('Content')
