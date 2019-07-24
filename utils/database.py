from __future__ import annotations

import sqlite3
from collections import defaultdict

from dataclasses import dataclass
from typing import Optional, Union, TypeVar, Type, Any, DefaultDict, Dict, Generator, List

from data.CONSTANTS import DB_PATH

DB = sqlite3.Connection


def connect(db_path=DB_PATH) -> DB:
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    return db


class _UnavailableMeta(type):
    def __getattribute__(self, name: str):
        raise AttributeError('Invalid Field Access!')


class Unavailable(metaclass=_UnavailableMeta): pass


T = TypeVar('T')
NonObligatory = Union[Type[Unavailable], T]


def nested_dict() -> DefaultDict:
    return defaultdict(nested_dict)


@dataclass
class RowData:
    @classmethod
    def _get_subclasses(cls: Type[RowData]) -> Generator[Type[RowData], None, None]:
        for subclass in cls.__subclasses__():
            yield from subclass._get_subclasses()
            yield subclass

    @classmethod
    def _find_subclass(cls: Type[RowData], name: str) -> Optional[Type[RowData]]:
        for subclass in cls._get_subclasses():
            if subclass.__name__ == name:
                return subclass

    @classmethod
    def _from_tree(cls: Type[RowData], tree: Dict[str, Any]) -> RowData:
        for key, value in tree.copy().items():
            if isinstance(value, dict):
                try:
                    tree[key] = RowData._find_subclass(key.capitalize())._from_tree(value)
                except AttributeError:
                    raise ValueError('invalid tree')
        return cls(**tree)

    @classmethod
    def build(cls: Type[RowData], **kwargs) -> RowData:
        tree: DefaultDict[str, Any] = nested_dict()
        for name, value in kwargs.items():
            subnames = name.split('.')
            subtree = tree
            for subtree_name in subnames[:-1]:
                subtree = subtree[subtree_name]
            subtree[subnames[-1]] = value
        return cls._from_tree(tree)

    @classmethod
    def from_rows(cls: Type[RowData], rows: List[sqlite3.Row]):
        return [cls.build(**r) for r in rows]


@dataclass
class Character(RowData):
    id: int
    name: NonObligatory[str] = Unavailable
    image_url: NonObligatory[Optional[str]] = Unavailable
    series: NonObligatory[str] = Unavailable
    min_rarity: NonObligatory[int] = Unavailable


@dataclass
class Rarity(RowData):
    value: int
    name: NonObligatory[str] = Unavailable
    colour: NonObligatory[int] = Unavailable
    weight: NonObligatory[float] = Unavailable


@dataclass
class User(RowData):
    id: int
    balance: NonObligatory[int] = Unavailable
    income: NonObligatory[int] = Unavailable
    birthday: NonObligatory[str] = Unavailable


@dataclass
class Waifu(RowData):
    id: int
    character: NonObligatory[Character] = Unavailable
    rarity: NonObligatory[Rarity] = Unavailable
    user: NonObligatory[User] = Unavailable


@dataclass
class Pack(RowData):
    id: int
    name: NonObligatory[str] = Unavailable
    cost: NonObligatory[int] = Unavailable
    description: NonObligatory[str] = Unavailable
    start_date: NonObligatory[str] = Unavailable
    end_date: NonObligatory[Optional[str]] = Unavailable


@dataclass
class Batch(RowData):
    id: int
    name: NonObligatory[str] = Unavailable
