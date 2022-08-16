import requests
from bs4 import BeautifulSoup
import sqlite3
from time import sleep
from datetime import datetime

class Event:
    def __init__(self, unique_id, date_time, title, venue, tags, month, day, year, time, time2, day_of_week, yyyymmdd, link):
        self.unique_id = unique_id
        self.date_time = date_time
        self.title = title.strip()
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

    curr_page = 0 # start at page 1
    while True:
        sp = get_page("https://www.juilliard.edu/stage-beyond/performance/calendar?start_date_from=-%201%20hours&start_date_thru=&division=All&tags=All&date_hidden=Date&page=", curr_page) 

        events = sp.find_all('li', {'class': 'event'}) # get all events on page
        
        for e in events:
            if e.find('time'): # if we have a time, the rest of the info will be there
                date_time = e.find('time')
                date_time = datetime.strptime(date_time.attrs['datetime'], '%Y-%m-%dT%H:%M:%SZ')
                month = date_time.strftime('%B') # for searching db by month in app
                day = date_time.strftime('%d') # for searching db by day in app
                year = date_time.strftime('%Y') # for searching db by year in app
                time = date_time.strftime('%I:%M%p') # for searching db by time in app
                time2 = date_time.strftime('%I:%M%p')
                if ":00" in time2: 
                    time2 = time2.replace(":00", "")
                day_of_week = date_time.strftime('%A') # for searching db by day of week in app
                title = e.find('div', {'class': 'title-subtitle'}).text
                venue = e.find('div', {'class': 'field--name-field-venue'}).text
                tags = e.find('div', {'class': 'field--name-field-event-tags'}).text.split('\n')
                yyyymmdd = date_time.strftime('%Y%m%d') 
                link = "http://juilliard.edu" + e.find(
                    'div', {'class': 'field--name-field-event-purchase-url'}).find('a')['href']
                while '' in tags:
                    tags.remove('')
                
                tags = ",".join(tags)

                unique_id = my_hash(title + str(date_time))
                event = Event(unique_id, date_time, title, venue, tags, month, day, year, time, time2, day_of_week, yyyymmdd, link)
                results.append(event)

        curr_page += 1 # increment to move on to next page
        if not sp.find('a', {'class': 'button js-load-more'}): # "Load More" button is not present
            break
    
    return results

def insert_into_db(events):
    for event in events:
        conn = sqlite3.connect('juilliard.db')
        c = conn.cursor()
        c.execute('REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (event.unique_id, event.date_time, event.title, event.venue, event.tags, event.month, event.day, event.year, event.time, event.time2, event.day_of_week, int(event.yyyymmdd), event.link))
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

    c.execute('''CREATE TABLE IF NOT EXISTS events (unique_id INTEGER PRIMARY KEY, date_time, title, venue, tags, month, day, year, time, time2, day_of_week, yyyymmdd INTEGER, link)''')
    insert_into_db(events)