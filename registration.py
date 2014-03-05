import os
from flask import Flask, Markup,  request, redirect, url_for, session, escape
from flask import render_template
from flask.ext.mongokit import MongoKit

from hashlib import sha224
import time
import requests
import random
import string


# configuration
#MONGODB_HOST = '127.0.0.1'
#MONGODB_PORT = 27017

MONGODB_HOST = 'troup.mongohq.com'
MONGODB_PORT = 10001
MONGODB_DATABASE = 'ngc-registration'
MONGODB_USERNAME = 'nirg'
MONGODB_PASSWORD  = 'dilk2d123'

app = Flask(__name__)
app.config.from_object(__name__)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

mdb = MongoKit(app)                        
               

@app.route('/index')
@app.route('/', methods=['POST','GET'])
def index():
    if request.method == 'POST':
        collection = mdb['operations']
        operation = [request.form.to_dict(flat=True)]
        collection.insert(operation)

    if 'username' in session:
        session.permanent = True
        col = mdb['operations']
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
        try:
            r = mdb['tokens'].find_one({"_id":get_token})
            session['username'] = r['username']
            session.permanent = True
            mdb['tokens'].remove(r)

        except KeyError:
            return render_template('token_unavaliable.html')

        return redirect(url_for('index'))

    return "ERROR"
	
@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        mdb['users'].insert([request.form.to_dict(flat=True)])

        token = id_generator(size=40)
        mdb['tokens'].insert([{"_id":token, "username":request.form['username']}])
        r = send_simple_message(request.form['username'],request.form['pname'], token )


        return render_template(url_for('mailok.html'))
    else:
        return render_template('register.html')

@app.route('/mailgun')
def mailgun():
	r = send_simple_message()
	return render_template('mailok.html')

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
    #un = "ngc-registration@balistica.org"
    con = mdb['operations']
    r = con.find_one({'_id':u'%s'%id})
    try:
        if un in r['participate']:
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

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))        
	
if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')
