from api.shinobu import Shinobu
from extensions.waifus.shop import WaifuShop
from extensions.waifus.trade import Trade


class Waifus(WaifuShop, Trade):
    pass


def setup(bot: Shinobu):
    bot.add_cog(Waifus())
