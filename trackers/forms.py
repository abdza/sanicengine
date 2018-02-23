from wtforms import Form, StringField, TextAreaField, BooleanField, DateField, SelectField

class TrackerForm(Form):
    title = StringField('Title')
    slug = StringField('Slug')
    module = StringField('Module')

class TrackerFieldForm(Form):
    name = StringField('Name')
    label = StringField('Label')
    field_type = SelectField('Type',choices=[('string','String'),('text','Text'),('integer','Integer'),('number','Number'),('date','Date'),('datetime','Date Time'),('boolean','Boolean')])

class TrackerRoleForm(Form):
    name = StringField('Name')
    role_type = SelectField('Type',choices=[('module','Module'),('query','Query')])
    compare = TextAreaField('Compare')

class TrackerStatusForm(Form):
    name = StringField('Name')
    display_fields = TextAreaField('Display Fields')

class TrackerTransitionForm(Form):
    name = StringField('Name')
    display_fields = TextAreaField('Display Fields')
    edit_fields = TextAreaField('Edit Fields')
