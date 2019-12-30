#!/usr/bin/env python
import sys

import csv

from utils import database


if __name__ == '__main__':
    with open(sys.argv[1], newline='') as tsvfile:
        new_chars = list(csv.DictReader(tsvfile, delimiter='\t'))
    db = database.connect()
    tmp = []
    for char in new_chars:
        char = {k: v.strip() for k, v in char.items()}
        try:
            char['id'] = int(char['id'])
        except ValueError:
            print(f'ERRONEOUS ENTRY: {char["name"]}')
        else:
            char['rarity'] = int(char['rarity'])
            char['url'] = char['url'] or None
            tmp.append(char)
    new_chars = tmp

    # Name conflicts
    new_names = []
    for c in new_chars:
        new_names.extend(c['name'].split())
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
        db.executemany('REPLACE INTO character(id, name, image_url, series, rarity) VALUES(?, ?, ?, ?, ?)',
                       [(c['id'], c['name'], c['url'], c['series'], c['rarity']) for c in new_chars])
        db.executemany('INSERT OR IGNORE INTO batch(name) VALUES(?)',
                       {(c['batch'],) for c in new_chars})
        batches = {b['name']: b['id'] for b in db.execute('SELECT name, id FROM batch')}
        db.executemany('INSERT OR IGNORE INTO character_in_batch(batch, character) VALUES(?, ?)',
                       [(batches[c['batch']], c['id']) for c in new_chars])
