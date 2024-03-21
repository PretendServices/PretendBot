import discord
from discord.ext import commands

from discord.ext.commands import group, has_guild_permissions

from tools.bot import Pretend
from tools.helpers import PretendContext

class Logging(commands.Cog):
    def __init__(self, bot: Pretend) -> None:
        self.bot = bot

    @commands.Cog.listener("on_message_edit")
    async def message_edit_logger(self, before: discord.Message, after: discord.Message):
        if check := await self.bot.db.fetchrow("SELECT messages FROM logging WHERE guild_id = $1", before.guild.id):
            channel = await self.bot.fetch_channel(check["messages"])
            if not channel:
                await self.bot.db.execute(
                    """
                    DELETE FROM logging
                    WHERE guild_id = $1
                    AND messages = $2
                    """,
                    before.guild.id,
                    check["messages"]
                )
            
            embed = discord.Embed(
                title="Message Edited",
                description=before.content
            ).add_field(
                name="After edit",
                value=before.content
            ).add_field(
                name="Info",
                value=f"**Author**: {after.author.id}"
                + f"\n**Message**: {after.id}"
                + f"\n**Link**: [Jump]({after.jump_url})"
            )

            await channel.send(embed=embed)

    @group(
        name="logs",
        aliases=["logging"],
        brief="manage server"
    )
    @has_guild_permissions(manage_guild=True)
    async def logs(self, ctx: PretendContext):
        """
        Log events in your server
        """

        await ctx.create_pages()

    @logs.command(
        name="messages",
        aliases=["msgs", "msg"],
        brief="manage server"
    )
    @has_guild_permissions(manage_guild=True)
    async def logs_messages(self, ctx: PretendContext, *, channel: discord.TextChannel):
        """
        Log message-related events
        """

        if str(channel).lower().strip() in ("none", "remove"):
            if check := await self.bot.db.fetchrow(
                """
                SELECT messages FROM logging
                WHERE guild_id = $1
                """,
                ctx.guild.id
            ) is None:
                return await ctx.send_warning(f"Logging is **not** enabled")
            else:
                await self.bot.db.execute(
                    """
                    DELETE FROM logging
                    WHERE guild_id = $1
                    AND messages = $2
                    """,
                    ctx.guild.id,
                    check["messages"]
                )
                return await ctx.send_success(f"No longer logging **messages**")

        if await self.bot.db.fetchrow(
            """
            SELECT messages FROM logging
            WHERE guild_id = $1
            """,
            ctx.guild.id
        ):
            args = ["UPDATE logging SET messages = $1 WHERE guild_id = $2", channel.id, ctx.guild.id]
        else:
            args = ["INSERT INTO logging (guild_id, messages) VALUES ($1, $2)", ctx.guild.id, channel.id]

        await self.bot.db.execute(*args)
        await ctx.send_success(f"Now sending **message logs** to {channel.mention}")

async def setup(bot: Pretend):
    await bot.add_cog(Logging(bot))