from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from typing import Optional, Union, TypeVar, Type, Any, DefaultDict, Dict, Generator, Iterator

import discord

from api.expected_errors import ExpectedCommandError
from data.CONSTANTS import DB_PATH

DB = sqlite3.Connection


def connect(db_path=DB_PATH) -> DB:
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db


def nested_dict() -> DefaultDict:
    return defaultdict(nested_dict)


class _UnavailableMeta(type):
    def __getattribute__(self, name: str):
        raise AttributeError('Invalid Field Access!')


class Unavailable(metaclass=_UnavailableMeta): pass


_T = TypeVar('_T')
NonObligatory = Union[Type[Unavailable], _T]

row_dataclass = partial(dataclass, unsafe_hash=True)

_RowDataT = TypeVar('_RowDataT', bound='RowData')


@row_dataclass
class RowData:
    @classmethod
    def _get_subclasses(cls) -> Generator[Type[_RowDataT], None, None]:
        for subclass in cls.__subclasses__():
            yield from subclass._get_subclasses()
            yield subclass

    @classmethod
    def _find_subclass(cls, name: str) -> Optional[Type[_RowDataT]]:
        for subclass in cls._get_subclasses():
            if subclass.__name__ == name:
                return subclass

    @classmethod
    def _from_tree(cls, tree: Dict[str, Any]) -> _RowDataT:
        for key, value in tree.copy().items():
            if isinstance(value, dict):
                try:
                    tree[key] = RowData._find_subclass(key.capitalize())._from_tree(value)
                except AttributeError:
                    raise ValueError('invalid tree')
        return cls(**tree)

    @classmethod
    def build(cls, **kwargs) -> _RowDataT:
        tree: DefaultDict[str, Any] = nested_dict()
        for name, value in kwargs.items():
            subnames = name.split('.')
            subtree = tree
            for subtree_name in subnames[:-1]:
                subtree = subtree[subtree_name]
            subtree[subnames[-1]] = value
        return cls._from_tree(tree)

    @classmethod
    def select_one(cls, db: DB, *args, **kwargs) -> _RowDataT:
        if row := db.execute(*args, **kwargs).fetchone():
            return cls.build(**row)

    @classmethod
    def select_many(cls, db: DB, *args, **kwargs) -> Iterator[_RowDataT]:
        for row in db.execute(*args, **kwargs):
            yield cls.build(**row)


@row_dataclass
class Character(RowData):
    id: int
    name: NonObligatory[str] = Unavailable
    image_url: NonObligatory[Optional[str]] = Unavailable
    series: NonObligatory[str] = Unavailable
    rarity: NonObligatory[Rarity] = Unavailable
    batch: NonObligatory[Batch] = Unavailable


@row_dataclass
class Rarity(RowData):
    value: int
    name: NonObligatory[str] = Unavailable
    colour: NonObligatory[int] = Unavailable
    weight: NonObligatory[float] = Unavailable
    refund: NonObligatory[int] = Unavailable
    upgrade_cost: NonObligatory[Optional[int]] = Unavailable
    auto_upgrade: NonObligatory[bool] = Unavailable


@row_dataclass
class User(RowData):
    id: int
    balance: NonObligatory[int] = Unavailable
    last_withdrawal: NonObligatory[str] = Unavailable
    birthday: NonObligatory[str] = Unavailable
    mal_username: NonObligatory[str] = Unavailable


@row_dataclass
class Waifu(RowData):
    id: int
    character: NonObligatory[Character] = Unavailable
    rarity: NonObligatory[Rarity] = Unavailable
    user: NonObligatory[User] = Unavailable

    def to_embed(self) -> discord.Embed:
        embed = discord.Embed(color=self.rarity.colour,
                              title=f'{self.character.name} [{self.character.series}]',
                              description=f"**{self.rarity.name}**")
        if self.character.image_url:
            embed.set_image(url=self.character.image_url)
        return embed

    def ensure_ownership(self, db: DB):
        updated_waifu = self.select_one(db, 'SELECT * FROM waifu WHERE id=? AND user=?', [self.id, self.user.id])
        if updated_waifu is None:
            raise ExpectedCommandError(f"You no longer own {self.character.name}!")
        elif (updated_waifu.id != self.id
              or updated_waifu.character != self.character.id
              or updated_waifu.rarity != self.rarity.value
              or updated_waifu.user != self.user.id):  # TODO: use updated_waifu != self
            raise ExpectedCommandError(f"Your {self.character.name} has changed!")


@row_dataclass
class Pack(RowData):
    name: str
    cost: NonObligatory[int] = Unavailable
    description: NonObligatory[str] = Unavailable
    start_date: NonObligatory[str] = Unavailable
    end_date: NonObligatory[Optional[str]] = Unavailable


@row_dataclass
class Batch(RowData):
    name: NonObligatory[str] = Unavailable
