import sqlite3

import logging

from CONSTANTS import DB_PATH
from shinobu import Shinobu

if __name__ == '__main__':
    logging.basicConfig(filename='example.log', level=logging.DEBUG)
    with sqlite3.connect(DB_PATH) as db:
        prefix, token = db.execute('SELECT command_prefix, token FROM config').fetchone()
    bot = Shinobu(command_prefix=prefix)
    bot.run(token)
