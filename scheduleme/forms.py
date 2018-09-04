# -*- coding: UTF-8 -*-
from flask_wtf import Form
from wtforms import TextField
from wtforms.validators import DataRequired, Email

class frmRegistration(Form):
    username = TextField(u'דואר אלקטרוני',
                         validators=[DataRequired(), Email([u'בשדה זה יש להקליד כתובת אימייל תקינה', 'has-error'])])
    # recaptcha = RecaptchaField()
    plname = TextField(u'שם פרטי ושם משפחה', validators=[DataRequired(u'יש להקליד שם')])
