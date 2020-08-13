from __future__ import annotations

import asyncio
import sqlite3
from abc import abstractmethod
from collections import defaultdict, UserList
from contextlib import AsyncExitStack
from dataclasses import dataclass
from functools import wraps, partial
from typing import List, Coroutine, Callable, DefaultDict, Protocol, Set

import discord
from discord.ext import commands

from api.expected_errors import ExpectedCommandError
from api.my_context import Context
from api.shinobu import Shinobu
from data.CONSTANTS import CURRENCY
from utils import database
from utils.database import DB, Waifu
from utils.waifus import add_money

change_dataclass = partial(dataclass, frozen=True)


@change_dataclass
class Change(Protocol):
    from_id: int
    to_id: int

    def __post_init__(self):
        if self.from_id == self.to_id:
            raise ExpectedCommandError("You can't give something to yourself!")

    @abstractmethod
    async def execute(self, db: DB): ...

    @abstractmethod
    def __str__(self): ...


@change_dataclass
class WaifuTransfer(Change):
    waifu: Waifu

    async def execute(self, db: DB):
        try:
            db.execute('UPDATE waifu SET user=? WHERE id=?', [self.to_id, self.waifu.id])
        except sqlite3.IntegrityError:
            raise ExpectedCommandError("You can't give someone a waifu they already own!")

    def __str__(self):
        return (f"<@{self.from_id}> gives"
                f" ***{self.waifu.rarity.name}*** **{self.waifu.character.name}**"
                f" [{self.waifu.character.series}] to <@{self.to_id}>")


@change_dataclass
class MoneyTransfer(Change):
    amount: int

    def __post_init__(self):
        super().__post_init__()
        if self.amount <= 0:
            raise ExpectedCommandError(f"You can only transfer positive amounts of {CURRENCY}!")

    async def execute(self, db: DB):
        with db:
            add_money(db, self.from_id, -self.amount)
            add_money(db, self.to_id, self.amount)

    def __str__(self):
        return f"<@{self.from_id}> gives {self.amount} {CURRENCY} to <@{self.to_id}>"


class LockedList(UserList):
    def __init__(self, initlist=None):
        # TODO: enforce locking
        super().__init__(initlist)
        self.lock = asyncio.Lock()


_CHANGES: DefaultDict[discord.User, LockedList[Change]] = defaultdict(LockedList)


def forbid(func: Callable[..., Coroutine]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # TODO: use the appropriate locks in this and in @require
        ctx = args[0] if isinstance(args[0], Context) else args[1]
        if not _CHANGES[ctx.author]:
            await func(*args, **kwargs)
        else:
            raise ExpectedCommandError("You can't do this while you're in a transaction!")

    return wrapper


def require(func: Callable[..., Coroutine]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[0] if isinstance(args[0], Context) else args[1]
        if _CHANGES[ctx.author]:
            await func(*args, **kwargs)
        else:
            raise ExpectedCommandError("You can only do this while you're in a transaction!")

    return wrapper


class Trade(commands.Cog):
    @commands.group(aliases=['t'], invoke_without_command=True)
    async def trade(self, ctx: Context):
        """Trade anything with anyone"""
        await ctx.send_help(ctx.command)

    @trade.command(name='cancel', aliases=['c'])
    @require
    async def trade_cancel(self, ctx: Context):
        """Cancel your transaction."""
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.clear()
            await ctx.info(f"Cancelled {ctx.author.mention}'s transaction.")

    @trade.command(name='money', aliases=['m'])
    async def trade_money(self, ctx: Context, partner: discord.User, amount: int):
        """Give money to someone"""
        transfer = MoneyTransfer(from_id=ctx.author.id, to_id=partner.id, amount=amount)
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.append(transfer)
        await ctx.info(f"Queued action: {transfer}")

    @trade.command(name='sign', aliases=['s'])
    @require
    async def trade_sign(self, ctx: Context, *signers: discord.User):
        """Execute the transactions of every specified signer including yourself"""
        signers: Set[discord.User] = {ctx.author, *signers}
        async with AsyncExitStack() as stack:
            for s in signers:
                await stack.enter_async_context(_CHANGES[s].lock)
            all_changes: List[Change] = [c for s in signers for c in _CHANGES[s]]
            changes_str = '\n'.join(str(c) for c in all_changes)
            mention_str = ', '.join(s.mention for s in signers)
            msg = await ctx.send(f"{mention_str}: Do you accept the following changes?\n{changes_str}")
            if await ctx.confirm(msg, users=signers):
                with database.connect() as db:
                    for c in all_changes:
                        await c.execute(db)
                    for s in signers:
                        _CHANGES[s].clear()
                    await ctx.info("Successfully executed transaction.")
            else:
                raise ExpectedCommandError("Cancelled execution! (Transaction contents are kept)")


def setup(bot: Shinobu):
    bot.add_cog(Trade())
