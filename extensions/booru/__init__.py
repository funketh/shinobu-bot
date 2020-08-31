from api.shinobu import Shinobu
from .booru import Booru


def setup(bot: Shinobu):
    bot.add_cog(Booru())
