import random
import sqlite3
from dataclasses import dataclass
from typing import Tuple, Generator, List, Union

import discord
from fuzzywuzzy import process

from api.expected_errors import ExpectedCommandError
from api.my_context import Context
from data.CONSTANTS import TRASH, CURRENCY, UPGRADE
from utils.database import DB, Waifu, Pack, Character, User, Rarity

CURRENT_PREDICATE = "((pack.start_date <= CURRENT_DATE) " \
                    " AND (pack.end_date IS NULL OR pack.end_date >= CURRENT_DATE))"


@dataclass(frozen=True)
class Refund:
    amount: int


@dataclass(frozen=True)
class Upgrade:
    upgraded_rarity: Rarity


DuplicateType = Union[Refund, Upgrade, None]


async def buy_pack(db: DB, user_id: int, pack_name: str) -> Tuple[Waifu, DuplicateType]:
    with db:
        user = User.select_one(db, 'SELECT * FROM user WHERE id=?', [user_id])
        try:
            pack = Pack.select_one(db, f'SELECT * FROM pack WHERE {CURRENT_PREDICATE} AND name LIKE ?', [pack_name])
        except TypeError:
            raise ExpectedCommandError(f"There's no pack named {pack_name}!")
        add_money(db, user.id, -pack.cost)
        character, rarity = pick_from_pack(db, pack.name)
        return give_waifu(db, user, character, rarity)


def add_money(db: DB, user_id: int, amount: int):
    try:
        db.execute('UPDATE user SET balance=balance+? WHERE id=?', [amount, user_id])
    except sqlite3.IntegrityError:
        raise ExpectedCommandError(f'<@{user_id}> does not have enough money!')


def pick_from_pack(db: DB, pack_name: str) -> Tuple[Character, Rarity]:
    rarity = pick_rarity(db)
    character = pick_character(db, pack_name, rarity.value)
    return character, rarity


def pick(*args, **kwargs):
    return random.choices(*args, **kwargs)[0]


def pick_rarity(db: DB) -> Rarity:
    rarities = db.execute('SELECT * FROM rarity').fetchall()
    return Rarity.build(**pick(rarities, weights=(r['weight'] for r in rarities)))


def pick_character(db: DB, pack_name: str, rarity_val: int) -> Character:
    chars = [dict(c) for c in db.execute("""
    SELECT character.id,
           character.name,
           character.image_url,
           character.series,
           character.rarity AS 'rarity.value',
           character.batch AS 'batch.name',
           MAX(batch_in_pack.weight) AS __weight__
    FROM character
    JOIN batch_in_pack      ON batch_in_pack.batch = character.batch
    JOIN rarity             ON rarity.value >= character.rarity
    WHERE batch_in_pack.pack = ? AND rarity.value = ?
    GROUP BY character.id
    """, [pack_name, rarity_val])]
    weights = [c.pop('__weight__') for c in chars]
    return Character.build(**pick(chars, weights=weights))


def give_waifu(db: DB, user: User, character: Character, new_rarity: Rarity) -> Tuple[Waifu, DuplicateType]:
    waifu = Waifu.select_one(db, """
    SELECT waifu.id, waifu.rarity AS 'rarity.value',
           waifu.character AS 'character.id', waifu.user AS 'user.id'
    FROM waifu WHERE user=? AND character=?
    """, [user.id, character.id])

    if waifu is None:
        waifu_id = db.execute('INSERT INTO waifu(user, character, rarity) VALUES(?, ?, ?)',
                              [user.id, character.id, new_rarity.value]).lastrowid
        waifu = Waifu(id=waifu_id, character=character, rarity=new_rarity, user=user)
        duplicate = None

    elif waifu.rarity.value == new_rarity.value and new_rarity.auto_upgrade:
        new_rarity = Rarity.select_one(db, 'SELECT * FROM rarity WHERE value=?', [waifu.rarity.value + 1])
        db.execute('UPDATE waifu SET rarity=? WHERE id=?', [new_rarity.value, waifu.id])
        duplicate = Upgrade(new_rarity)

    else:
        waifu.rarity = Rarity.select_one(db, 'SELECT * FROM rarity WHERE value=?', [waifu.rarity.value])
        lower, higher = sorted((new_rarity, waifu.rarity), key=lambda r: r.value)
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
    except StopIteration:
        raise ExpectedCommandError("You don't have any waifus!")


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
    return list(Waifu.select_many(db, """
    SELECT waifu.id,
           -- Character
               character.id AS "character.id",
               character.name AS "character.name",
               character.image_url AS "character.image_url",
               character.series AS "character.series",
           -- Rarity
               rarity.value AS "rarity.value",
               rarity.name AS "rarity.name",
               rarity.colour AS "rarity.colour",
               rarity.refund AS "rarity.refund",
               rarity.upgrade_cost AS "rarity.upgrade_cost",
               rarity.auto_upgrade AS "rarity.auto_upgrade",
           -- User
               user.id AS "user.id",
               user.balance AS "user.balance",
               user.last_withdrawal AS "user.last_withdrawal",
               user.birthday AS "user.birthday",
               user.mal_username AS "user.mal_username"
    FROM waifu
    JOIN character ON character.id = waifu.character
    JOIN rarity ON rarity.value = waifu.rarity
    JOIN user ON user.id = waifu.user
    WHERE user.id = ?
    ORDER BY rarity.value DESC,
             character.name ASC
    """, [user_id]))


async def waifu_interactions(ctx: Context, db: DB, msg: discord.Message, waifu: Waifu):
    reactions = [TRASH]
    if waifu.rarity.upgrade_cost is not None:
        reactions.append(UPGRADE)

    async for reaction, user in ctx.wait_for_reactions(msg, reactions=reactions):
        waifu.ensure_ownership(db)

        if reaction.emoji == TRASH:
            confirmation_msg = await ctx.info(f'Do you really want to refund {waifu.character.name}'
                                              f' for {waifu.rarity.refund} {CURRENCY}?')
            if await ctx.confirm(confirmation_msg):
                waifu.ensure_ownership(db)
                with db:
                    add_money(db, ctx.author.id, waifu.rarity.refund)
                    db.execute('DELETE FROM waifu WHERE id=?', [waifu.id])
                embed: discord.Embed = confirmation_msg.embeds[0]
                embed.description = f"Successfully refunded {waifu.character.name} for {waifu.rarity.refund} {CURRENCY}"
                await confirmation_msg.edit(embed=embed)
            else:
                await confirmation_msg.delete()
                await reaction.remove(user)

        elif reaction.emoji == UPGRADE:
            confirmation_msg = await ctx.info(f'Do you really want to upgrade {waifu.character.name}'
                                              f' for {waifu.rarity.refund} {CURRENCY}?')
            if await ctx.confirm(confirmation_msg):
                waifu.ensure_ownership(db)
                new_rarity = Rarity.select_one(db, 'SELECT * FROM rarity WHERE value=?', [waifu.rarity.value + 1])
                with db:
                    add_money(db, ctx.author.id, -waifu.rarity.upgrade_cost)
                    db.execute('UPDATE waifu SET rarity=? WHERE id=?', [new_rarity.value, waifu.id])
                embed: discord.Embed = confirmation_msg.embeds[0]
                embed.description = f"Successfully upgraded {waifu.character.name} to a **{waifu.rarity.name}**"
                await confirmation_msg.edit(embed=embed)
            else:
                await confirmation_msg.delete()
                await reaction.remove(user)
