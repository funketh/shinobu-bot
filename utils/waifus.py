import math
import sqlite3

import discord
import random
from fuzzywuzzy import process
from typing import Tuple, Optional, Generator, List

from utils.database import DB, Waifu, Pack, Character, User, Rarity

CURRENT_PREDICATE = "((pack.start_date <= CURRENT_DATE) " \
                    " AND (pack.end_date IS NULL OR pack.end_date >= CURRENT_DATE))"


class NotEnoughMoney(BaseException): pass


class UnknownPackName(BaseException): pass


async def buy_pack(db: DB, user_id: int, pack_name: str) -> Tuple[Waifu, Optional[int], int]:
    with db:
        user = User.build(**db.execute('SELECT * FROM user WHERE id=?', [user_id]).fetchone())
        try:
            pack = Pack.build(**db.execute(f'SELECT * FROM pack WHERE '
                                           f'{CURRENT_PREDICATE} AND name LIKE ?', [pack_name]).fetchone())
        except AttributeError:
            raise UnknownPackName
        add_money(db, user.id, -pack.cost)
        character, rarity = pick_from_pack(db, pack.id)
        waifu, old_rarity_val = give_waifu(db, user, character, rarity)
        refund_amount: int = 0
        if old_rarity_val is not None:
            refunded_rarity_val = min(rarity.value, old_rarity_val)
            refund_amount = refund(db, user_id, refunded_rarity_val, pack.cost)
        return waifu, old_rarity_val, refund_amount


def add_money(db: DB, user_id: int, amount: int):
    try:
        db.execute('UPDATE user SET balance=balance+? WHERE id=?', [amount, user_id])
    except sqlite3.IntegrityError:
        raise NotEnoughMoney


def pick_from_pack(db: DB, pack_id: int) -> Tuple[Character, Rarity]:
    rarity = pick_rarity(db)
    character = pick_character(db, pack_id, rarity.value)
    return character, rarity


def random_choice(*args, **kwargs):
    return (random.choices(*args, **kwargs))[0]


def pick_rarity(db: DB) -> Rarity:
    rarities = db.execute('SELECT * FROM rarity').fetchall()
    return Rarity.build(**random_choice(rarities, weights=(r['weight'] for r in rarities)))


def pick_character(db: DB, pack_id: int, rarity_val: int) -> Character:
    chars = db.execute("""
    SELECT character.*, MAX(batch_in_pack.weight) AS weight FROM character
    JOIN character_in_batch   ON character_in_batch.character = character.id
    JOIN batch              ON batch.id = character_in_batch.batch
    JOIN batch_in_pack      ON batch_in_pack.batch = batch.id
    JOIN rarity             ON rarity.value >= character.min_rarity
    WHERE batch_in_pack.pack = ? AND rarity.value = ?
    GROUP BY character.id
    """, [pack_id, rarity_val]).fetchall()
    weights = [c.pop('weight') for c in chars]
    return Character.build(**random_choice(chars, weights=weights))


def give_waifu(db: DB, user: User, character: Character, new_rarity: Rarity) -> Tuple[Waifu, Optional[int]]:
    old_rarity_val, waifu_id = db.execute('''SELECT rarity.value, waifu.id FROM waifu
                                          JOIN rarity ON rarity.value=waifu.rarity
                                          WHERE user=? AND character=?''',
                                          [user.id, character.id]).fetchone() or (None, None)
    if waifu_id is None or old_rarity_val < new_rarity.value:
        waifu_id = db.execute('REPLACE INTO waifu(user, character, rarity) VALUES(?, ?, ?)',
                              [user.id, character.id, new_rarity.value]).lastrowid
    return Waifu.build(id=waifu_id, character=character, rarity=new_rarity, user=user), old_rarity_val


def refund(db: DB, user_id: int, rarity_val: int, cost: int) -> int:
    amount = math.ceil(db.execute("""
    SELECT ? * CAST(value AS FLOAT) / (SELECT MAX(value) FROM rarity)
    AS amount FROM rarity WHERE value=?
    """, [cost, rarity_val]).fetchone()[0])
    add_money(db, user_id, amount)
    return amount


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
           rarity.name AS "rarity.name", rarity.colour AS "rarity.colour", rarity.value AS "rarity.value"
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
