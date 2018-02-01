from jinja2 import Template, Environment, FileSystemLoader

jinja_env = Environment(loader=FileSystemLoader('templates'))

def render(template_file, *args, **kwargs):
    from main import app
    return jinja_env.get_template(template_file).render(app=app,*args,**kwargs)

def render_string(template_string, *args, **kwargs):
    from main import app
    return jinja_env.from_string(template_string).render(app=app,*args,**kwargs)
