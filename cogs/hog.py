import os
import psutil 
import discord

from tools.bot import Pretend 
from tools.helpers import PretendContext
from tools.validators import ValidCommand
from io import BytesIO

from discord import User, Embed, __version__, utils, Permissions
from discord.ext.commands import Cog, command, hybrid_command
from discord.ui import View, Button
from platform import python_version
from posthog import Posthog
posthog = Posthog("phc_pTxc2ZEgflCq1wBWWtloXS8xqK97FPYjlpWLWseYMt8", "https://hog.semisol.dev")
class Hog(Cog):
  def __init__(self, bot: Pretend):
    self.bot = bot 
    self.description = "Posthog Analytics"

  @Cog.listener("on_guild_join")
  async def on_guild_join(self, guild: discord.Guild):
    posthog.group_identify('guild', str(guild.id), {
    'name': guild.name,
    'subscription type': await get_sub_type(self, guild),
 })
  @Cog.listener("on_guild_update")
  async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        posthog.group_identify('guild', str(after.id), {
        'name': after.name,
        'subscription type': await get_sub_type(self, after),
    })
async def get_sub_type(self, guild):
   auth = await self.bot.db.fetchrow("SELECT * FROM AUTHORIZE WHERE guild_id = $1", guild.id)
   if auth:
      till = auth.get("till")
      if till:
            return "monthly"
      else:
            return "onetime"
   else:
       if guild.member_count > 5000:
          return "5k"
       else:
            return "none"
async def setup(bot: Pretend) -> None: 
  return await bot.add_cog(Hog(bot))    
