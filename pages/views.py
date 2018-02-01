# -*- coding: utf-8 -*-
from sanic import Blueprint
from sanic.response import html, redirect
from .models import Page
from database import dbsession

bp = Blueprint('pages')

@bp.route('/view/<slug>')
def view(request, slug):
    page = dbsession.query(Page).filter_by(slug=slug).first()
    if page:
        return html(page.render())
    else:
        print("No page to view")
        return redirect('/')
