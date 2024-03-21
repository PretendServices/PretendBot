import discord
from discord.ext import commands

from discord.ext.commands import group, has_guild_permissions

from tools.bot import Pretend
from tools.helpers import PretendContext

class Logging(commands.Cog):
    def __init__(self, bot: Pretend) -> None:
        self.bot = bot

    @commands.Cog.listener("on_message_delete")
    async def message_delete_logger(self, message: discord.Message):
        if check := await self.bot.db.fetchrow("SELECT messages FROM logging WHERE guild_id = $1", message.guild.id):
            channel = await self.bot.fetch_channel(check["messages"])
            if not channel:
                return await self.bot.db.execute(
                    """
                    DELETE FROM logging
                    WHERE guild_id = $1
                    AND messages = $2
                    """,
                    message.guild.id,
                    check["messages"]
                )

            embed = discord.Embed(
                title="Message Deleted",
                description=message.content,
                color=self.bot.color
            ).add_field(
                name="Info",
                value=f"**Author**: {message.author.id}"
                + f"\n**Message**: {message.id}"
                + f"\n**Link**: [Jump]({message.jump_url})"
            ).set_author(
                name=message.author.name,
                icon_url=message.author.display_avatar.url
            )

            await channel.send(embed=embed)

    @commands.Cog.listener("on_message_edit")
    async def message_edit_logger(self, before: discord.Message, after: discord.Message):
        if after.content != before.content:
            if check := await self.bot.db.fetchrow("SELECT messages FROM logging WHERE guild_id = $1", before.guild.id):
                channel = await self.bot.fetch_channel(check["messages"])
                if not channel:
                    return await self.bot.db.execute(
                        """
                        DELETE FROM logging
                        WHERE guild_id = $1
                        AND messages = $2
                        """,
                        before.guild.id,
                        check["messages"]
                    )
                
                if before.embeds:
                    return
                
                if before.author.bot:
                    return

                embed = discord.Embed(
                    title="Message Edited",
                    description=before.content,
                    color=self.bot.color
                ).add_field(
                    name="After edit",
                    value=after.content,
                    inline=False
                ).add_field(
                    name="Info",
                    value=f"**Author**: {after.author.id}"
                    + f"\n**Message**: {after.id}"
                    + f"\n**Link**: [Jump]({after.jump_url})",
                    inline=False
                ).set_author(
                    name=after.author.name,
                    icon_url=after.author.display_avatar.url
                )

                await channel.send(embed=embed)

    @commands.Cog.listener("on_guild_update")
    async def guild_update_logger(self, before: discord.Guild, after: discord.Guild):
        if check := await self.bot.db.fetchrow("SELECT guild FROM logging WHERE guild_id = $1", before.id):
            channel = await self.bot.fetch_channel(check["guild"])
            if not channel:
                await self.bot.db.execute(
                    """
                    DELETE FROM logging
                    WHERE guild_id = $1
                    AND messages = $2
                    """,
                    before.id,
                    check["guild"]
                )

            actions = []

            if before.name != after.name:
                actions.append(f"**Old Name**: {before.name}\n**New Name**: {after.name}")

            if before.afk_channel != after.afk_channel:
                actions.append(f"**Old AFK Channel**: {before.afk_channel.mention}\n**New AFK Channel**: {after.afk_channel.mention}")

            if before.icon != after.icon:
                actions.append(f"**Old Icon**: {before.icon.url if before.icon else 'N/A'}\n**New Icon** {after.icon.url if after.icon else 'Removed'}")

            if before.banner != after.banner:
                actions.append(f"**Old Banner**: {before.banner.url}\n**New Banner** {after.banner.url if after.banner else 'Removed'}")

            embed = discord.Embed(
                title="Guild Edited",
                description="\n".join(actions),
                color=self.bot.color
            )

            await channel.send(embed=embed)

    @commands.Cog.listener("on_guild_role_create")
    async def role_create_logger(self, role: discord.Role):
        if check := await self.bot.db.fetchrow("SELECT roles FROM logging WHERE guild_id = $1", role.guild.id):
            channel = await self.bot.fetch_channel(check["roles"])
            if not channel:
                await self.bot.db.execute(
                    """
                    DELETE FROM logging
                    WHERE guild_id = $1
                    AND messages = $2
                    """,
                    role.guild.id,
                    check["roles"]
                )

            embed = discord.Embed(
                title="Role Created",
                description=f"{role.mention} ({role.id})",
                color=self.bot.color
            ).set_author(
                name=self.bot.user.name,
                icon_url=self.bot.user.avatar.url
            )

            await channel.send(embed=embed)

    @commands.Cog.listener("on_guild_role_delete")
    async def role_delete_logger(self, role: discord.Role):
        if check := await self.bot.db.fetchrow("SELECT roles FROM logging WHERE guild_id = $1", role.guild.id):
            channel = await self.bot.fetch_channel(check["roles"])
            if not channel:
                await self.bot.db.execute(
                    """
                    DELETE FROM logging
                    WHERE guild_id = $1
                    AND messages = $2
                    """,
                    role.guild.id,
                    check["roles"]
                )

            embed = discord.Embed(
                title="Role Deleted",
                description=f"{role.mention} ({role.id})",
                color=self.bot.color
            ).set_author(
                name=self.bot.user.name,
                icon_url=self.bot.user.avatar.url
            )

            await channel.send(embed=embed)

    @group(
        name="logs",
        aliases=["logging"],
        brief="manage server",
        invoke_without_command=True
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
        Log message related events
        """

        if str(channel).lower().strip() in ("none", "remove"):
            if check := await self.bot.db.fetchrow(
                """
                SELECT messages FROM logging
                WHERE guild_id = $1
                """,
                ctx.guild.id
            ) is None:
                return await ctx.send_warning(f"Message logging is **not** enabled")
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

    @logs.command(
        name="guild",
        brief="manage server"
    )
    @has_guild_permissions(manage_guild=True)
    async def logs_guild(self, ctx: PretendContext, *, channel: discord.TextChannel):
        """
        Log guild edit events
        """

        if str(channel).lower().strip() in ("none", "remove"):
            if check := await self.bot.db.fetchrow(
                """
                SELECT guild FROM logging
                WHERE guild_id = $1
                """,
                ctx.guild.id
            ) is None:
                return await ctx.send_warning(f"Guild logging is **not** enabled")
            else:
                await self.bot.db.execute(
                    """
                    DELETE FROM logging
                    WHERE guild_id = $1
                    AND guild = $2
                    """,
                    ctx.guild.id,
                    check["guild"]
                )
                return await ctx.send_success(f"No longer logging **guild changes**")
            
        if await self.bot.db.fetchrow(
            """
            SELECT guild FROM logging
            WHERE guild_id = $1
            """,
            ctx.guild.id
        ):
            args = ["UPDATE logging SET guild = $1 WHERE guild_id = $2", channel.id, ctx.guild.id]
        else:
            args = ["INSERT INTO logging (guild_id, guild) VALUES ($1, $2)", ctx.guild.id, channel.id]

        await self.bot.db.execute(*args)
        await ctx.send_success(f"Now sending **guild logs** to {channel.mention}")

    @logs.command(
        name="roles",
        aliases=["role"],
        brief="manage server"
    )
    @has_guild_permissions(manage_guild=True)
    async def logs_roles(self, ctx: PretendContext, *, channel: discord.TextChannel):
        """
        Log role related events
        """

        if str(channel).lower().strip() in ("none", "remove"):
            if check := await self.bot.db.fetchrow(
                """
                SELECT roles FROM logging
                WHERE guild_id = $1
                """,
                ctx.guild.id
            ) is None:
                return await ctx.send_warning(f"Role logging is **not** enabled")
            else:
                await self.bot.db.execute(
                    """
                    DELETE FROM logging
                    WHERE guild_id = $1
                    AND roles = $2
                    """,
                    ctx.guild.id,
                    check["roles"]
                )
                return await ctx.send_success(f"No longer logging **role changes**")
            
        if await self.bot.db.fetchrow(
            """
            SELECT roles FROM logging
            WHERE guild_id = $1
            """,
            ctx.guild.id
        ):
            args = ["UPDATE logging SET roles = $1 WHERE guild_id = $2", channel.id, ctx.guild.id]
        else:
            args = ["INSERT INTO logging (guild_id, roles) VALUES ($1, $2)", ctx.guild.id, channel.id]

        await self.bot.db.execute(*args)
        await ctx.send_success(f"Now sending **roles logs** to {channel.mention}")

async def setup(bot: Pretend):
    await bot.add_cog(Logging(bot))