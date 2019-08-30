from __future__ import annotations

import asyncio
import sqlite3
from collections import defaultdict, UserList

import discord
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from discord.ext import commands
from functools import wraps
from typing import List, Coroutine, Callable, DefaultDict

from api.my_context import Context
from api.shinobu import Shinobu
from data.CONSTANTS import CURRENCY
from utils import database
from utils.database import DB, Waifu
from utils.waifus import find_waifus


class ConstraintError(ValueError):
    pass


class Constraint:
    def __init__(self, condition, msg: str):
        if not condition:
            raise ConstraintError(msg)


class Change(ABC):
    @abstractmethod
    async def execute(self, db: DB): ...

    @abstractmethod
    def __str__(self): ...


class WaifuTransfer(Change):
    def __init__(self, db: DB, waifu: Waifu, old_owner_id: int, new_owner_id: int):
        Constraint(old_owner_id != new_owner_id, "You can't give something to yourself!")
        Constraint(db.execute('SELECT id FROM waifu WHERE user=? AND character=?',
                              [new_owner_id, waifu.character.id]).fetchone() is None,
                   "You can't give someone a waifu that he already owns")
        self.waifu = waifu
        self.old_owner_id = old_owner_id
        self.new_owner_id = new_owner_id

    async def execute(self, db: DB):
        db.execute('UPDATE waifu SET user=? WHERE id=?', [self.new_owner_id, self.waifu.id])

    def __str__(self):
        return f"<@{self.old_owner_id}> gives ***{self.waifu.rarity.name}*** **{self.waifu.character.name}** " \
            f"[{self.waifu.character.series}] to <@{self.new_owner_id}>"


class MoneyTransfer(Change):
    def __init__(self, db: DB, amount: int, from_id: int, to_id: int):
        Constraint(from_id != to_id, "You can't give something to yourself!")
        Constraint(amount <= db.execute('SELECT balance FROM user WHERE id=?').fetchone()[0],
                   "You don't have enough money for that!")
        self.amount = amount
        self.from_id = from_id
        self.to_id = to_id

    async def execute(self, db: DB):
        db.execute('UPDATE user SET balance=balance-? WHERE id=?', [self.amount, self.from_id])
        db.execute('UPDATE user SET balance=balance+? WHERE id=?', [self.amount, self.to_id])

    def __str__(self):
        return f"<@{self.from_id}> gives {self.amount} {CURRENCY} to <@{self.to_id}>"


class LockedList(UserList):
    def __init__(self, initlist=None):
        super().__init__(initlist)
        self.lock = asyncio.Lock()


_CHANGES: DefaultDict[discord.User, LockedList] = defaultdict(LockedList)


def forbid(func: Callable[..., Coroutine]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[0] if isinstance(args[0], Context) else args[1]
        if not _CHANGES[ctx.author]:
            return await func(*args, **kwargs)
        await ctx.error("You can't do this while you're in a transaction!")

    return wrapper


def require(func: Callable[..., Coroutine]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[0] if isinstance(args[0], Context) else args[1]
        if _CHANGES[ctx.author]:
            return await func(*args, **kwargs)
        await ctx.error("You can only do this while you're in a transaction!")

    return wrapper


class Transactions(commands.Cog):
    @commands.group(aliases=['t'], invoke_without_command=True)
    async def transaction(self, ctx: Context):
        """Trade anything with anyone"""
        await ctx.send_help(ctx.command)

    @transaction.command(aliases=['c'])
    @require
    async def cancel(self, ctx: Context):
        """Cancel your transaction."""
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.clear()
            await ctx.info(f"Cancelled {ctx.author.mention}'s transaction.")

    @transaction.command(aliases=['s'])
    @require
    async def sign(self, ctx: Context, *signers: discord.User):
        """Execute the transactions of every specified signer including yourself"""
        signers: List[discord.User] = list({ctx.author, *signers})
        async with AsyncExitStack() as stack:
            all_changes: List[Change] = []
            for s in signers:
                try:
                    change_list = _CHANGES[s]
                except KeyError:
                    return await ctx.error(f"{s} does not have an active transaction!")
                all_changes.extend(change_list)
                await stack.enter_async_context(change_list.lock)
            changes_str = '\n'.join(str(c) for c in all_changes)
            msg = await ctx.send(f"{', '.join(s.mention for s in signers)}: "
                                 f"Do you accept the following changes? (React with 👍 or 👎)\n"
                                 f"{changes_str}")
            if await ctx.confirm_multiuser(msg, signers):
                try:
                    with database.connect() as db:
                        for c in all_changes:
                            await c.execute(db)
                        for s in signers:
                            _CHANGES[s].clear()
                        await ctx.info("Successfully executed transaction.")
                except sqlite3.IntegrityError as e:
                    await ctx.bot.on_command_error(ctx, e)
            else:
                return await ctx.error("Cancelled execution! (Transaction contents are kept)")

    @transaction.command(aliases=['w'])
    async def waifu(self, ctx: Context, partner: discord.User, *search_terms):
        """Give one of your waifus to the specified user"""
        db = database.connect()
        try:
            waifu = next(find_waifus(db, ctx.author.id, ' '.join(search_terms)))
        except StopIteration:
            return await ctx.error("You don't have any waifus!")
        try:
            transfer = WaifuTransfer(db, waifu, ctx.author.id, partner.id)
        except ConstraintError as e:
            return await ctx.bot.on_command_error(ctx, e)
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.append(transfer)
        await ctx.info(f"Queued action: {transfer}")

    @transaction.command(aliases=['m'])
    async def money(self, ctx: Context, partner: discord.User, amount: int):
        """Give money to someone"""
        try:
            transfer = MoneyTransfer(database.connect(), amount, ctx.author.id, partner.id)
        except ConstraintError as e:
            return await ctx.bot.on_command_error(ctx, e)
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.append(transfer)
        await ctx.info(f"Queued action: {transfer}")


def setup(bot: Shinobu):
    bot.add_cog(Transactions())
