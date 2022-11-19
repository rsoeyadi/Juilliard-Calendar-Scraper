from flask import Flask, render_template, request, g, session, redirect, url_for
import sqlite3
from datetime import datetime, date, timedelta
import re

app = Flask(__name__)
app.secret_key = "\x0b\x16\x8al\x14\xa5&\xf2\xf5\x85\xf8\xed\t\xe8\xb1Z\x9e\xbbN\xfcR87"


@app.route("/", methods=['GET', 'POST'])
def index():
    data = search_db()  # get events from database

    if not data:  # get number of events
        numberOfEvents = 0
    else:
        numberOfEvents = len(data)
        if session.get('desc'):
            data.reverse()
    lastUpdated = get_last_updated_time()
    keywords = get_keywords()
    keywords_list = get_keyword_list() # for dropdown menu

    return render_template(
        "index.html",
        results=data,
        q=request.args.get('q'),
        lastUpdatedTime=lastUpdated,
        keywords=keywords,
        numberOfEvents=numberOfEvents,
        desc=session.get('desc'),
        keywords_list=keywords_list)

def get_keyword_list():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect('./juilliard.db')
    cursor = db.cursor()
    cursor.execute("SELECT * FROM keywords")
    results = (cursor.fetchall())
    results = [keyword[0] for keyword in results]
    return results

@app.route("/sort", methods=['POST'])
def toggleDesc():
    if request.method == 'POST':
        if session.get('desc'):
            session['desc'] = False
        else:
            session['desc'] = True
    return redirect(url_for('index'))


@app.route("/add_keyword", methods=['POST'])
def add_keyword():
    if request.method == 'POST':
        keywords = get_keywords()
        kw = request.form.get("q", False)
        kw = kw.strip()  # remove whitespace

        # split keywords by spaces
        curr_list = kw.split(" ")

        for kw in curr_list:
            # regex to remove special characters except colon
            kw = re.sub(r'[^a-zA-Z0-9/:-]+', '', kw)
            if kw:  # if sanitized keyword is not empty
                kw = kw.lower()

                # ex. "mondays at 7:30pm" -> "monday at 7:30pm"
                days = ["mondays", "tuesdays", "wednesdays",
                        "thursdays", "fridays", "saturdays", "sundays"]
                if kw in days:
                    kw = kw[:-1]

                if kw not in keywords:
                    keywords.append(kw)
                    session['keywords'] = keywords
                session.modified = True

    return redirect(url_for('index'))


@app.route("/remove_keyword", methods=['POST'])
def remove_keyword():
    if request.method == 'POST':
        keywords = get_keywords()
        kw = request.form.get('remove_keyword', False)

        if kw in keywords:
            keywords.remove(kw)
            session['keywords'] = keywords
        session.modified = True
    return redirect(url_for('index'))


@app.route("/clear_all_filters", methods=['POST'])
def clear_all_filters():
    if request.method == 'POST':
        session['keywords'] = []
        session.modified = True
    return redirect(url_for('index'))


def get_last_updated_time():
    db = getattr(g, '_database', None)

    # get last modified time of database
    if db is None:
        db = g._database = sqlite3.connect('./juilliard.db')
    cursor = db.cursor()
    cursor.execute("SELECT * FROM extras")
    results = (cursor.fetchall())
    lastUpdatedTime = results[0][1]

    # convert to datetime object
    lastUpdatedTime = datetime.strptime(
        lastUpdatedTime, '%Y-%m-%d %H:%M:%S.%f')

    now = datetime.now()

    lastUpdatedTime = now - lastUpdatedTime

    # convert to minutes
    lastUpdatedTime = lastUpdatedTime.seconds / 60
    if lastUpdatedTime > 60:  # if last updated time is greater than 1 hour
        lastUpdatedTime = lastUpdatedTime / 60
        lastUpdatedTime = round(lastUpdatedTime)

        lastUpdatedTime = str(
            lastUpdatedTime) + " hour" if lastUpdatedTime == 1 else str(lastUpdatedTime) + " hours"
    else:
        lastUpdatedTime = round(lastUpdatedTime)

        lastUpdatedTime = str(
            lastUpdatedTime) + " minute" if lastUpdatedTime == 1 else str(lastUpdatedTime) + " minutes"

    return lastUpdatedTime


def search_db():
    keywords = get_keywords()
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect('./juilliard.db')
    cursor = db.cursor()

    qs = []
    query = "SELECT * FROM events WHERE(yyyymmdd >= {}) "

    if keywords:
        for i in range(len(keywords)):
            query += "AND ((title LIKE '%{}%') OR (tags LIKE '%{}%') OR (venue LIKE '%{}%') OR (month LIKE '%{}%') OR (day LIKE '%{}%') OR (year LIKE '%{}%') OR (time LIKE '%{}%') OR (time2 LIKE '%{}%') OR (day_of_week LIKE '%{}%')) "
            for _ in range(9):
                if keywords[i] and keywords[i] != '':
                    qs.append(keywords[i])
        query += ("ORDER BY date_time ASC")
        cursor.execute(query.format(datetime.now().strftime("%Y%m%d"), *qs,))
    else:
        cursor.execute(
            "SELECT * FROM events WHERE (yyyymmdd >= ?) ORDER BY date_time ASC",
            (datetime.now().strftime("%Y%m%d"),
             ))
    results = cursor.fetchall()
    results = [(
                    str(event[3]), # venue
                    str(event[1]), # date_time
                    str(event[2]), # title
                    str(event[4]), # tags
                    str(event[12]), # link
                    datetime.strptime(event[1], "%Y-%m-%d %H:%M:%S").time().strftime("%I:%M %p").lstrip('0'), 
                    str(datetime.strptime(event[1], "%Y-%m-%d %H:%M:%S").date()) == str((datetime.today() - timedelta(hours=5)).strftime("%Y-%m-%d")), # change timedelta to 4 (from 5) when daylight savings time ends, i.e., March 2023
                    event[13]) 
                for event in results]
    
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
    return (datetime.strptime(value, format)).strftime(
        '%a, %B %d, %Y at %-I:%M%p')


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


if __name__ == '__main__':
    app.run()
