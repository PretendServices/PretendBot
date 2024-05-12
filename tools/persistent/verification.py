
import asyncio
import datetime
import discord
import random
import string
from discord.abc import GuildChannel
from discord.ui import View, Button, Select
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
class VerificationView(discord.ui.View):
      def __init__(self):
        super().__init__()
        verify_button = discord.ui.Button(label="Verify", style=discord.ButtonStyle.primary, custom_id="verify:persistent")
      
      
        verify_button.callback = self.verify
       
       
        self.add_item(verify_button)
       
      async def verify(self, interaction: discord.Interaction):
        random_alphanumeric_5 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        code = str(random_alphanumeric_5)
        match_code = str(''.join(random.choice(string.hexdigits.upper()) if i not in (3, 6) else '-' for i in range(11)))

        await interaction.client.db.execute(
            "INSERT INTO verify_codes_discord(user_id, guild_id, guild_name, valid_until, code, match_code, confirmed) VALUES ($1, $2, $3, $4, $5, $6, $7)",
            interaction.user.id, interaction.guild.id, interaction.guild.name,
            datetime.datetime.now() + datetime.timedelta(minutes=5), code, match_code, False
        )

        await interaction.response.send_message(
            f"Click the link to verify {match_code}, https://id.pretend.bot/Verify/{code}",
            ephemeral=True
        )