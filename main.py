import CONSTANTS
from shinobu import Shinobu
from utils.setup_logging import setup_logging

if __name__ == '__main__':
    setup_logging()
    bot = Shinobu(command_prefix=CONSTANTS.CMD_PREFIX)
    with open('TOKEN') as f:
        token = f.readline().strip()
    bot.run(token)
