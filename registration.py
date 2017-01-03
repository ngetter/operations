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
from flask.ext.mongokit import MongoKit
from flask_wtf import Form
from wtforms import TextField
from wtforms.validators import DataRequired, Email
from bson.objectid import ObjectId
from bson.json_util import dumps as bdumps

from logentries import LogentriesHandler


###### configuration
LOCAL = False # Make true if running from the IDE
MONGO_LOCAL = LOCAL and False # Make true if running from the IDE and the mongod is running too on the local machine

if LOCAL:
    # SERVER_NAME = '127.0.0.1:5000'
    RETURN_TO = 'http://127.0.0.1:5000'

else:
    # SERVER_NAME = r'http://ancient-beyond-8896.herokuapp.com:80'
    RETURN_TO = r'http://opsign.herokuapp.com'

if MONGO_LOCAL:
    MONGODB_HOST = '127.0.0.1'
    MONGODB_PORT = 27017
    MONGODB_DATABASE = 'test'
else:
    MONGODB_HOST = 'ds127928.mlab.com'
    MONGODB_PORT = 27928
    MONGODB_DATABASE = 'operations'
    MONGODB_USERNAME = 'nir'
    MONGODB_PASSWORD = '123456'
############# configuration

TOR_SIZE = 64

app = Flask(__name__)
app.config.from_object(__name__)

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


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/index')
@app.route('/', methods=['POST', 'GET'])
def index():
    rule = request.url_rule
    print (rule.rule)
    if 'username' in session:
        if not ('api' in rule.rule):
            session.permanent = True
            username = escape(session['username'])
            try:
                users = mdb['users']
                r = users.find_one({'username': username})
                session['plname'] = r['plname']
                if LOCAL == False and username != "ngetter@gmail.com": logen.info('%s logged in' % r['plname'])
            except TypeError:
                return redirect(url_for('logout'))
            except Exception:
                if LOCAL == False: logen.warn("abort(404)")
                abort(404)

        l = getOperations(username)
        return render_template('main.html', l=l, user=r)
            # request by '/top
        
    else:
        return redirect(url_for('register'))

@app.route('/api', methods=['POST', 'GET'])
def apiOperations():
    col = mdb['operations']
    l = col.find({'date': {'$gte': dt.now(None) - td(2)}}).sort("date", 1)
    res = [d for d in l]
    return jsonify(data=res, success=True)
    
def getOperations(username):
    col = mdb['operations']
    l = list(col.find({'date': {'$gte': dt.now(None) - td(2)}}).sort("date", 1).limit(12))
    for li in l:
        try:

            li['participants_count'] = len(li['participate'])
            par_list = username in li
            par_dict = [x for x in li['participate'] if isinstance(x, dict) and x['un'] == username]
            li['participate'] = str((len(par_dict) > 0) or par_list)
            li['participant_comment'] = par_dict[0]['comment']
        except:
            pass
    return l
        
@app.route('/signin', methods=['POST', 'GET'])
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
def login(get_token):
    # if request.method == 'GET':
    try:  #if the token is in the pool
        r = mdb['tokens'].find_one({"_id": get_token})
        user = mdb['users'].find_one({"username": r['user']['username']})
        try:  #if the user already registered
            session['username'] = user['username']
            session['plname'] = user['plname']
            session.permanent = True
        except TypeError:  # the user is not regitered - should register him

            session['username'] = r['user']['username']
            session.permanent = True
            mdb['users'].insert(r['user'])  #register the user
        else:
            mdb['tokens'].remove({"_id": r['_id']})  #anyway delete the token
            #logen.info('%s logged in from email'%session['username'])

    except TypeError:  #the provided token not exsist
        return render_template('token_unavaliable.html')

        #return redirect(url_for('index'))
        #logen.warn("abort(404)")
        #abort(404)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if 'username' in session:
        logen.info('%s using registration form when already registered' % (request.form['username']))
        return redirect(url_for('index'))
    else:
        form = frmRegistration()
        if form.validate_on_submit():
            token = id_generator(size=40)
            mdb['tokens'].insert([{"_id": token, "user": request.form.to_dict(flat=True), "time": dt.now()}])
            login(token)
            # r = send_simple_message(request.form['username'],request.form['plname'], token )
            logen.info('%s [%s] sent registration form' % (request.form['plname'], request.form['username']))
            #return render_template('mailok.html', username=request.form['username'], plname=request.form['plname'])
            return redirect(url_for('index'))
        else:
            logen.info('annonymous redirected to registration form')
            return render_template('register.html', form=form)


def sendRegMessage(to, member, id, opdate):
    con = mdb['operations']
    r = con.find_one({'_id': ObjectId(id)})
    try:
        users = mdb['users'].find({"username": {"$in": r['participate']}})
    except KeyError:
        users = []

    return requests.post(
        "https://api.mailgun.net/v2/nir.mailgun.org/messages",
        auth=("api", "key-6vcbt7a5dv8p754k3myvzqb5p8123ts5"),
        files=[("inline", open("static/img/logo.jpg", "rb"))],
        data={"from": "מערכת רישום לפעולה - מדנ <postmaster@nir.mailgun.org>",
              "to": to,
              "subject": u"רישום לפעולה במרכז דאייה נגב [%s]" % member,
              "text": u"נרשמת לפעולה במרכז הדאייה נגב ביום -  %s" % opdate,
              "html": render_template('registeToOperation.html', username=member, id=id, opdate=opdate,
                                      users=list(users), server=RETURN_TO),
              "o:tag": "registration"
        })


@app.route('/participants/<ObjectId:id>')
def participants(id):
    con = mdb['operations']
    r = con.find_one({'_id': ObjectId(id)})
    try:

        new_par = [x for x in r['participate'] if isinstance(x, dict)]
        new_par = [x['un'] for x in new_par]
        users = mdb['users'].find({"username": {"$in": r['participate'] + new_par}})
        l = list(users)
        # print(r)
        tmp = []
        for x in l:
            tmp = [t for t in r['participate']
                   if isinstance(t, dict) and
                   t['un'] == x['username'] and
                   'comment' in t
            ]
            x['comment'] = tmp[0]['comment'] if len(tmp) == 1 else ""
            if 'position' in x:
                try:
                    x['position'] = mytor(int(r['first']), int(x['position']))
                except ValueError:
                    x['position'] = 65
            else:
                x['position'] = 65

        part = sorted(l, key=lambda k: k['position'])
        return render_template('participants.html', l=part, operation=r)
    except KeyError:
        return render_template('participants.html', l=[], operation=r)


@app.route('/mark_arrival', methods=['POST'])
@app.route('/mark_arrival/<int:id>', methods=['GET'])
def arrival(id=None):
    print("arrival function %s" % request.method)
    try:
        un = escape(session['username'])
    except:
        return redirect(url_for('register'))

    if request.method == 'POST':
        id = request.form['id']

    # un = "ngc-registration@balistica.org"
    con = mdb['operations']
    r = con.find_one({'_id': ObjectId(id)})

    try:
        new_par = [x for x in r['participate'] if isinstance(x, dict) and x['un'] == un]
        print(len(new_par))  #new_par = [x['un'] for x in new_par]

        if un in r['participate']:
            r['participate'].remove(un)
            print('%s chacked out from %s' % (session['username'], r['date']))
            logen.info('%s chacked out from %s' % (session['username'], r['date']))
            con.save(r)
            if request.method == 'POST':
                return dumps({'participate': False, 'length': len(list(r['participate']))})
            else:
                return render_template('unregisterConfirm.html', opdate=r['date'], plname=session['plname'])
        elif len(new_par) > 0:
            print (new_par[0])
            r['participate'].remove(new_par[0])
            con.save(r)
            if request.method == 'POST':
                return dumps({'participate': False, 'length': len(list(r['participate']))})
            else:
                return render_template('unregisterConfirm.html', opdate=r['date'], plname=session['plname'])
        else:
            r['participate'].append(dict(un=un))

            logen.info('%s chacked in to %s' % (session['username'], r['date']))
            sendRegMessage(session['username'], session['plname'], id, r['date'])
            print('%s chacked in to %s' % (session['username'], r['date']))
            con.save(r)
            if request.method == 'POST':
                return dumps({'participate': True, 'length': len(list(r['participate']))})
            else:
                return 'נוסף לרשימת המשתתפים בפעולה'

    except TypeError:
        logen.error('Type Error in arrival() [/%s] %s' % (request.method, id))
        print('Type Error in arrival() [/%s] %s' % (request.method, id))
        abort(404)
    except ValueError:
        return 'ValueError'
    except KeyError:
        print('KeyError')
        r['participate'] = [dict(un=un)]
        logen.info('%s chacked in to %s' % (session['username'], r['date']))
        sendRegMessage(session['username'], session['plname'], id, r['date'])
        con.save(r)
        return dumps({'participate': True, 'length': len(list(r['participate']))})


@app.route('/tables/<collection>')
def tables(collection):
    if 'username' in session:
        session.permanent = True
        username = escape(session['username'])
        try:
            users = mdb['users']
            r = users.find_one({'username': username})
            session['plname'] = r['plname']
        except TypeError:
            return redirect(url_for('logout'))
        tor = mdb[collection]
    l = list(tor.find({}).sort("_id", 1))
    return render_template('%s/index.html' % collection, l=l, user=r)


@app.route('/update', methods=['POST'])
def update():
    id = request.form['pk']
    newname = request.form['value']
    params = request.form['name'].split("/")
    try:
        tor = mdb[params[0]]
        r = tor.find_one({'_id': ObjectId(id)})
        if len(params) == 2:
            r[params[1]] = newname
        elif len(params) == 3:
            username = escape(session['username'])
            t = r[params[1]]
            key = params[2]
            doc = [x for x in t if isinstance(x, dict) and x['un'] == username][0]
            t.remove(doc)
            doc[key] = newname
            t.append(doc)
            r[params[1]] = t

        tor.save(r)
        return "True"
    except TypeError:
        return "Type Error %s" % id


@app.route('/getUserDetails', methods=['POST'])
def getUserDetails():
    email = request.form['name']
    try:
        users = mdb['users']
        r = users.find_one({'username': email})
        return dumps({"plname": r['plname'], "status": r['status']})
    except TypeError:
        return dumps({"response": "new member"})


@app.route('/SendWeeklyEmail/<int:fri>/<int:fri_guests>/<int:sat>/<int:sat_guests>')
def sendWeeklyEmail(fri,fri_guests, sat, sat_guests):
    members = fri + sat
    html = render_template('weeklyMail.html', membersNumber=members, 
        fri=fri, sat=sat, fri_guests=fri_guests,sat_guests=sat_guests )
    r = requests.post(
        "https://api.mailgun.net/v2/nir.mailgun.org/messages",
        auth=("api", "key-6vcbt7a5dv8p754k3myvzqb5p8123ts5"),
        files=[("inline", open("static/img/logo.jpg", "rb"))],
        data={"from": "Nir Getter <ngetter@gmail.com>",
              "to": ["Ngc@savoray.com "],
              "subject": u"תזכורת בנוגע לרישום לפעולה במדנ לסוף השבוע הקרוב",
              "text": u"תזכורת בנוגע לרישום לפעולה במדנ לסוף השבוע הקרוב",
              "html": html,
              "o:tag": "reminder"
        })

    return html


@app.route('/SendReminder')
def sendReminder():
    con = mdb['operations']
    r = con.find({'date': {'$gte': dt.now(None) - td(2)}}).sort("date", 1).limit(2)
    l_1 = []
    l_2 = []
    err = []
    try:
#        users_1 = mdb['users'].find({"username": {"$in": r[0]['participate']}})
        l_1 = list(r[0]['participate'])
    except:
        l_1 = []
        err.append({'label':"first day"})
    
    try:
#        users_2 = mdb['users'].find({"username": {"$in": r[1]['participate']}})
        l_2 = list(r[1]['participate'])
    except:
        l_2 = []
        err.append({'label': "second day"})
        # print(r)
    try:
        fri_guests = r[0]['guests']
    except KeyError:
        fri_guests = 0
        
    try:
        sat_guests = r[1]['guests']
    except KeyError:
        sat_guests = 0        
        
    return sendWeeklyEmail(len(l_1),fri_guests, len(l_2), sat_guests)
    # return str({'fri_num' : len(l_1),
                # 'fri_guests' : fri_guests,
                # 'fri_date': r[0]['date'],
                # 'sat_num' : len(l_2),
                # 'sat_guests' : sat_guests,
                # 'sat_date': r[1]['date'],
                # 'err' : err})


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


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


if __name__ == "__main__":
    import os
    app.run(debug=True, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))