from __future__ import annotations

from contextlib import AsyncExitStack
from typing import List, Set

import discord
from discord.ext import commands

from api.expected_errors import ExpectedCommandError
from api.my_context import Context
from api.shinobu import Shinobu
from utils import database
from utils.trade import Change, MoneyTransfer, CHANGES, require


class Trade(commands.Cog):
    @commands.group(aliases=['t'], invoke_without_command=True)
    async def trade(self, ctx: Context):
        """Trade anything with anyone"""
        await ctx.send_help(ctx.command)

    @trade.command(name='cancel', aliases=['c'])
    @require
    async def trade_cancel(self, ctx: Context):
        """Cancel your transaction."""
        change_list = CHANGES[ctx.author]
        async with change_list.lock:
            change_list.clear()
            await ctx.info(f"Cancelled {ctx.author.mention}'s transaction.")

    @trade.command(name='money', aliases=['m'])
    async def trade_money(self, ctx: Context, partner: discord.User, amount: int):
        """Give money to someone"""
        transfer = MoneyTransfer(from_id=ctx.author.id, to_id=partner.id, amount=amount)
        change_list = CHANGES[ctx.author]
        async with change_list.lock:
            change_list.append(transfer)
        await ctx.info(f"Queued action: {transfer}")

    @trade.command(name='sign', aliases=['s'])
    @require
    async def trade_sign(self, ctx: Context, *signers: discord.User):
        """Execute the transactions of every specified signer including yourself"""
        signers: Set[discord.User] = {ctx.author, *signers}
        async with AsyncExitStack() as stack:
            for s in signers:
                await stack.enter_async_context(CHANGES[s].lock)
            all_changes: List[Change] = [c for s in signers for c in CHANGES[s]]
            changes_str = '\n'.join(str(c) for c in all_changes)
            mention_str = ', '.join(s.mention for s in signers)
            msg = await ctx.send(f"{mention_str}: Do you accept the following changes?\n{changes_str}")
            if await ctx.confirm(msg, users=signers):
                with database.connect() as db:
                    for c in all_changes:
                        await c.execute(db)
                    for s in signers:
                        CHANGES[s].clear()
                    await ctx.info("Successfully executed transaction.")
            else:
                raise ExpectedCommandError("Cancelled execution! (Transaction contents are kept)")


def setup(bot: Shinobu):
    bot.add_cog(Trade())
