from wtforms import Form, StringField, TextAreaField, BooleanField, DateField

class PageForm(Form):
    title = StringField('Title')
    slug = StringField('Slug')
    module = StringField('Module')
    content = TextAreaField('Content')
    published = BooleanField('Published')
    require_login = BooleanField('Require Login')
    publish_date = DateField('Publish Date')
    expire_date = DateField('Expire Date')
