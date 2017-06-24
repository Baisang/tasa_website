import sqlite3
import sys

POSITIONS = [
    'President',
    'Internal Vice President',
    'External Vice President',
    'Treasurer',
    'Webmaster',
    'Outreach',
    'Public Relations',
    'Family Head',
    'Historian',
    'Senior Advisor',
    'Family Head Intern',
    'Historian Intern',
    'Public Relations Intern',
    'Outreach Intern',
    'Treasurer Intern',
    'Webmaster Intern',
]

def connect_db():
    return sqlite3.connect('tasa_website/tasa_website.db')

def get_officers(db):
    return query_db(db, 'select * from officers;')

def query_db(db, query, args=(), one=False):
    cur = db.execute(query, args)
    rv = cur.fetchall()
    db.commit()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def main():
    db = connect_db()
    db.row_factory = sqlite3.Row
    officers = get_officers(db)
    for officer in officers:
        if officer['position'] == 'EVP':
            officer['position'] = 'External Vice President'
        elif officer['position'] == 'IVP':
            officer['position'] = 'Internal Vice President'
        new_position = POSITIONS.index(officer['position'])
        query = 'insert into officers (name, year, major, quote, description, image_url, position, href)'\
                'values (?, ?, ?, ?, ?, ?, ?, ?)'
        query_db(db, query, [
            officer['name'],
            officer['year'],
            officer['major'],
            officer['quote'],
            officer['description'],
            officer['image_url'],
            new_position,
            officer['href'],
        ])

if __name__ == '__main__':
    sys.exit(main())
