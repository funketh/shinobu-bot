#!/usr/bin/env python
import csv
import sys
from typing import NamedTuple

from utils import database


Char = NamedTuple('Char', id=int, name=str, image_url=str, series=str, rarity=int, batch=str)
CHAR_ATTR_ORDER = 'id, name, image_url, series, rarity, batch'
def throw(): raise ValueError


if __name__ == '__main__':
    with open(sys.argv[1], newline='') as tsvfile:
        raw_char_rows = list(csv.DictReader(tsvfile, delimiter='\t'))

    # Figure out which column contains the ids
    id_key_candidates = [k for k in raw_char_rows[0].keys() if k.startswith('id')]
    if len(id_key_candidates) > 1:
        raise ValueError('Multiple columns could be the id!')
    if len(id_key_candidates) == 0:
        raise ValueError('No column looks like it contains the ids (none of them start with "id")!')
    id_key = id_key_candidates[0]

    # Sanitize the raw data into proper data types and check its validity
    chars = []
    for row in raw_char_rows:
        try:
            chars.append(Char(id=int(row[id_key].strip()),
                              name=row['name'].strip() or throw(),
                              image_url=row['image_url'].strip() or None,
                              series=row['series'].strip() or throw(),
                              rarity=int(row['rarity'].strip()),
                              batch=row['batch'].strip() or throw()))
        except Exception as e:
            raise ValueError(f'ERRONEOUS ENTRY: {row}') from e

    # Insert Data
    with database.connect() as db:
        db.executemany(f'REPLACE INTO character({CHAR_ATTR_ORDER}) VALUES(?,?,?,?,?,?)', chars)
        db.executemany('INSERT OR IGNORE INTO batch(name) VALUES(?)', {(c.batch,) for c in chars})
