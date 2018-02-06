from wtforms import Form, StringField, TextAreaField, BooleanField, DateField, FileField

class FileLinkForm(Form):
    title = StringField('Title')
    slug = StringField('Slug')
    module = StringField('Module')
    filename = FileField('File')
