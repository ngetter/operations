import os
from flask import Flask, Markup,  request, redirect, url_for, session, escape
from flask import render_template
from hashlib import sha224
from mongokit import Connection, Document

import sqlite3 
import time
import requests
import random
import string
import csv

# configuration
MONGODB_HOST = '127.0.0.1'
MONGODB_PORT = 27017

app = Flask(__name__)
app.config.from_object(__name__)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
# connect to the database
connection = Connection(app.config['MONGODB_HOST'],
                        app.config['MONGODB_PORT'])

@app.route('/index')
@app.route('/', methods=['POST','GET'])
def index():
    if request.method == 'POST':
        collection = connection['test'].operations
        operation = [request.form.to_dict(flat=True)]
        collection.insert(operation)

    if 'username' in session:
        session.permanent = True
        col = connection['test'].operations
        l = list(col.find())
        return render_template('main.html', l=l, username=escape(session['username']))	
    else:
        return redirect(url_for('register'))

@app.route('/signin',methods=['POST','GET'])
def signin():
		if request.method == 'POST':
		
			return redirect(url_for('/'))
		else:
			return render_template('signin.html')

@app.route('/token', methods=['GET'])
def token():
	if request.method == 'GET':
		get_token = request.args.get('token','')
		conn = sqlite3.connect('example.db')
		c = conn.cursor()
		c.execute('select username from tokens where token=?',(get_token,)) 
		try:
			session['username'] = c.fetchone()[0]
			session.permanent = True
			c.execute('delete from tokens where token=?',(get_token,))
		except TypeError:
			return render_template('token_unavaliable.html')
		
		conn.commit()
		conn.close()
		return redirect(url_for('index'))
	
	return "ERROR"
	
@app.route('/register', methods=['POST','GET'])
def register():
		if request.method == 'POST':
			conn = sqlite3.connect('example.db')
			c = conn.cursor()
			c.execute('INSERT INTO users VALUES(?,"pass",?,?,?)',(request.form['username'],
			request.form['pname'],
			request.form['lname'],
			request.form['phone']))
			
			token = id_generator(size=40)
			c.execute('INSERT INTO tokens VALUES(?,?)',(request.form['username'],token))
			r = send_simple_message(request.form['username'],request.form['pname'], token )
			conn.commit()
			conn.close()
		
			return render_template(url_for('mailok.html'))
		else:
			return render_template('register.html')

@app.route('/mailgun')
def mailgun():
	r = send_simple_message()
	return render_template('mailok.html')

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))

	
def send_simple_message(to, member, token):
    return requests.post(
        "https://api.mailgun.net/v2/nir.mailgun.org/messages",
        auth=("api", "key-6vcbt7a5dv8p754k3myvzqb5p8123ts5"),
        data={"from": "Nir Getter <ngetter@gmail.com>",
              "to": to,
              "subject": "רישום למערכת",
              "text": "נרשמת איזה יופי",
			  "html": render_template('register_email.html',username=member, token=token)})


@app.route('/getop')
def readOperatios():
    with open("operations.csv","r") as f:
		df = csv.reader(f)
		ops = [line for line in df]
	
		conn = sqlite3.connect('example.db')
		c = conn.cursor()
		c.executemany('insert into operations values(?,?,?,?,?)',ops[1:])
	
		conn.commit()
		conn.close()
	
		return redirect(url_for('index'))
		
@app.route('/mark_arrival', methods=['POST'])
def arrival():
    id = request.form['id']
    un = request.form['username']
    #un = "test@balistica.org"
    con = connection['test'].operations
    r = con.find_one({'_id':u'%s'%id})
    try:
        if request.form['username'] in r['participate']:
            r['participate'].remove(un)
            con.save(r)
            return 'nonpar'

        else:
            r['participate'].append(un)
            con.save(r) 
            return 'par'
            
    except TypeError:
        return 'Type Error %s'%id
    
    except KeyError:
        r['participate'] = [un]
        con.save(r) 
        return 'par'
        
	
if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')
