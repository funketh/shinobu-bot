from discord.ext import commands


class Boorualias:

    @commands.command()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def neko(self, ctx, *, tag=""):
        """Neko images"""

        tag_default = " neko"
        tag += tag_default
        boards = ["dan", "gel", "kon", "yan", "safe", "nekos_nsfw_neko", "nekos_sfw_neko"]

        await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.is_nsfw()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def anal(self, ctx, *, tag=""):
    #     """Anal images"""
    #
    #     tag_default = " anal"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "safe", "anal", "nekos_nsfw_anal"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.is_nsfw()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def ass(self, ctx, *, tag=""):
    #     """Ass images"""
    #
    #     tag_default = " ass"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "safe", "ass", "obutts"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.is_nsfw()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def bdsm(self, ctx, *, tag=""):
    #     """Bdsm images"""
    #
    #     tag_default = " bdsm"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "safe", "bdsm", "nekos_nsfw_bdsm", "nekos_nsfw_femdom"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.is_nsfw()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def boobs(self, ctx, *, tag=""):
    #     """Boobs images"""
    #
    #     tag_default = " boobs"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "safe", "boobs", "oboobs", "nekos_nsfw_boobs"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.is_nsfw()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def cumon(self, ctx, *, tag=""):
    #     """Cum_on images"""
    #
    #     tag_default = " cum_on_*"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "safe", "cumshots", "nekos_nsfw_cum"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def yaoi(self, ctx, *, tag=""):
    #     """Yaoi images"""
    #
    #     tag_default = " yaoi"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "safe"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def lesbian(self, ctx, *, tag=""):
    #     """Lesbian images"""
    #
    #     tag_default = " lesbian yuri"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "safe", "lesbian", "nekos_nsfw_yuri"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def milf(self, ctx, *, tag=""):
    #     """Milf images"""
    #
    #     tag_default = " milf"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "safe", "milf"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.is_nsfw()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def oral(self, ctx, *, tag=""):
    #     """Oral images"""
    #
    #     tag_default = " oral"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "cunnilingus", "blowjob", "deepthroat", "nekos_nsfw_blowjob", "nekos_nsfw_cunnilingus"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

    # @commands.command()
    # @commands.is_nsfw()
    # @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    # async def pussy(self, ctx, *, tag=""):
    #     """Pussy images"""
    #
    #     tag_default = " pussy"
    #     tag += tag_default
    #     boards = ["dan", "gel", "kon", "yan", "safe", "pussy", "cunnilingus", "nekos_nsfw_pussy", "nekos_nsfw_cunnilingus"]
    #
    #     await self.generic_alias_booru(ctx, boards, tag)

