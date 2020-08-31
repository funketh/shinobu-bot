import logging

import aiohttp
from discord.ext import commands

from .boorualias import Boorualias
from .boorucore import BooruCore

# Debug stuff
log = logging.getLogger("Booru")
log.setLevel(logging.DEBUG)

BaseCog = getattr(commands, "Cog", object)


class Booru(BaseCog, BooruCore, Boorualias):
    """Show images from various sources"""

    def __init__(self):
        # Reusable stuff
        self.session = aiohttp.ClientSession()

    @commands.command()
    async def booru(self, ctx, *, tag=None):
        """Shows images based on user input and settings"""
        await self.generic_booru(ctx, tag)

    @commands.group()
    async def boorus(self, ctx):
        """Query the boorus"""
        pass

    @boorus.group()
    async def yan(self, ctx, *, tag=None):
        """Shows images using tags from yande.re"""

        board = "yan"
        await self.generic_specific_source(ctx, board, tag)

    @boorus.group()
    async def gel(self, ctx, *, tag=None):
        """Shows images using tags from gelbooru"""

        board = "gel"
        await self.generic_specific_source(ctx, board, tag)

    @boorus.group()
    async def kon(self, ctx, *, tag=None):
        """Shows images using tags from konachan"""

        board = "kon"
        await self.generic_specific_source(ctx, board, tag)

    @boorus.group()
    async def dan(self, ctx, *, tag=None):
        """Shows images using tags from Danbooru"""

        board = "dan"
        await self.generic_specific_source(ctx, board, tag)

    @boorus.group()
    async def r34(self, ctx, *, tag=None):
        """Shows images using tags from Rule34"""

        board = "r34"
        await self.generic_specific_source(ctx, board, tag)

    @boorus.group()
    async def safe(self, ctx, *, tag=None):
        """Shows images using tags from Safebooru"""

        board = "safe"
        await self.generic_specific_source(ctx, board, tag)

    @commands.group()
    async def reddits(self, ctx):
        """Query sources for all the subreddits!"""
        pass

    @reddits.group(name="hentai")
    @commands.is_nsfw()
    async def _hentai(self, ctx):
        """Images from hentai subreddits"""

        board = "hentai"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @reddits.group(name="rule34")
    @commands.is_nsfw()
    async def _rule34(self, ctx):
        """Images from rule34 subreddits"""
        await self.generic_specific_source(ctx, board='rule34', tag=None)

    @commands.group()
    async def nekos(self, ctx):
        """Query sources from nekos.life!"""
        pass

    @nekos.group()
    async def nsfw(self, ctx):
        """Query nsfw sources from nekos.life!"""
        pass

    @nsfw.group(name="classic")
    @commands.is_nsfw()
    async def _nekos_nsfw_classic(self, ctx):
        """Images from classic endpoints"""

        board = "nekos_nsfw_classic"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="blowjob")
    @commands.is_nsfw()
    async def _nekos_nsfw_blowjob(self, ctx):
        """Images from blowjob endpoints"""

        board = "nekos_nsfw_blowjob"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="boobs")
    @commands.is_nsfw()
    async def _nekos_nsfw_boobs(self, ctx):
        """Images from boobs endpoints"""

        board = "nekos_nsfw_boobs"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="neko")
    @commands.is_nsfw()
    async def _nekos_nsfw_neko(self, ctx):
        """Images from nekos endpoints"""

        board = "nekos_nsfw_neko"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="furry")
    @commands.is_nsfw()
    async def _nekos_nsfw_furry(self, ctx):
        """Images from furry endpoints"""

        board = "nekos_nsfw_furry"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="pussy")
    @commands.is_nsfw()
    async def _nekos_nsfw_pussy(self, ctx):
        """Images from pussy endpoints"""

        board = "nekos_nsfw_pussy"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="feet")
    @commands.is_nsfw()
    async def _nekos_nsfw_feet(self, ctx):
        """Images from feet endpoints"""

        board = "nekos_nsfw_feet"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="yuri")
    @commands.is_nsfw()
    async def _nekos_nsfw_yuri(self, ctx):
        """Images from yuri endpoints"""

        board = "nekos_nsfw_yuri"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="anal")
    @commands.is_nsfw()
    async def _nekos_nsfw_anal(self, ctx):
        """Images from anal endpoints"""

        board = "nekos_nsfw_anal"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="solo")
    @commands.is_nsfw()
    async def _nekos_nsfw_solo(self, ctx):
        """Images from solo endpoints"""

        board = "nekos_nsfw_solo"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="cum")
    @commands.is_nsfw()
    async def _nekos_nsfw_cum(self, ctx):
        """Images from cum endpoints"""

        board = "nekos_nsfw_cum"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="spank")
    @commands.is_nsfw()
    async def _nekos_nsfw_spank(self, ctx):
        """Images from spank endpoints"""

        board = "nekos_nsfw_spank"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="cunnilingus")
    @commands.is_nsfw()
    async def _nekos_nsfw_cunnilingus(self, ctx):
        """Images from cunnilingus endpoints"""

        board = "nekos_nsfw_cunnilingus"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="bdsm")
    @commands.is_nsfw()
    async def _nekos_nsfw_bdsm(self, ctx):
        """Images from bdsm endpoints"""

        board = "nekos_nsfw_bdsm"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="piercings")
    @commands.is_nsfw()
    async def _nekos_nsfw_piercings(self, ctx):
        """Images from piercings endpoints"""

        board = "nekos_nsfw_piercings"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="kitsune")
    @commands.is_nsfw()
    async def _nekos_nsfw_kitsune(self, ctx):
        """Images from kitsune endpoints"""

        board = "nekos_nsfw_kitsune"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="holo")
    @commands.is_nsfw()
    async def _nekos_nsfw_holo(self, ctx):
        """Images from holo endpoints"""

        board = "nekos_nsfw_holo"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nsfw.group(name="femdom")
    @commands.is_nsfw()
    async def _nekos_nsfw_femdom(self, ctx):
        """Images from femdom endpoints"""

        board = "nekos_nsfw_femdom"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @nekos.group()
    async def sfw(self, ctx):
        """Query sfw sources from nekos.life!"""
        pass

    @sfw.group(name="neko")
    async def _nekos_sfw_neko(self, ctx):
        """Images from neko endpoints"""

        board = "nekos_sfw_neko"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @sfw.group(name="waifu")
    async def _nekos_sfw_waifu(self, ctx):
        """Images from waifu endpoints"""

        board = "nekos_sfw_waifu"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @sfw.group(name="kitsune")
    async def _nekos_sfw_kitsune(self, ctx):
        """Images from kitsune endpoints"""

        board = "nekos_sfw_kitsune"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @sfw.group(name="smug")
    async def _nekos_sfw_smug(self, ctx):
        """Images from smug endpoints"""

        board = "nekos_sfw_smug"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    @sfw.group(name="holo")
    async def _nekos_sfw_holo(self, ctx):
        """Images from holo endpoints"""

        board = "nekos_sfw_holo"
        tag = None
        await self.generic_specific_source(ctx, board, tag)

    def __unload(self):
        # Aiohttp closing plz work
        self.session.detach()

