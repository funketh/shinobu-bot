from api.shinobu import Shinobu
from extensions.waifus.shop import WaifuShop
from extensions.waifus.transactions import Transactions


class Waifus(WaifuShop, Transactions):
    pass


def setup(bot: Shinobu):
    bot.add_cog(Waifus())
