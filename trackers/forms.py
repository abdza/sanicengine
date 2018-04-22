from wtforms import Form, StringField, TextAreaField, BooleanField, DateField, SelectField, IntegerField
from .models import TrackerStatus

class TrackerForm(Form):
    title = StringField('Title')
    slug = StringField('Slug')
    module = StringField('Module')
    pagelimit = IntegerField('Page Limit')
    list_fields = StringField('List Fields')
    search_fields = StringField('Search Fields')
    filter_fields = StringField('Filter Fields')

class TrackerFieldForm(Form):
    name = StringField('Name')
    label = StringField('Label')
    field_type = SelectField('Type',choices=[('string','String'),('text','Text'),('integer','Integer'),('number','Number'),('date','Date'),('datetime','Date Time'),('boolean','Boolean'),('object','Object'),('user','User')])
    obj_table = StringField('Object Table')
    obj_field = StringField('Object Field')
    default = TextAreaField('Default')

class TrackerRoleForm(Form):
    name = StringField('Name')
    role_type = SelectField('Type',choices=[('module','Module'),('query','Query')])
    compare = TextAreaField('Compare')

class TrackerStatusForm(Form):
    name = StringField('Name')
    display_fields = StringField('Display Fields')

class TrackerTransitionForm(Form):
    name = StringField('Name')
    roles = StringField('Roles')
    display_fields = StringField('Display Fields')
    edit_fields = StringField('Edit Fields')
    prev_status_id = SelectField('Prev Status')
    next_status_id = SelectField('Next Status')
    postpage = TextAreaField('Post Page Url')
