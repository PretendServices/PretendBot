import json
import asyncio
import datetime
import humanize
import humanfriendly
import discord
import random
import string
from discord.abc import GuildChannel
from discord.ui import View, Button, Select
from discord.ext.commands import group, Cog, has_guild_permissions
from discord import (
    Interaction,
    Embed,
    Member,
    User,
    AuditLogAction,
    Guild,
    TextChannel,
    Message,
    Role,
)

from typing import Union, List

from tools.bot import Pretend
from tools.validators import ValidTime
from tools.converters import Punishment
from tools.helpers import PretendContext
from tools.predicates import antinuke_owner, antinuke_configured, admin_antinuke
def generate_code():
  characters = string.hexdigits.upper()
  return ''.join(random.choice(characters) if i not in (3, 6) else '-' for i in range(11))
class BtnViewUrl(View):
    def __init__(self, url: str):
        super().__init__()
        button = discord.ui.button(label="Verify", style=discord.ButtonStyle.url, url=url)
        self.add_item(button)
class BtnViewStart(discord.ui.View):
    def __init__(self):
        super().__init__()

        # Create the button
        verify_button = discord.ui.Button(label="Verify", style=discord.ButtonStyle.primary)
        

        verify_button.callback = self.verify
        
     
        self.add_item(verify_button)
    
    async def verify(self, button: discord.ui.Button, interaction: discord.Interaction):
        random_alphanumeric_5 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        code = str(random_alphanumeric_5)
        match_code = str(generate_code())
        
        await interaction.client.db.execute(
            "INSERT INTO verify_codes_discord(user_id, guild_id, guild_name, valid_until, code, match_code, confirmed) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            interaction.user.id, interaction.guild.id, interaction.guild.name,
            datetime.datetime.now() + datetime.timedelta(minutes=5), code, match_code, False
        )
        
        await interaction.response.send_message(
            f"Click the button below to verify {match_code}",
            view=BtnViewUrl(f"https://pretend.bot/verify/{code}"),
            ephemeral=True
        )
class Verification(Cog):
    def __init__(self, bot: Pretend):
        self.bot = bot
        self.description = "Verification commands"
        self.thresholds = {}

    @group(invoke_without_command=True)
    async def verification(self, ctx: PretendContext):
        await ctx.send_help(ctx.command)
    @has_guild_permissions(administrator=True)
    @verification.command(name="setup", brief="Administrator")
    async def verification_setup(self, ctx: PretendContext, channel: TextChannel, *, role: Role):
        """setup verification"""
        check = await self.bot.db.fetchrow("SELECT * FROM verify_guilds WHERE guild_id = $1", ctx.guild.id)
        if check:
            return await ctx.send("Verification is already setup in this server.")
        await self.bot.db.execute("INSERT INTO verify_guilds(guild_id, role_id) VALUES ($1, $2)", ctx.guild.id, role.id)
        embedcode = "{embed}{color: #181a14}$v{title: Verify}$v{description: Click on the button below this message to verify}$v{author: name: {guild.name} && icon: {guild.icon}}"
        await channel.send(embed=Embed(
            title="Verify",
            description="Click on the button below this message to verify",
            color=discord.Color.blurple()
        ),
       view=BtnViewStart)
        await ctx.send_success("Verification setup successfully.")
    @has_guild_permissions(administrator=True)
    @verification.command(name="reset", brief="Administrator")    
    async def verification_reset(self, ctx: PretendContext):
        """reset verification"""
        check = await self.bot.db.fetchrow("SELECT * FROM verify_guilds WHERE guild_id = $1", ctx.guild.id)
        if not check:
            return await ctx.send("Verification is not setup in this server.")
        await self.bot.db.execute("DELETE FROM verify_guilds WHERE guild_id = $1", ctx.guild.id)
        await ctx.send_success("Verification reset successfully.")


async def setup(bot: Pretend) -> None:
    return await bot.add_cog(Verification(bot))
