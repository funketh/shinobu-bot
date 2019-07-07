import time

import discord
from discord.ext import commands

import shinobu
from utils import database


class CallNotification(commands.Cog):
    def __init__(self):
        self.COOLDOWN_TIME = 5
        self.last_used = 0
        self.voiceid_to_textid = {
            row['voice_id']: row['text_id']
            for row in database.connect().execute(
                'SELECT voice_id, text_id FROM voice_to_text'
            )
        }

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState,
                                    after: discord.VoiceState):
        """Notifies certain channels when someone starts a call"""
        print('activated')
        if (time.time() < self.last_used + self.COOLDOWN_TIME
            or after.channel is None
            or after.channel.id == getattr(before.channel, 'id', None)
            or len(after.channel.members) > 1
            or after.channel.id not in self.voiceid_to_textid
            ): return
        text_channel = discord.utils.get(
            member.guild.channels,
            id=self.voiceid_to_textid[after.channel.id]
        )
        await text_channel.send(embed=discord.Embed(
            description=f"{member.mention} started a call.",
            colour=discord.Colour.green()
        ))
        self.last_used = time.time()


def setup(bot: shinobu.Shinobu):
    bot.add_cog(CallNotification())
