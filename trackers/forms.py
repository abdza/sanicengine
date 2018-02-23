from wtforms import Form, StringField, TextAreaField, BooleanField, DateField, SelectField

class TrackerForm(Form):
    title = StringField('Title')
    slug = StringField('Slug')
    module = StringField('Module')

class TrackerFieldForm(Form):
    name = StringField('Name')
    label = StringField('Label')
    field_type = SelectField('Field Type',choices=[('string','String'),('text','Text'),('integer','Integer'),('number','Number'),('date','Date'),('datetime','Date Time'),('boolean','Boolean')])
