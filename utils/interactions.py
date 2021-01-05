import discord
from discord.ext import commands

from api.expected_errors import ExpectedCommandError
from api.my_context import Context
from data.CONSTANTS import CURRENCY, UPGRADE, TRASH, SEND, CONFIRM, CANCEL
from extensions.trade import Trade
from utils.database import DB, Waifu, Rarity
from utils.trade import add_money, WaifuTransfer, CHANGES, MoneyTransfer


async def waifu_interactions(ctx: Context, db: DB, msg: discord.Message, waifu: Waifu):
    # TODO: allow interactions that ctx.author can't react to
    assert waifu.user.id == ctx.author.id

    async def trash(user: discord.User, **_):
        waifu.ensure_ownership(db)
        confirmation_msg = await ctx.info(f'Do you really want to refund {waifu.character.name}'
                                          f' for {waifu.rarity.refund} {CURRENCY}?')
        if await ctx.confirm(confirmation_msg):
            waifu.ensure_ownership(db)
            with db:
                add_money(db, user.id, waifu.rarity.refund)
                db.execute('DELETE FROM waifu WHERE id=?', [waifu.id])
            embed: discord.Embed = confirmation_msg.embeds[0]
            embed.description = f"Successfully refunded {waifu.character.name} for {waifu.rarity.refund} {CURRENCY}"
            await confirmation_msg.edit(embed=embed)
        else:
            await confirmation_msg.delete()

    async def upgrade(user: discord.User, **_):
        waifu.ensure_ownership(db)
        confirmation_msg = await ctx.info(f'Do you really want to upgrade {waifu.character.name}'
                                          f' for {waifu.rarity.upgrade_cost} {CURRENCY}?')
        if await ctx.confirm(confirmation_msg):
            waifu.ensure_ownership(db)
            new_rarity = Rarity.select_one(db, 'SELECT * FROM rarity WHERE value=?', [waifu.rarity.value + 1])
            with db:
                add_money(db, user.id, -waifu.rarity.upgrade_cost)
                db.execute('UPDATE waifu SET rarity=? WHERE id=?', [new_rarity.value, waifu.id])
            embed: discord.Embed = confirmation_msg.embeds[0]
            embed.description = f"Successfully upgraded {waifu.character.name} to a **{new_rarity.name}**"
            await confirmation_msg.edit(embed=embed)
        else:
            await confirmation_msg.delete()

    async def send(user: discord.User, **_):
        waifu.ensure_ownership(db)

        answer = await ctx.quick_question(f'Who do you want to give {waifu.character.name} to?', user)
        if answer is None:
            return

        try:
            trade_to = await commands.UserConverter().convert(ctx, answer)
        except commands.BadArgument:
            raise ExpectedCommandError(f"Invalid user! You have to mention them like so: {ctx.bot.user.mention}")

        transfer = WaifuTransfer(from_id=user.id, to_id=trade_to.id, waifu=waifu)
        change_list = CHANGES[ctx.author]
        async with change_list.lock:
            waifu.ensure_ownership(db)
            change_list.append(transfer)
        queued_msg = await ctx.info(f"Queued action: {transfer}")
        await queue_interactions(ctx, queued_msg)

    reactions = {}
    if waifu.rarity.upgrade_cost is not None:
        reactions[UPGRADE] = upgrade
    reactions[TRASH] = trash
    reactions[SEND] = send

    await ctx.reaction_buttons(msg, reactions)


async def user_interactions(ctx: Context, msg: discord.Message, target_user: discord.User):
    async def send(user: discord.User, **_):
        if user == target_user:
            answer = await ctx.quick_question(f'Who do you want to give {CURRENCY} to?', user)
            if answer is None:
                return

            try:
                trade_to = await commands.UserConverter().convert(ctx, answer)
            except commands.BadArgument:
                raise ExpectedCommandError(f"Invalid user! You have to mention them like so: {ctx.bot.user.mention}")
        else:
            trade_to = target_user

        answer = await ctx.quick_question(f'How much {CURRENCY} do you want to give {trade_to.mention}?', user)
        if answer is None:
            return

        try:
            amount = int(answer)
        except ValueError:
            raise ExpectedCommandError(f"Invalid amount!")

        transfer = MoneyTransfer(from_id=user.id, to_id=trade_to.id, amount=amount)
        change_list = CHANGES[ctx.author]
        async with change_list.lock:
            change_list.append(transfer)
        queued_msg = await ctx.info(f"Queued action: {transfer}")
        await queue_interactions(ctx, queued_msg)

    await ctx.reaction_buttons(msg, {SEND: send})


async def queue_interactions(ctx: Context, msg: discord.Message):
    async def confirm(**_):
        # XXX: this is hacky because I'm injecting an incorrect context and self but it doesn't really matter
        await Trade.trade_sign.callback(object(), ctx)

    async def cancel(**_):
        # XXX: this is hacky because I'm injecting an incorrect context and self but it doesn't really matter
        await Trade.trade_cancel.callback(object(), ctx)

    await ctx.reaction_buttons(msg, {CONFIRM: confirm, CANCEL: cancel})
