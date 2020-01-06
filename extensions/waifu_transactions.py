from __future__ import annotations

import asyncio
import sqlite3
from abc import abstractmethod
from collections import defaultdict, UserList
from contextlib import AsyncExitStack
from functools import wraps
from typing import List, Coroutine, Callable, DefaultDict, Protocol

import discord
from discord.ext import commands

from api.my_context import Context
from api.shinobu import Shinobu
from data.CONSTANTS import CURRENCY, FAKE_USER_ID
from utils import database
from utils.constrain import constrain
from utils.database import DB, Waifu
from utils.waifus import find_waifu, add_money


class Change(Protocol):
    async def pre_execute(self, db: DB): ...

    @abstractmethod
    async def execute(self, db: DB): ...

    @abstractmethod
    def __str__(self): ...


class WaifuTransfer(Change):
    def __init__(self, waifu: Waifu, old_owner_id: int, new_owner_id: int):
        constrain(old_owner_id != new_owner_id, "You can't give something to yourself!")
        self.waifu = waifu
        self.old_owner_id = old_owner_id
        self.new_owner_id = new_owner_id

    async def pre_execute(self, db: DB):
        db.execute('UPDATE waifu SET user=? WHERE id=?', [FAKE_USER_ID, self.waifu.id])

    async def execute(self, db: DB):
        try:
            db.execute('UPDATE waifu SET user=? WHERE id=?', [self.new_owner_id, self.waifu.id])
        except sqlite3.IntegrityError:
            raise ValueError("You can't give someone a waifu they already own!"
                             " (unless they give you their version of it simultaneously)")

    def __str__(self):
        return (
            f"<@{self.old_owner_id}> gives"
            f" ***{self.waifu.rarity.name}*** **{self.waifu.character.name}**"
            f" [{self.waifu.character.series}] to <@{self.new_owner_id}>"
        )


class MoneyTransfer(Change):
    def __init__(self, amount: int, from_id: int, to_id: int):
        constrain(from_id != to_id, "You can't give something to yourself!")
        constrain(amount > 0, f"You can only transfer positive amounts of {CURRENCY}!")
        self.amount = amount
        self.from_id = from_id
        self.to_id = to_id

    async def execute(self, db: DB):
        add_money(db, self.from_id, -self.amount)
        add_money(db, self.to_id, self.amount)

    def __str__(self):
        return f"<@{self.from_id}> gives {self.amount} {CURRENCY} to <@{self.to_id}>"


class LockedList(UserList):
    def __init__(self, initlist=None):
        super().__init__(initlist)
        self.lock = asyncio.Lock()


_CHANGES: DefaultDict[discord.User, LockedList[Change]] = defaultdict(LockedList)


def forbid(func: Callable[..., Coroutine]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[0] if isinstance(args[0], Context) else args[1]
        if not _CHANGES[ctx.author]:
            await func(*args, **kwargs)
        else:
            raise ValueError("You can't do this while you're in a transaction!")

    return wrapper


def require(func: Callable[..., Coroutine]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[0] if isinstance(args[0], Context) else args[1]
        if _CHANGES[ctx.author]:
            await func(*args, **kwargs)
        else:
            raise ValueError("You can only do this while you're in a transaction!")

    return wrapper


class Transactions(commands.Cog):
    def __init__(self):
        with database.connect() as db:
            db.execute('INSERT OR REPLACE INTO user(id) VALUES (?)', [FAKE_USER_ID])

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
            for s in signers:
                await stack.enter_async_context(_CHANGES[s])
            all_changes: List[Change] = [c for s in signers for c in _CHANGES[s]]
            changes_str = '\n'.join(str(c) for c in all_changes)
            msg = await ctx.send(f"{', '.join(s.mention for s in signers)}: "
                                 f"Do you accept the following changes?\n{changes_str}")
            if await ctx.confirm_multiuser(msg, signers):
                with database.connect() as db:
                    for c in all_changes:
                        await c.pre_execute(db)
                    for c in all_changes:
                        await c.execute(db)
                    for s in signers:
                        del _CHANGES[s]
                    await ctx.info("Successfully executed transaction.")
            else:
                return await ctx.error("Cancelled execution! (Transaction contents are kept)")

    @transaction.command(aliases=['w'])
    async def waifu(self, ctx: Context, partner: discord.User, *search_terms):
        """Give one of your waifus to the specified user"""
        db = database.connect()
        waifu = find_waifu(db, ctx.author.id, ' '.join(search_terms))
        transfer = WaifuTransfer(waifu=waifu, old_owner_id=ctx.author.id, new_owner_id=partner.id)
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.append(transfer)
        await ctx.info(f"Queued action: {transfer}")

    @transaction.command(aliases=['m'])
    async def money(self, ctx: Context, partner: discord.User, amount: int):
        """Give money to someone"""
        transfer = MoneyTransfer(amount=amount, from_id=ctx.author.id, to_id=partner.id)
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.append(transfer)
        await ctx.info(f"Queued action: {transfer}")


def setup(bot: Shinobu):
    bot.add_cog(Transactions())
