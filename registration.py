import os
from flask import Flask, Markup,  request, redirect, url_for, session, escape, render_template, abort
from flask.ext.mongokit import MongoKit

from flask_wtf import Form,RecaptchaField
from wtforms import TextField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email

from hashlib import sha224
from json import dumps
from datetime import datetime
import requests
import random
import string
import ast

from logentries import LogentriesHandler
import logging
# configuration
# MONGODB_HOST = '127.0.0.1'
# MONGODB_PORT = 27017
# MONGODB_DATABASE = 'test'

MONGODB_HOST = 'troup.mongohq.com'
MONGODB_PORT = 10001
MONGODB_DATABASE = 'ngc-registration'
MONGODB_USERNAME = 'nirg'
MONGODB_PASSWORD  = 'dilk2d123'

RECAPTCHA_PUBLIC_KEY = "6LcWKPASAAAAAN4dF2Qf7Ojyv6vpv4FvXFoxR6SC"
RECAPTCHA_PRIVATE_KEY = "6LcWKPASAAAAAKpIVc_iPFM7T6xtyebNCplhIB5h"
RECAPTCHA_OPTIONS = {"theme":"white"}

app = Flask(__name__)
app.config.from_object(__name__)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

mdb = MongoKit(app)                        


logen = logging.getLogger('logentries')
logen.setLevel(logging.INFO)
# Note if you have set up the logentries handler in Django, the following line is not necessary
logen.addHandler(LogentriesHandler('5ac1a243-662a-4f2c-910d-a57da29e38f4'))

class frmRegistration(Form):
    username = TextField(u'דואר אלקטרוני', validators=[DataRequired(), Email([u'בשדה זה יש להקליד כתובת אימייל תקינה','has-error'])]) 
    #recaptcha = RecaptchaField()
    plname = TextField(u'שם פרטי ושם משפחה', validators=[DataRequired(u'יש להקליד שם')])
    
@app.route('/index')
@app.route('/', methods=['POST','GET'])
def index():
    if 'username' in session:
        session.permanent = True
        username = escape(session['username'])
        try:
            users = mdb['users']
            r = users.find_one({'username':username})
            logen.info('%s logged in'%username)
        except TypeError:
            return redirect(url_for('logout'))
        except Exception:
            logen.warn("abort(501)")
            abort(501)
            
        col = mdb['operations']
        l = list(col.find({'date':{'$gte':datetime.now(None)}}).sort("date",1).limit(12))
        return render_template('main.html', l=l, user=r)	
    else:
        return redirect(url_for('register'))

@app.route('/signin',methods=['POST','GET'])
def signin():
		if request.method == 'POST':
			return redirect(url_for('/'))
		else:
			return render_template('signin.html')

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))
    
@app.route('/login/<get_token>', methods=['GET'])
def token(get_token):
    if request.method == 'GET':
        try: #if the token is in the pool
            r = mdb['tokens'].find_one({"_id":get_token})
            user = mdb['users'].find_one({"username":r['user']['username']})
            try: #if the user already registered 
                session['username'] = user['username']
                session.permanent = True
            except TypeError: # the user is not regitered - should register him
            
                session['username'] = r['user']['username']
                session.permanent = True
                mdb['users'].insert(r['user']) #register the user
            else:
                mdb['tokens'].remove({"_id":r['_id']}) #anyway delete the token
                logen.info('%s logged in from email'%session['username'])
                
        except TypeError: #the provided token not exsist
            return render_template('token_unavaliable.html')
            
        return redirect(url_for('index'))
    logen.warn("abort(404)")
    abort(404)
	
@app.route('/register', methods=['POST','GET'])
def register():
    form = frmRegistration()
    if form.validate_on_submit():
        token = id_generator(size=40)
        mdb['tokens'].insert([{"_id":token, "user":request.form.to_dict(flat=True), "time":datetime.now()}])
        r = send_simple_message(request.form['username'],request.form['plname'], token )
        logen.info('%s sent registration form'%(request.form['username']))
        return render_template('mailok.html', username=request.form['username'], plname=request.form['plname'])
        
    else:
        logen.info('annonymous redirected to registration form')
        return render_template('register.html', form=form)

@app.route('/mailgun')
def mailgun():
	r= send_simple_message('ngetter@gmail.com','Experiment','bla bla token bla')
	return render_template('mailok.html', username='ngetter@gmail.com',r=0)

def send_simple_message(to, member, token):
    return requests.post(
        "https://api.mailgun.net/v2/nir.mailgun.org/messages",
        auth=("api", "key-6vcbt7a5dv8p754k3myvzqb5p8123ts5"),
        files=[("inline", open("static/img/logo.jpg","rb"))],
        data={"from": "Nir Getter <ngetter@gmail.com>",
              "to": to,
              "subject": u"אימות רישום למערכת חניכים - מרכז דאייה נגב [%s]"%member,
              "text": u"נרשמת למערכת חניכים במרכז הדאייה נגב - על מנת להשלים את הרישום עליך להעתיק את הקישור המצורף לשדה הכתובת בדפדפן: http://ancient-beyond-8896.herokuapp.com/login/%s"%token,
			  "html": render_template('register_email.html',username=member, token=token, server='http://ancient-beyond-8896.herokuapp.com'),
              "o:tag": "registration"
              })

@app.route('/participants/<int:id>')
def participants(id):
    con = mdb['operations']
    r = con.find_one({'_id':int(id)})
    try:
        users = mdb['users'].find({"username":{"$in":r['participate']}})
        return render_template('participants.html', l = list(users))
    except KeyError:
        return '<div class="alert alert-info">אין משתתפים בפעולה זו</div>'

@app.route('/mark_arrival', methods=['POST'])
def arrival():
    id = request.form['id']
    un = request.form['username']
    #un = "ngc-registration@balistica.org"
    con = mdb['operations']
    r = con.find_one({'_id':int(id)})
    try:
        if un in r['participate']:
            r['participate'].remove(un)
            logen.info('%s chacked out from %s'%(session['username'],r['date']))
            con.save(r)
            return dumps({'participate':False, 'length':len(list(r['participate']))})

        else:
            r['participate'].append(un)
            logen.info('%s chacked in to %s'%(session['username'],r['date']))
            con.save(r) 
            return dumps({'participate':True, 'length':len(list(r['participate']))})
            
    except TypeError:
        return 'Type Error %s'%id
    except ValueError:
        return 'ValueError'
    except KeyError:
        r['participate'] = [un]
        con.save(r) 
        return dumps({'participate':True, 'length':len(list(r['participate']))})

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))        
	
if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')
