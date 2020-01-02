#!/usr/bin/env python
from data import CONSTANTS
from api.shinobu import Shinobu
from utils.setup_logging import setup_logging

if __name__ == '__main__':
    setup_logging()
    bot = Shinobu(command_prefix=CONSTANTS.CMD_PREFIX)
    with open('data/TOKEN') as f:
        token = f.readline().strip()
    bot.run(token)
