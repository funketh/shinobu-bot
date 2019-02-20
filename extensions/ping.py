from discord.ext import commands

from shinobu import Shinobu


@commands.command()
async def ping(ctx: commands.Context):
    await ctx.send('Pong!')


def setup(bot: Shinobu):
    cmds = (ping,)
    for cmd in cmds:
        bot.add_command(cmd)
