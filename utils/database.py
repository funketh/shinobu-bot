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


class _Unavailable:
    def __getattribute__(self, name: str):
        raise AttributeError('Invalid Field Access!')


UNAVAILABLE = _Unavailable()

_T = TypeVar('_T')
NonObligatory = Union[_Unavailable, _T]
_RowDataT = TypeVar('_RowDataT', bound='RowData')

row_dataclass = partial(dataclass, unsafe_hash=True)


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
    name: NonObligatory[str] = UNAVAILABLE
    image_url: NonObligatory[Optional[str]] = UNAVAILABLE
    series: NonObligatory[str] = UNAVAILABLE
    rarity: NonObligatory[Rarity] = UNAVAILABLE
    batch: NonObligatory[Batch] = UNAVAILABLE


@row_dataclass
class Rarity(RowData):
    value: int
    name: NonObligatory[str] = UNAVAILABLE
    colour: NonObligatory[int] = UNAVAILABLE
    weight: NonObligatory[float] = UNAVAILABLE
    refund: NonObligatory[int] = UNAVAILABLE
    upgrade_cost: NonObligatory[Optional[int]] = UNAVAILABLE
    auto_upgrade: NonObligatory[bool] = UNAVAILABLE


@row_dataclass
class User(RowData):
    id: int
    balance: NonObligatory[int] = UNAVAILABLE
    last_withdrawal: NonObligatory[str] = UNAVAILABLE
    birthday: NonObligatory[str] = UNAVAILABLE
    mal_username: NonObligatory[str] = UNAVAILABLE


@row_dataclass
class Waifu(RowData):
    id: int
    character: NonObligatory[Character] = UNAVAILABLE
    rarity: NonObligatory[Rarity] = UNAVAILABLE
    user: NonObligatory[User] = UNAVAILABLE

    def to_embed(self) -> discord.Embed:
        embed = discord.Embed(color=self.rarity.colour,
                              title=f'{self.character.name} [{self.character.series}]',
                              description=f"**{self.rarity.name}**")
        if self.character.image_url:
            embed.set_image(url=self.character.image_url)
        return embed

    def ensure_ownership(self, db: DB):
        updated_waifu: Waifu = self.select_one(db, 'SELECT * FROM waifu WHERE id=? AND user=?', [self.id, self.user.id])
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
    cost: NonObligatory[int] = UNAVAILABLE
    description: NonObligatory[str] = UNAVAILABLE
    start_date: NonObligatory[str] = UNAVAILABLE
    end_date: NonObligatory[Optional[str]] = UNAVAILABLE


@row_dataclass
class Batch(RowData):
    name: NonObligatory[str] = UNAVAILABLE
