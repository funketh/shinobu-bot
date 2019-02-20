import discord


class UserNotInGuild(BaseException):
    pass


async def guild() -> discord.Guild:
    return NotImplemented


async def user_to_member(user: discord.User) -> discord.Member:
    member = (await guild()).get_member(user.id)
    if not member:
        raise UserNotInGuild
    return member
