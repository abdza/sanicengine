from jinja2 import Template, Environment, FileSystemLoader

jinja_env = Environment(loader=FileSystemLoader('templates'))

def render(request, template_file, *args, **kwargs):
    return jinja_env.get_template(template_file).render(app=request.app,request=request,*args,**kwargs)

def render_string(request, template_string, *args, **kwargs):
    return jinja_env.from_string(template_string).render(app=request.app,request=request,*args,**kwargs)
