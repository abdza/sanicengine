from wtforms import Form, StringField, TextAreaField, BooleanField, DateField, FileField

class FileLinkForm(Form):
    title = StringField('Title')
    slug = StringField('Slug')
    module = StringField('Module')
    filename = FileField('File')
    require_login = BooleanField('Require Login')
    allowed_roles = StringField('Allowed Roles')
