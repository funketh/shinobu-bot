import importlib
import inspect
import io
import os
import re
from glob import iglob

import discord
from discord.ext import commands

from api.my_context import Context
from api.shinobu import Shinobu
from utils.constrain import constrain


def import_from_str(import_instruction: str) -> object:
    invalid_obj_msg = f'Invalid object path: {import_instruction}'
    constrain(not re.search(r'[^-_.A-Za-z0-9]', import_instruction),
              invalid_obj_msg)
    path = import_instruction.split('.')
    current_dir = os.getcwd()
    for i, p in enumerate(path):
        as_subdir = current_dir + '/' + p + '/'
        if next(iglob(as_subdir), None):
            current_dir = as_subdir
            continue
        if next(iglob(current_dir + '/' + p + '.py'), None):
            i += 1
            break
        raise ValueError(invalid_obj_msg)
    else:
        raise ValueError(invalid_obj_msg)
    namespace = importlib.import_module('.'.join(path[:i]))
    for p in path[i:]:
        try:
            namespace = getattr(namespace, p)
        except AttributeError:
            raise ValueError(invalid_obj_msg)
    return namespace


class PrintSource(commands.Cog):
    @commands.group(aliases=['s'], invoke_without_command=True)
    async def source(self, ctx: Context):
        """Get the source code of this bot"""
        await ctx.send_help(ctx.command)

    @source.command(aliases=['f'])
    async def file(self, ctx: Context, path: import_from_str):
        """Get the source code of a specified object as a file"""
        await ctx.send(file=discord.File(io.StringIO(inspect.getsource(path)), filename=path.__name__ + '.py'))

    @source.command(name='print', aliases=['p'])
    async def print_(self, ctx: Context, path: import_from_str):
        """Print the source code of a specified object"""
        await ctx.send_paginated(inspect.getsource(path), prefix='```py\n', suffix='\n```')


def setup(bot: Shinobu):
    bot.add_cog(PrintSource())
