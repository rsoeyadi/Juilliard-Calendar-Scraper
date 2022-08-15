from flask import Flask, session, render_template, request, g
import sqlite3
from datetime import datetime
import os
import time

app = Flask(__name__)

@app.route("/")
def index():
    data = search_db() # get events from database

    modTimeSinceEpoc = os.path.getmtime('./juilliard.db') # get last modified time of database
    modTimeSinceEpoc = datetime.fromtimestamp(modTimeSinceEpoc)  # cast to datetime object
    currTime = datetime.now()

    timeDiff = currTime - modTimeSinceEpoc
    time_passed = int(timeDiff.total_seconds() / 60)# get time passed since last modified
    if time_passed > 60: # if time passed is greater than 60 minutes, convert to hours
        time_passed = int(time_passed / 60)
        time_passed = str(time_passed) + ' hours'
    else:
        time_passed = str(time_passed) + ' minutes'
    return render_template("index.html", results=data, q=request.args.get('q'), lastUpdatedTime=time_passed)

def search_db():
    db = getattr(g, '_database', None)
    q = request.args.get('q')

    if db is None:
        db = g._database = sqlite3.connect('./juilliard.db')
    cursor = db.cursor()
    if q:
        cursor.execute("SELECT * FROM events WHERE title LIKE '%{}%' OR tags LIKE '%{}%' or venue LIKE '%{}%' OR month LIKE '%{}%' OR day LIKE '%{}%' OR year LIKE '%{}%' OR time LIKE '%{}%' or day_of_week LIKE '%{}%' ORDER BY date_time ASC".format(q, q, q, q, q, q, q, q))
    else:
        cursor.execute("SELECT * FROM events ORDER BY date_time ASC")
    results = cursor.fetchall()
    
    results = [(str(event[3]), str(event[1]), str(event[2]), str(event[4])) for event in results]
    if not results:
        return
    return results

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    if not value: 
        return 
    return (datetime.strptime(value, format)).strftime('%a, %B %d, %Y at %-I:%M%p')

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}
    
if __name__ == '__main__':
    app.run()