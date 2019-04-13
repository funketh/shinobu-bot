import logging

import CONSTANTS
from shinobu import Shinobu

if __name__ == '__main__':
    logging.basicConfig(filename='logs/shinobu.log', level=logging.DEBUG)
    bot = Shinobu(command_prefix=CONSTANTS.CMD_PREFIX)
    with open('TOKEN') as f:
        token = f.readline().strip()
    bot.run(token)
