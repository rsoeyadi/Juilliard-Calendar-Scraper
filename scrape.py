import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import re


class Event:
    def __init__(self, unique_id, date_time, title, subtitle, venue, tags, month, day, year, time, time2, day_of_week, yyyymmdd, link):
        self.unique_id = unique_id
        self.date_time = date_time
        self.title = title.strip()
        self.subtitle = subtitle.strip()
        self.venue = venue
        self.tags = tags
        self.month = month
        self.day = day
        self.year = year
        self.time = time
        self.time2 = time2
        self.day_of_week = day_of_week
        self.yyyymmdd = yyyymmdd
        self.link = link

    def __str__(self):
        return '{} | {} @ {} | {}'.format((self.date_time), self.title.strip(), self.venue.strip(), self.tags)


def get_page(url, page_number):
    url = url + str(page_number)
    r = requests.get(url)
    r = BeautifulSoup(r.text, 'html.parser')
    return r


def get_events():
    results = []

    curr_page = 0  # start at page 1
    while True:
        sp = get_page(
            "https://www.juilliard.edu/stage-beyond/performance/calendar?start_date_from=09/1/22&start_date_thru=&division=All&tags=All&date_hidden=Date&page=", curr_page)

        # get all events on page
        events = sp.find_all('li', {'class': 'event'})

        for e in events:
            if e.find('time'):  # if we have a time, the rest of the info will be there
                date_time = e.find('time')
                date_time = datetime.strptime(
                    date_time.attrs['datetime'], '%Y-%m-%dT%H:%M:%SZ')
                # for searching db by month in app
                month = date_time.strftime('%B')
                # for searching db by day in app
                day = date_time.strftime('%d')
                # for searching db by year in app
                year = date_time.strftime('%Y')
                # for searching db by time in app
                time = date_time.strftime('%I:%M%p')
                time2 = date_time.strftime('%I:%M%p')
                if ":00" in time2:
                    time2 = time2.replace(":00", "")
                # for searching db by day of week in app
                day_of_week = date_time.strftime('%A')
                title = e.find(
                    'div', {'class': 'title-subtitle'}).find('h3').text
                subtitle = e.find(
                    'div', {'class': 'field--name-field-subtitle'}).text if e.find('div', {'class': 'field--name-field-subtitle'}) else ''
                venue = e.find(
                    'div', {'class': 'field--name-field-venue field__item'}).text if e.find('div', {'class': 'field--name-field-venue field__item'}) else ''
                tags = e.find(
                    'div', {'class': 'field--name-field-event-tags'}).text.split('\n')
                yyyymmdd = date_time.strftime('%Y%m%d')
                link = "http://juilliard.edu" + e.find(
                    'div', {'class': 'field--name-field-event-purchase-url'}).find('a')['href']

                tags = list(set(tags))
                if '-' in title:
                    hyphenated_words = [
                        word for word in title.split() if '-' in word]
                    if hyphenated_words:
                        for word in hyphenated_words:
                            tags.extend([word, word.replace('-', '')])

                standard_date_format = date_time.strftime(
                    '%m/%d/%Y')  # ex. 1/01/2022
                tags.extend(  # different date forms, ex. 1/1/22, 1/01/22, etc.
                    [standard_date_format, standard_date_format[:6] + standard_date_format[8:], date_time.strftime(
                        '%m/%-d/%Y'), standard_date_format[:3] + standard_date_format[4:6] + standard_date_format[8:] if standard_date_format[3] == '0' else '',
                        standard_date_format[1:] if standard_date_format[0] == '0' else ''])

                instruments = "Piano Violin Viola Cello Bass Guitar Flute Clarinet Saxophone Trumpet Trombone Tuba Percussion Harp Voice Organ".split()

                # check for graduting students' recitals
                if ';' not in title and ("," in title) and any(instrument in title for instrument in instruments) and ("Faculty" not in title):
                    tags.extend(["graduate", "graduating",
                                "grad recital", "grad recitals", "senior recital", "seniors"])
                if 'Preparatory Education' not in tags:
                    tags.extend(["college-only", "college-division"])

                for word in title.split():
                    tags.append(re.sub(r'\W+', '', word.lower()))
                for word in venue.split():
                    tags.append(re.sub(r'\W+', '', word.lower()))

                while '' in tags:
                    tags.remove('')

                tags = ",".join(tags)

                unique_id = my_hash(title + str(date_time))
                event = Event(unique_id, date_time, title, subtitle, venue, tags, month,
                              day, year, time, time2, day_of_week, yyyymmdd, link)
                results.append(event)

        curr_page += 1  # increment to move on to next page
        # "Load More" button is not present
        if not sp.find('a', {'class': 'button js-load-more'}):
            break

    return results


def insert_events_into_db(events):
    for event in events:
        conn = sqlite3.connect('juilliard.db')
        c = conn.cursor()
        c.execute('REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (event.unique_id, event.date_time, event.title, event.venue,
                  event.tags, event.month, event.day, event.year, event.time, event.time2, event.day_of_week, int(event.yyyymmdd), event.link, event.subtitle))
        conn.commit()
        conn.close()


def insert_current_time_into_db():
    conn = sqlite3.connect('juilliard.db')
    c = conn.cursor()
    c.execute('REPLACE INTO extras VALUES (?, ?)',
              ("juilliard.db", datetime.utcnow(),))
    conn.commit()
    conn.close()


def insert_each_word_into_db(events):
    keywords = set()
    for event in events:
        conn = sqlite3.connect('juilliard.db')
        c = conn.cursor()
        for word in event.title.split():
            keywords.add(re.sub(r'\W+', '', word.lower()))
        for word in event.tags.split(','):
            keywords.add(word.lower())

        # if new line in title, remove it
        if '\n' in event.title:
            event.title = event.title.replace('\n', ' ')

        keywords.add(event.title.lower())
        keywords.add(event.venue.lower())

    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]
    days = ["monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday"]
    times = ["1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm", "11pm", "12pm",
             "8am", "9am", "10am", "11am", "2:30pm", "3:30pm", "4:30pm", "5:30pm", "6:30pm", "7:30pm", "8:30pm"]
    for month in months:
        keywords.add(month)
    for day in days:
        keywords.add(day)
    for time in times:
        keywords.add(time)

    conn = sqlite3.connect('juilliard.db')
    c = conn.cursor()

    for keyword in keywords:
        if len(keyword) <= 2:
            continue

        c.execute('REPLACE INTO keywords VALUES (?)',
                  (keyword,))
    conn.commit()
    conn.close()


def my_hash(s):
    h = 0
    for c in s:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return h


if __name__ == '__main__':
    events = get_events()

    # create connection
    conn = sqlite3.connect('juilliard.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS events (unique_id INTEGER PRIMARY KEY, date_time, title, venue, tags, month, day, year, time, time2, day_of_week, yyyymmdd INTEGER, link, subtitle)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS extras (filename PRIMARY KEY, current_time)''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS keywords (keyword PRIMARY KEY)''')

    insert_current_time_into_db()
    insert_events_into_db(events)
    insert_each_word_into_db(events)
