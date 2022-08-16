from re import L
from flask import Flask, render_template, request, g, session
import sqlite3
from datetime import datetime
import os
import time

app = Flask(__name__)
app.secret_key = os.urandom(12)

@app.route("/", methods=['GET', 'POST'])
def index():
    
    data = search_db() # get events from database
    lastUpdated = get_last_updated_time()
    keywords = get_keywords()


    return render_template("index.html", results=data, q=request.args.get('q'), lastUpdatedTime=lastUpdated, keywords=keywords)
   
@app.route("/remove_keyword", methods=['GET', 'POST'])
def remove_keyword():
    if request.method == 'POST':
        keywords = get_keywords()
        kw = request.form.get('remove_keyword', False)

        if kw in keywords:
            keywords.remove(kw)
            session['keywords'] = keywords
            
        app.logger.error("removing->" + kw)
            
        session['keywords'] = keywords
        return index()
    
    return index()


@app.route("/add_keyword", methods=['GET', 'POST'])
def add_keyword():
    if request.method == 'POST':
        keywords = get_keywords()
        keyword = request.form.get('add_keyword', False)

        for keyword in keywords:
            if keyword not in session['keywords']:
                session['keywords'].append(keyword)

        session['keywords'] = keywords
    return index()

def get_last_updated_time():
    # get last modified time of database
    updatedOn_time = os.path.getmtime('./juilliard.db')
    updatedOn_time = time.ctime(updatedOn_time)  # cast to datetime object
    updatedOn_time = datetime.strptime(updatedOn_time, "%a %b %d %H:%M:%S %Y")
    now = datetime.now()
    lastUpdatedTime = now - updatedOn_time
    # convert to minutes
    lastUpdatedTime = lastUpdatedTime.seconds / 60

    if lastUpdatedTime > 60:
        lastUpdatedTime = lastUpdatedTime / 60
        lastUpdatedTime = str(int(lastUpdatedTime)) + " hours"
    else:
        lastUpdatedTime = str(round(lastUpdatedTime)) + " minutes"

    return lastUpdatedTime

def search_db():
    keywords = get_keywords()
    db = getattr(g, '_database', None)
    q = request.args.get('q')

    if db is None:
        db = g._database = sqlite3.connect('./juilliard.db')
    cursor = db.cursor()

    if q and q not in keywords:
        keywords.append(q)
        session['keywords'] = keywords

    qs = []
    query = "SELECT * FROM events WHERE(yyyymmdd >= {}) "

    if q or keywords:
        for i in range(len(keywords)):
            query += "AND ((title LIKE '%{}%') OR (tags LIKE '%{}%') OR (venue LIKE '%{}%') OR (month LIKE '%{}%') OR (day LIKE '%{}%') OR (year LIKE '%{}%') OR (time LIKE '%{}%') or (day_of_week LIKE '%{}%')) "
            for _ in range(8):
                if keywords[i] and keywords[i] != '':
                    qs.append(keywords[i])
        query += ("ORDER BY date_time ASC")
        currTime = datetime.now().strftime('%Y%m%d')
        cursor.execute(query.format(datetime.now().strftime('%Y%m%d'), *qs,))
    else:
        cursor.execute("SELECT * FROM events WHERE (yyyymmdd >= ?) ORDER BY date_time ASC",(datetime.now().strftime('%Y%m%d'),))
    results = cursor.fetchall()
    
    results = [(str(event[3]), str(event[1]), str(event[2]), str(event[4])) for event in results]
    if not results:
        return
    return results

def get_keywords():
    if not session.get('keywords'):
        session['keywords'] = []
    return session['keywords']

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