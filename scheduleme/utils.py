# -*- coding: UTF-8 -*-
import os
from scheduleme import *

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

def sendRegMessage(to, member, id, opdate):
    con = mdb['operations']
    r = con.find_one({'_id': ObjectId(id)})
    try:
        users = mdb['users'].find({"username": {"$in": r['participate']}})
    except KeyError:
        users = []
    
    mailtxt = render_template('registeToOperation.html', username=member, id=id, opdate=opdate,
                                      users=list(users), server=RETURN_TO)
    mailtxt = transform(html = mailtxt)
    return requests.post(
        "https://api.mailgun.net/v3/mail.ngc.org.il/messages",
        auth=("api", os.getenv('MAILGUN_KEY','')),
        files=[("inline", open("static/img/logo.png", "rb"))],
        data={"from": "מערכת רישום לפעולה - מדנ <admin@mail.ngc.org.il>",
              "to": to,
              "subject": u"רישום לפעולה במרכז דאייה נגב [%s]" % member,
              "text": u"נרשמת לפעולה במרכז הדאייה נגב ביום -  %s" % opdate,
              "html": mailtxt,
              "o:tag": "registration"
        })

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

