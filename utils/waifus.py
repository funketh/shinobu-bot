import random
import sqlite3
from dataclasses import dataclass
from typing import Tuple, Generator, List, Union

import discord
from fuzzywuzzy import process

from api.expected_errors import ExpectedCommandError
from utils.database import DB, Waifu, Pack, Character, User, Rarity


CURRENT_PREDICATE = "((pack.start_date <= CURRENT_DATE) " \
                    " AND (pack.end_date IS NULL OR pack.end_date >= CURRENT_DATE))"


class NotEnoughMoney(ExpectedCommandError): pass
class UnknownPackName(ExpectedCommandError): pass


@dataclass(frozen=True)
class Refund:
    amount: int


@dataclass(frozen=True)
class Upgrade:
    upgraded_rarity: Rarity


DuplicateType = Union[Refund, Upgrade, None]


async def buy_pack(db: DB, user_id: int, pack_name: str) -> Tuple[Waifu, DuplicateType]:
    with db:
        user = User.build(**db.execute('SELECT * FROM user WHERE id=?', [user_id]).fetchone())
        try:
            pack = Pack.build(**db.execute(f'SELECT * FROM pack WHERE '
                                           f'{CURRENT_PREDICATE} AND name LIKE ?', [pack_name]).fetchone())
        except TypeError:
            raise UnknownPackName(f"There's no pack named {pack_name}!")
        add_money(db, user.id, -pack.cost)
        character, rarity = pick_from_pack(db, pack.name)
        return give_waifu(db, user, character, rarity)


def add_money(db: DB, user_id: int, amount: int):
    try:
        db.execute('UPDATE user SET balance=balance+? WHERE id=?', [amount, user_id])
    except sqlite3.IntegrityError as e:
        raise NotEnoughMoney(f'<@{user_id}> does not have enough money!') from e


def pick_from_pack(db: DB, pack_name: str) -> Tuple[Character, Rarity]:
    rarity = pick_rarity(db)
    character = pick_character(db, pack_name, rarity.value)
    return character, rarity


def random_choice(*args, **kwargs):
    return (random.choices(*args, **kwargs))[0]


def pick_rarity(db: DB) -> Rarity:
    rarities = db.execute('SELECT * FROM rarity').fetchall()
    return Rarity.build(**random_choice(rarities, weights=(r['weight'] for r in rarities)))


def pick_character(db: DB, pack_name: str, rarity_val: int) -> Character:
    chars = [dict(c) for c in db.execute("""
    SELECT character.id, character.name, character.image_url,
           character.series, character.rarity AS 'rarity.value',
           character.batch AS 'batch.name',
           MAX(batch_in_pack.weight) AS __weight__ FROM character
    JOIN batch_in_pack      ON batch_in_pack.batch = character.batch
    JOIN rarity             ON rarity.value >= character.rarity
    WHERE batch_in_pack.pack = ? AND rarity.value = ?
    GROUP BY character.id
    """, [pack_name, rarity_val]).fetchall()]
    weights = [c.pop('__weight__') for c in chars]
    return Character.build(**random_choice(chars, weights=weights))


def give_waifu(db: DB, user: User, character: Character, new_rarity: Rarity) -> Tuple[Waifu, DuplicateType]:
    _old_waifu_row = db.execute("""
    SELECT waifu.id, waifu.rarity AS 'rarity.value',
           waifu.character AS 'character.id', waifu.user AS 'user.id'
    FROM waifu WHERE user=? AND character=?
    """, [user.id, character.id]).fetchone()
    waifu = Waifu.build(**_old_waifu_row) if _old_waifu_row else None

    if waifu is None:
        _waifu_id = db.execute('INSERT INTO waifu(user, character, rarity) VALUES(?, ?, ?)',
                               [user.id, character.id, new_rarity.value]).lastrowid
        waifu = Waifu.build(id=_waifu_id, character=character, rarity=new_rarity, user=user)
        duplicate = None
    elif waifu.rarity.value == new_rarity.value and new_rarity.auto_upgrade:
        new_rarity = Rarity.build(**db.execute('SELECT * FROM rarity WHERE value=?',
                                               [waifu.rarity.value + 1]).fetchone())
        db.execute('UPDATE waifu SET rarity=? WHERE id=?', [new_rarity.value, waifu.id])
        duplicate = Upgrade(new_rarity)
    else:
        waifu.rarity = Rarity.build(**db.execute('SELECT * FROM rarity WHERE value=?',
                                                 [waifu.rarity.value]).fetchone())
        lower, higher = sorted([new_rarity, waifu.rarity], key=lambda r: r.value)
        db.execute('UPDATE waifu SET rarity=? WHERE id=?', [higher.value, waifu.id])
        duplicate = Refund(lower.refund)
        add_money(db, user.id, duplicate.amount)

    waifu.rarity = new_rarity
    waifu.character = character
    waifu.user = user

    return waifu, duplicate


def find_waifu(*args, **kwargs) -> Waifu:
    try:
        return next(find_waifus(*args, **kwargs))
    except StopIteration as e:
        raise ExpectedCommandError("You don't have any waifus!") from e


def find_waifus(db: DB, user_id: int, query: str) -> Generator[Waifu, None, None]:
    waifus = list_waifus(db, user_id)
    matches = process.extract(query, (w.character.name for w in waifus), limit=None)
    for m in matches:
        for i, w in enumerate(waifus):
            if w.character.name == m[0]:
                found_i = i
                break
        else:
            continue
        yield waifus.pop(found_i)


def list_waifus(db: DB, user_id: int) -> List[Waifu]:
    return Waifu.from_rows(db.execute("""
    SELECT waifu.id, waifu.user, character.name AS "character.name", character.image_url AS "character.image_url",
           character.series AS "character.series", character.id AS "character.id",
           rarity.name AS "rarity.name", rarity.colour AS "rarity.colour", rarity.value AS "rarity.value",
           rarity.refund AS "rarity.refund", rarity.upgrade_cost AS "rarity.upgrade_cost",
           rarity.auto_upgrade AS "rarity.auto_upgrade"
    FROM waifu
    JOIN character ON character.id = waifu.character
    JOIN rarity ON rarity.value = waifu.rarity
    WHERE waifu.user=?
    ORDER BY rarity.value DESC, character.name ASC
    """, [user_id]).fetchall())


def waifu_embed(waifu: Waifu):
    embed = discord.Embed(color=waifu.rarity.colour, title=f'{waifu.character.name} [{waifu.character.series}]',
                          description=f"**{waifu.rarity.name}**")
    if waifu.character.image_url:
        embed.set_image(url=waifu.character.image_url)
    return embed
