# This Python file uses the following encoding: utf-8
from json import dumps
from datetime import timedelta as td
from datetime import datetime as dt
import random
import string
import logging
import requests
import os

from flask import Flask, Markup, request, redirect, url_for, session, escape, render_template, abort, \
    send_from_directory, jsonify
from flask_mongokit import MongoKit
from flask_wtf import Form
from flask_cors import CORS

from wtforms import TextField
from wtforms.validators import DataRequired, Email
from bson.objectid import ObjectId
from bson.json_util import dumps as bdumps

from logentries import LogentriesHandler
from premailer import transform

###### configuration
try:
    LOCAL = os.getenv('C9_HOSTNAME')=="scheduleme-ngetter.c9users.io"# Make true if running from the IDE
    MONGO_LOCAL = LOCAL and True # Make true if running from the IDE and the mongod is running too on the local machine
    RETURN_TO = os.getenv('IP')
except Exception:
    LOCAL = False
    MONGO_LOCAL = False
    RETURN_TO = r'http://opsign.herokuapp.com'

if MONGO_LOCAL:
    MONGODB_HOST = os.getenv('IP')
    MONGODB_PORT = 27017
    MONGODB_DATABASE = 'test'
else:

    MONGODB_HOST = 'ds127928.mlab.com'
    MONGODB_PORT = 27928
    MONGODB_DATABASE = 'operations'
    MONGODB_USERNAME = 'nir'
    MONGODB_PASSWORD = '123456'

TOR_SIZE = 64

############# configuration

app = Flask(__name__)
app.config.from_object(__name__)
CORS(app)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

mdb = MongoKit(app)

logen = logging.getLogger('logentries')
logen.setLevel(logging.INFO)
# Note if you have set up the logentries handler in Django, the following line is not necessary
logen.addHandler(LogentriesHandler('5ac1a243-662a-4f2c-910d-a57da29e38f4'))


class frmRegistration(Form):
    username = TextField(u'דואר אלקטרוני',
                         validators=[DataRequired(), Email([u'בשדה זה יש להקליד כתובת אימייל תקינה', 'has-error'])])
    # recaptcha = RecaptchaField()
    plname = TextField(u'שם פרטי ושם משפחה', validators=[DataRequired(u'יש להקליד שם')])

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
