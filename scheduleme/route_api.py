# -*- coding: UTF-8 -*-
from scheduleme import app, mdb
from flask import Flask, Markup, request, redirect, url_for, session, escape, render_template, abort, send_from_directory, jsonify
from json import dumps
from datetime import timedelta as td
from datetime import datetime as dt
from bson.json_util import dumps as bdumps

@app.route('/api/add/<new_date>', methods=['GET'])
def add(new_date):
    ndate = addDate(new_date)
    return jsonify(data=str(ndate), success=True) 

@app.route('/api/delete/<del_date>', methods=['GET'])
def deleteOperation(del_date):
    nds = del_date.split("-") #new_date split
    ndate = dt( int(nds[0]), int(nds[1]), int(nds[2]) )
    mdb['operations'].remove({"date": ndate})
    return jsonify(data=str(ndate), success=True)

@app.route('/api/add/multi/<start_date>', methods=['GET'])
def batchdates(start_date):
    nds = start_date.split("-") #new_date split
    friday_one = dt( int(nds[0]), int(nds[1]), int(nds[2]) )
    if friday_one.weekday() Not in [4,5] :
        return 'Date should be friday or saturday'
        
    add_day = td(days = 1)
    
    response = []
    for next_weekend in range(0,8):
        weeks = td(weeks=next_weekend)
        ndate = friday_one + weeks
        response.append({ 'operation':addDate(ndate.strftime('%Y-%m-%d')) })
    
    return jsonify(data=response, success=True)
    
@app.route('/api/list', methods=['POST', 'GET'])
def apiOperations():
    col = mdb['operations']
    l = col.find({'date': {'$gte': dt.now(None) - td(2)}}).sort("date", 1)
    res = list(d for d in l)
    return bdumps(dict(data=res, success=True))
    
def addDate(new_date):
    days = ["ראשון",
    "שני",
    "שלישי",
    "רביעי",
    "חמישי",
    "שישי",
    "שבת"]
    nds = new_date.split("-") #new_date split
    ndate = dt( int(nds[0]), int(nds[1]), int(nds[2]) )
    comment = "יום {}".format(days[ndate.isoweekday()])
    mdb['operations'].insert([{"date":ndate, "comment":comment, "participants":[]}])
    return ndate
