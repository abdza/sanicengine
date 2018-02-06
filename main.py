from sanic import Sanic
from sanic.response import json, html
import users, pages, fileLinks
from template import render
from database import dbsession, ModelBase, dbengine

app = Sanic()
app.static('/static','./static')

@app.listener('before_server_start')
async def setup_db(app, loop):
    ModelBase.metadata.create_all(dbengine)

@app.listener('before_server_start')
async def register_bp(app, loop):
    app.blueprint(users.views.bp)
    app.blueprint(pages.views.bp)
    app.blueprint(fileLinks.views.bp)

@app.route("/",methods=['GET','POST'])
async def test(request):
    form = users.forms.UserForm(request.form)
    print(request.method)
    if request.method=='POST' and form.validate():
        user=users.models.User()
        form.populate_obj(user)
        dbsession.add(user)
        dbsession.commit()
    return html(render(request,'test.html',name='hi',form=form))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
