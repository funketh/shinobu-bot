import sqlite3

from CONSTANTS import DB_PATH

DB = sqlite3.Connection


def connect(db_path=DB_PATH) -> DB:
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db
