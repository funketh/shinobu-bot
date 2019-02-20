import discord

from utils.main_guild import user_to_member, UserNotInGuild


async def has_role(user: discord.User, role: discord.Role):
    try:
        member = await user_to_member(user)
    except UserNotInGuild:
        return False
    return role in member.roles
