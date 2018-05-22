from wtforms import Form, StringField, TextAreaField, BooleanField, DateField, FileField

class FileLinkForm(Form):
    module = StringField('Module')
    slug = StringField('Slug')
    title = StringField('Title')
    filename = FileField('File')
    require_login = BooleanField('Require Login')
    allowed_roles = StringField('Allowed Roles')
