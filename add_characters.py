import sys

import csv
from typing import Optional

from utils import database


def format_name(*, forename: Optional[str], surname: Optional[str],
                nickname: Optional[str], **kwargs):
    only_if = lambda cond, val: val if cond else ''
    return (''
            + only_if(forename, f'{forename} ')
            + only_if(nickname, f'"{nickname}" ')
            + only_if(surname, f'{surname}'))


if __name__ == '__main__':
    with open(sys.argv[1], newline='') as csvfile:
        new_chars = list(csv.DictReader(csvfile, delimiter=','))
    db = database.connect()
    highest_id = db.execute('SELECT MAX(id) FROM character').fetchone()[0] or 0
    for i, char in enumerate(new_chars):
        char['id'] = highest_id + i + 1
        char['url'] = char['url'] or None
        char['rarity'] = char['rarity'] or 1

    # Name conflicts
    new_names = {name for sublist in
                 ((w['forename'], w['surname'], w['nickname']) for w in new_chars)
                 for name in sublist}
    conflicts = list(filter(lambda c: filter(lambda n: n in new_names,
                                             c['name'].split()),
                            db.execute('SELECT * FROM character').fetchall()))
    if conflicts:
        print('Potential Conflicts:')
        for conflict in conflicts:
            for attr in conflict:
                print(attr, end='|')
            print()
        assert input('Proceed anyway? [y/n] ').lower() == 'y'
    # Insert Data
    with db:
        db.executemany('REPLACE INTO character(id, name, image_url, series, min_rarity) VALUES(?, ?, ?, ?, ?)',
                       [[c['id'],
                         format_name(**c),
                         c['url'],
                         c['series'],
                         c['rarity']]
                        for c in new_chars])
        db.executemany('INSERT OR IGNORE INTO batch(name) VALUES(?)',
                       {(c['batch'],) for c in new_chars})
        batches = {b['name']: b['id'] for b in db.execute('SELECT name, id FROM batch')}
        db.executemany('INSERT INTO character_in_batch(batch, character) VALUES(?, ?)',
                       [(batches[c['batch']], c['id']) for c in new_chars])
