import time

import discord
from discord.ext import commands

import shinobu

cooldown_time = 5
voiceid_to_textid = {
    440532931841228807: 440532276594343936,  # MoC
    456898147415883776: 456799399176306688,  # NSFW
    296355094243311617: 296355094243311616,  # Allgemein
    515240036871045132: 513010405929648128,  # Informatik
}
last_used = 0


class CallNotification(commands.Cog):
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Notifies certain channels when someone starts a call"""
        global last_used
        if (time.time() < last_used + cooldown_time
            or after.channel is None
            or after.channel.id == getattr(before.channel, 'id', None)
            or len(after.channel.members) > 1
            or after.channel.id not in voiceid_to_textid
            ): return
        text_channel = discord.utils.get(member.guild.channels, id=voiceid_to_textid[after.channel.id])
        await text_channel.send(embed=discord.Embed(description=f"{member.mention} started a call.",
                                                    colour=discord.Colour.green()))
        last_used = time.time()


def setup(bot: shinobu.Shinobu):
    bot.add_cog(CallNotification())
