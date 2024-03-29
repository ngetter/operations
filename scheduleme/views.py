# -*- coding: UTF-8 -*-
import os
import requests
from scheduleme import *
from scheduleme.utils import *

from flask import Flask, Markup, request, redirect, url_for, session, escape, render_template, abort, send_from_directory, jsonify

from json import dumps
from datetime import timedelta as td
from datetime import datetime as dt
from bson.objectid import ObjectId

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'ico/favicon.ico', mimetype='image/vnd.microsoft.icon')
                               
@app.route('/mobile')
def mobile():
    return send_from_directory(os.path.join(app.root_path, 'ionic'),
                               'www/index.html', mimetype='text/html')

@app.route('/build/<path:path>')
def mobileBuild(path):
    app.static_folder = os.path.join(app.root_path, 'ionic/www/build/')
    return send_from_directory(os.path.join(app.root_path, 'ionic/www/build/'), path)
                               
@app.route('/service-worker.js')
def serviceworker():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'js/service-worker.js', mimetype='text/javascript')
                                  
@app.route('/index')
@app.route('/', methods=['POST', 'GET'])
def index():
    print ("hi i am index: runned from code")
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

@app.route('/AddOperations', methods=['GET'])
def addOperations():
    return render_template('add_operations.html')
    

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

@app.route('/api/getparticipants', methods=['POST'])
@app.route('/participants/<ObjectId:id>')
def participants(id = None):
    con = mdb['operations']
    if request.method == 'POST':
        jsonres = request.get_json()
        id = jsonres['id']
        
    r = con.find_one({'_id': ObjectId(id)})
    try:

        new_par = [x for x in r['participate'] if isinstance(x, dict)]
        new_par = [x['un'] for x in new_par]
        users = mdb['users'].find({"username": {"$in": r['participate'] + new_par}},{"_id":0})
        l = list(users)
        print(l)
        print(r)
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
                    x['position'] = 1
            else:
                x['position'] = 1

        part = sorted(l, key=lambda k: k['position'])
        if request.method == 'POST':
            return dumps(part)
        else:
            return render_template('participants.html', l=part, operation=r)
    except KeyError:
        return render_template('participants.html', l=[], operation=r)


@app.route('/mark_arrival', methods=['POST'])
def arrival():
    print("arrival function %s" % request.method)
    content = request.get_json(silent=True)
    print content
    un = None
    try:
        un = escape(session['username'])
        print 'username set from session %s' % un
    except:
        pass
        #return redirect(url_for('register'))
        #un = request.form['username']
    if un is None:
        un = content['username']
        id = content['id']
        print('username & id set from POST json request %s, %s' % (id, un))
    else:
        id = request.form['id']
        
    con = mdb['operations']
    r = con.find_one({'_id': ObjectId(id)})

    try:
        new_par = [x for x in r['participate'] if isinstance(x, dict) and x['un'] == un]
        print(len(new_par))  #new_par = [x['un'] for x in new_par]

        if un in r['participate']: # remove participant already listed to op
            print ('#########  the un in r[participate] condition')
            r['participate'].remove(un)
            print('%s chacked out from %s' % (un, r['date']))
            logen.info('%s chacked out from %s' % (un, r['date']))
            con.save(r)
            return dumps({'participate': False, 'length': len(list(r['participate']))})

        elif len(new_par) > 0: 
            print ('#########  the len(new_par) > 0 condition')
            print (new_par[0])
            r['participate'].remove(new_par[0])
            con.save(r)
            return dumps({'participate': False, 'length': len(list(r['participate']))})

        else: # append new participant to operation member list
            print ('#########  the append new participant to operation member list condition')
            r['participate'].append(dict(un=un))

            logen.info('%s chacked in to %s' % (un, r['date']))
            #sendRegMessage(un, session['plname'], id, r['date'])
            print('%s chacked in to %s' % (un, r['date']))
            con.save(r)
            return dumps({'participate': True, 'length': len(list(r['participate']))})

    except TypeError:
        logen.error('Type Error in arrival() [/%s] %s' % (request.method, id))
        print('Type Error in arrival() [/%s] %s' % (request.method, id))
        abort(404)
    except ValueError:
        return 'ValueError'
    except KeyError:
        print('####### KeyError adding a new participant (removing everyone else')
        r['participate'] = [dict(un=un)]
        logen.info('%s chacked in to %s' % (un, r['date']))
        #sendRegMessage(un, session['plname'], id, r['date'])
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
    html = transform(html)
    r = requests.post(
        "https://api.mailgun.net/v3/mail.ngc.org.il/messages",
        auth=("api", os.getenv('MAILGUN_KEY','')),
        # files=[("inline", open("../static/img/logo_48.png", "rb"))],
        data={"from": "NGC admin<admin@mail.ngc.org.il>",
              "to": ["members@mail.ngc.org.il"],
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
