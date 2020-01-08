from __future__ import annotations

import asyncio
import sqlite3
from abc import abstractmethod
from collections import defaultdict, UserList
from contextlib import AsyncExitStack
from functools import wraps
from typing import List, Coroutine, Callable, DefaultDict, Protocol, Set

import discord
from discord.ext import commands

from api.my_context import Context
from data.CONSTANTS import CURRENCY
from utils import database
from utils.constrain import constrain
from utils.database import DB, Waifu
from utils.waifus import find_waifu, add_money


class Change(Protocol):
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

    async def execute(self, db: DB):
        try:
            db.execute('UPDATE waifu SET user=? WHERE id=?', [self.new_owner_id, self.waifu.id])
        except sqlite3.IntegrityError:
            raise ValueError("You can't give someone a waifu they already own!")

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
    @commands.group(aliases=['t'], invoke_without_command=True)
    async def transaction(self, ctx: Context):
        """Trade anything with anyone"""
        await ctx.send_help(ctx.command)

    @transaction.command(name='cancel', aliases=['c'])
    @require
    async def transaction_cancel(self, ctx: Context):
        """Cancel your transaction."""
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.clear()
            await ctx.info(f"Cancelled {ctx.author.mention}'s transaction.")

    @transaction.command(name='waifu', aliases=['w'])
    async def transaction_waifu(self, ctx: Context, partner: discord.User, *search_terms):
        """Give one of your waifus to the specified user"""
        db = database.connect()
        waifu = find_waifu(db, ctx.author.id, ' '.join(search_terms))
        transfer = WaifuTransfer(waifu=waifu, old_owner_id=ctx.author.id, new_owner_id=partner.id)
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.append(transfer)
        await ctx.info(f"Queued action: {transfer}")

    @transaction.command(name='money', aliases=['m'])
    async def transaction_money(self, ctx: Context, partner: discord.User, amount: int):
        """Give money to someone"""
        transfer = MoneyTransfer(amount=amount, from_id=ctx.author.id, to_id=partner.id)
        change_list = _CHANGES[ctx.author]
        async with change_list.lock:
            change_list.append(transfer)
        await ctx.info(f"Queued action: {transfer}")

    @transaction.command(name='sign', aliases=['s'])
    @require
    async def transaction_sign(self, ctx: Context, *signers: discord.User):
        """Execute the transactions of every specified signer including yourself"""
        signers: Set[discord.User] = {ctx.author, *signers}
        async with AsyncExitStack() as stack:
            for s in signers:
                await stack.enter_async_context(_CHANGES[s].lock)
            all_changes: List[Change] = [c for s in signers for c in _CHANGES[s]]
            changes_str = '\n'.join(str(c) for c in all_changes)
            msg = await ctx.send(f"{', '.join(s.mention for s in signers)}: "
                                 f"Do you accept the following changes?\n{changes_str}")
            if await ctx.confirm_multiuser(msg, list(signers)):
                with database.connect() as db:
                    for c in all_changes:
                        await c.execute(db)
                    for s in signers:
                        _CHANGES[s].clear()
                    await ctx.info("Successfully executed transaction.")
            else:
                return await ctx.error("Cancelled execution! (Transaction contents are kept)")
