from wtforms import Form, StringField, TextAreaField, BooleanField, DateField, DecimalField, IntegerField, SelectField
from wtforms.validators import Optional

class SettingForm(Form):
    module = StringField('Module')
    name = StringField('Name')
    setting_type = SelectField('Type',choices=[('text','Text'),('json','JSON'),('integer','Integer'),('float','Float'),('date','Date')])
    txtdata = TextAreaField('Text',validators=(Optional(),))
    intdata = IntegerField('Integer',validators=(Optional(),))
    floatdata = DecimalField('Float',validators=(Optional(),))
    datedata = DateField('Date',validators=(Optional(),))
