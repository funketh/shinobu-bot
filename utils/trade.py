import asyncio
import sqlite3
from abc import abstractmethod
from collections import UserList, defaultdict, Callable, Coroutine
from dataclasses import dataclass
from functools import partial, wraps
from typing import Protocol, Final

import discord

from api.expected_errors import ExpectedCommandError
from api.my_context import Context
from data.CONSTANTS import CURRENCY
from utils.database import DB, Waifu

change_dataclass = partial(dataclass, frozen=True)


def add_money(db: DB, user_id: int, amount: int):
    try:
        db.execute('UPDATE user SET balance=balance+? WHERE id=?', [amount, user_id])
    except sqlite3.IntegrityError:
        raise ExpectedCommandError(f'<@{user_id}> does not have enough {CURRENCY}!')


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


CHANGES: Final[defaultdict[discord.User, LockedList]] = defaultdict(LockedList)


def forbid(func: Callable[..., Coroutine]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # TODO: use the appropriate locks in this and in @require
        ctx = args[0] if isinstance(args[0], Context) else args[1]
        if not CHANGES[ctx.author]:
            await func(*args, **kwargs)
        else:
            raise ExpectedCommandError("You can't do this while you're in a transaction!")

    return wrapper


def require(func: Callable[..., Coroutine]):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = args[0] if isinstance(args[0], Context) else args[1]
        if CHANGES[ctx.author]:
            await func(*args, **kwargs)
        else:
            raise ExpectedCommandError("You can only do this while you're in a transaction!")

    return wrapper
