#!/usr/bin/env python
import discord

from data import CONSTANTS
from api.shinobu import Shinobu
from utils.setup_logging import setup_logging


if __name__ == '__main__':
    setup_logging()

    intents = discord.Intents.default()
    intents.members = True
    bot = Shinobu(command_prefix=CONSTANTS.CMD_PREFIX, intents=intents)

    with open('data/TOKEN') as f:
        token = f.readline().strip()
    bot.run(token)
