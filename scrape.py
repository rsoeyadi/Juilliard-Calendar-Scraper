import requests
from bs4 import BeautifulSoup
import sqlite3
from time import sleep
from datetime import datetime

class Event:
    def __init__(self, date, time, title, venue, tags):
        self.date = date
        self.time = time
        self.title = title
        self.venue = venue
        self.tags = tags
        
    def __str__(self):
        return '{} | {} {} @ {} | {}'.format(str(self.date).strip(), self.time, self.title.strip(), self.venue.strip(), self.tags)

def get_page(url, page_number):
    url = url + str(page_number)
    r = requests.get(url)
    r = BeautifulSoup(r.text, 'html.parser')
    return r

def get_events():
    results = []
    curr_page = 0
    while True:
        sp = get_page("https://www.juilliard.edu/stage-beyond/performance/calendar?start_date_from=-%201%20hours&start_date_thru=&division=All&tags=All&date_hidden=Date&page=", curr_page)

        events = sp.find_all('li', {'class': 'event'})
        
        for e in events:
            if e.find('time'):
                date_time = e.find('time')
                date_time = datetime.strptime(date_time.attrs['datetime'], '%Y-%m-%dT%H:%M:%SZ')
                date = date_time.date()
                time = date_time.time()

                title = e.find('div', {'class': 'title-subtitle'}).text
                venue = e.find('div', {'class': 'field--name-field-venue'}).text
                tags = e.find('div', {'class': 'field--name-field-event-tags'}).text.split('\n')
                
                while '' in tags:
                    tags.remove('')

                event = Event(date, time, title, venue, tags)
                results.append(event)

        curr_page += 1
        if not sp.find('a', {'class': 'button js-load-more'}):
            break
    
    return results

def insert_into_db(events):
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS events (date TEXT, time TEXT, title TEXT, venue TEXT, tags TEXT)')
    for e in events:
        c.execute('INSERT INTO events VALUES (?, ?, ?, ?, ?)', (e.date, e.time, e.title, e.venue, e.tags))
    conn.commit()
    conn.close()
        

if __name__ == '__main__':
    events = get_events()

    for event in events:
        print(event)


    
    
    