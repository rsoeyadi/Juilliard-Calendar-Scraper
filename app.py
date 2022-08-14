from flask import Flask, session, render_template, request, g
import sqlite3
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    data = search_db()
    return render_template("index.html", results=data, q=request.args.get('q'))

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
    
if __name__ == '__main__':
    app.run()