import sqlite3

from CONSTANTS import DB_PATH

def connect(db_path=DB_PATH) -> sqlite3.Connection:
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db
