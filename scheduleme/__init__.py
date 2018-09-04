# This Python file uses the following encoding: utf-8
import os
import logging

from flask import Flask, Markup
from flask_mongokit import MongoKit
from flask_cors import CORS

from logentries import LogentriesHandler
from premailer import transform

from scheduleme.config import *

# initializations
app = Flask(__name__)
app.config.from_object('scheduleme.config')
CORS(app)

app.secret_key = os.getenv('APP_SECRET_KEY')

mdb = MongoKit(app)

# initiate logging to logentries
logen = logging.getLogger('logentries')
logen.setLevel(logging.INFO)
logen.addHandler(LogentriesHandler(os.getenv('LOGENTRIES_KEY')))


import scheduleme.forms
import scheduleme.views
import scheduleme.route_api


@app.template_filter('emptysign')
def emptysign(value, text=''):
    if value:
        return value
    elif text != '':
        return Markup("<span>%s</span>" % text)
    else:
        return Markup("<i class='fa fa-exclamation-triangle'></i>")


@app.template_filter('typesign')
def typesign(value):
    if value == 'חניך':
        return value
    elif value == 'סוליסט':
        return value
    else:
        return value


@app.template_filter('mytor')
def mytor(value, position):
    if value:
        if position >= int(value):
            return position - int(value) + 1
        else:
            return TOR_SIZE - int(value) + position + 1
    else:
        return Markup("<i class='fa fa-exclamation-triangle'></i>")
