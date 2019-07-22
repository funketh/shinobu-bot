import math
import sqlite3

import discord
import random
from fuzzywuzzy import process

from utils.database import DB
from typing import Tuple, Optional, NamedTuple, Generator, List


CURRENT_PREDICATE = "((pack.start_date <= CURRENT_DATE) " \
                    " AND (pack.end_date IS NULL OR pack.end_date >= CURRENT_DATE))"


class NotEnoughMoney(BaseException): pass


class UnknownPackName(BaseException): pass


class Receipt(NamedTuple):
    character: sqlite3.Row
    rarity: sqlite3.Row
    old_rarity: Optional[sqlite3.Row]
    pack: sqlite3.Row
    refund: int


async def buy_pack(db: DB, user_id: int, pack_name: str) -> Receipt:
    with db:
        pack = db.execute(f'SELECT * FROM pack WHERE {CURRENT_PREDICATE} AND name LIKE ?', [pack_name]).fetchone()
        if pack is None:
            raise UnknownPackName
        add_money(db, user_id, -pack['cost'])
        char, rarity = pick_from_pack(db, pack['id'])
        old_rarity = give_waifu(db, user_id, char['id'], rarity['value'])
        refund_amount: int = 0
        if old_rarity is not None:
            refunded_rarity_val = min(rarity['value'], old_rarity['value'])
            refund_amount = refund(db, user_id, refunded_rarity_val, pack['cost'])
        return Receipt(character=char, rarity=rarity, old_rarity=old_rarity, pack=pack, refund=refund_amount)


def add_money(db: DB, user_id: int, amount: int):
    try:
        db.execute('UPDATE user SET balance=balance+? WHERE id=?', [amount, user_id])
    except sqlite3.IntegrityError:
        raise NotEnoughMoney


def pick_from_pack(db: DB, pack_id: int) -> Tuple[sqlite3.Row, sqlite3.Row]:
    rarity = pick_rarity(db)
    char = pick_character(db, pack_id, rarity['value'])
    return char, rarity


def random_choice(*args, **kwargs):
    return (random.choices(*args, **kwargs))[0]


def pick_rarity(db: DB) -> sqlite3.Row:
    rarities = db.execute('SELECT * FROM rarity').fetchall()
    return random_choice(rarities, weights=(r['weight'] for r in rarities))


def pick_character(db: DB, pack_id: int, rarity_val: int) -> sqlite3.Row:
    chars = db.execute("""
    SELECT character.*, MAX(batch_in_pack.weight) AS weight FROM character
    JOIN character_in_batch   ON character_in_batch.character = character.id
    JOIN batch              ON batch.id = character_in_batch.batch
    JOIN batch_in_pack      ON batch_in_pack.batch = batch.id
    JOIN rarity             ON rarity.value >= character.min_rarity
    WHERE batch_in_pack.pack = ? AND rarity.value = ?
    GROUP BY character.id
    """, [pack_id, rarity_val]).fetchall()
    return random_choice(chars, weights=(v['weight'] for v in chars))


def give_waifu(db: DB, user_id: int, char_id: int, new_rarity_val: int) -> Optional[sqlite3.Row]:
    old_rarity = db.execute('''SELECT rarity.* FROM waifu
                               JOIN rarity ON rarity.value=waifu.rarity
                               WHERE user=? AND character=?''',
                            [user_id, char_id]).fetchone()
    if old_rarity is None or old_rarity['value'] < new_rarity_val:
        db.execute('REPLACE INTO waifu(user, character, rarity) VALUES(?, ?, ?)',
                   [user_id, char_id, new_rarity_val])
    return old_rarity


def refund(db: DB, user_id: int, rarity_val: int, cost: int) -> int:
    amount = math.ceil(db.execute("""
    SELECT ? * CAST(value AS FLOAT) / (SELECT MAX(value) FROM rarity)
    AS amount FROM rarity WHERE value=?
    """, [cost, rarity_val]).fetchone()[0])
    add_money(db, user_id, amount)
    return amount


def find_waifus(db: DB, user_id: int, query: str) -> Generator[sqlite3.Row, None, None]:
    waifus = list_waifus(db, user_id)
    matches = process.extract(query, (w['name'] for w in waifus), limit=None)
    for m in matches:
        for i, w in enumerate(waifus):
            if w['name'] == m[0]:
                found_i = i
                break
        else:
            continue
        yield waifus.pop(found_i)


def list_waifus(db: DB, user_id: int) -> List[sqlite3.Row]:
    return db.execute("""
    SELECT waifu.id AS "waifu.id",
           character.name, character.image_url, character.series, character.id AS "character.id",
           rarity.name AS "rarity.name", rarity.colour AS "rarity.colour", rarity.value AS "rarity.value"
    FROM waifu
    JOIN character ON character.id = waifu.character
    JOIN rarity ON rarity.value = waifu.rarity
    WHERE waifu.user=?
    ORDER BY rarity.value DESC, character.name ASC
    """, [user_id]).fetchall()


def waifu_embed(name, series, image_url, rarity_name, rarity_color):
    embed = discord.Embed(color=rarity_color, title=f'{name} [{series}]',
                          description=f"**{rarity_name}**")
    if image_url:
        embed.set_image(url=image_url)
    return embed
