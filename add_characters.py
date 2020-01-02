#!/usr/bin/env python
import sys

import csv

from utils import database


if __name__ == '__main__':
    with open(sys.argv[1], newline='') as tsvfile:
        new_chars = list(csv.DictReader(tsvfile, delimiter='\t'))
    db = database.connect()
    id_key = [k for k in new_chars[0].keys() if k.startswith('id')][0]
    tmp = []
    for char in new_chars:
        char = {k: v.strip() for k, v in char.items()}
        try:
            char['id'] = int(char[id_key])
            del char[id_key]
        except ValueError:
            print(f'ERRONEOUS ENTRY: {char["name"]}')
        else:
            char['rarity'] = int(char['rarity'])
            char['image_url'] = char['image_url'] or None
            tmp.append(char)
    new_chars = tmp

    assert input('Proceed? [y/n] ').lower() == 'y'

    # Insert Data
    with db:
        db.executemany('REPLACE INTO character(id, name, image_url, series, rarity, batch) VALUES(?, ?, ?, ?, ?, ?)',
                       [(c['id'], c['name'], c['image_url'], c['series'], c['rarity'], c['batch']) for c in new_chars])
        db.executemany('INSERT OR IGNORE INTO batch(name) VALUES(?)',
                       {(c['batch'],) for c in new_chars})
