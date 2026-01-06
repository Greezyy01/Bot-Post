from __future__ import annotations

import discord
from discord import app_commands

from models import ChannelConfig


def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        guild = interaction.guild
        if not guild:
            return False
        config = interaction.client.config.get_guild(guild.id)
        if config.owner_id is None:
            return False
        return interaction.user.id == config.owner_id

    return app_commands.check(predicate)


class SetupModal(discord.ui.Modal, title="AutoPost Setup"):
    user_token = discord.ui.TextInput(
        label="User Token", style=discord.TextStyle.short, required=True
    )
    webhook_url = discord.ui.TextInput(
        label="Webhook URL", style=discord.TextStyle.short, required=False
    )
    owner_id = discord.ui.TextInput(
        label="Owner ID", style=discord.TextStyle.short, required=True
    )
    default_delay = discord.ui.TextInput(
        label="Default Delay (min,max)",
        style=discord.TextStyle.short,
        required=True,
        placeholder="60,300",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        min_delay, max_delay = self._parse_delay(self.default_delay.value)
        await interaction.client.config.set_token(self.user_token.value)
        await interaction.client.config.update_guild(
            interaction.guild_id,
            {
                "owner_id": int(self.owner_id.value),
                "webhook_url": self.webhook_url.value or None,
                "default_min_delay": min_delay,
                "default_max_delay": max_delay,
            },
        )
        await interaction.response.send_message(
            "Setup selesai! Gunakan `/dashboard` untuk membuka dashboard.",
            ephemeral=True,
        )

    def _parse_delay(self, value: str) -> tuple[int, int]:
        parts = value.split(",")
        if len(parts) != 2:
            return (60, 300)
        try:
            return int(parts[0].strip()), int(parts[1].strip())
        except ValueError:
            return (60, 300)


class CommandRegistrar:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    def register(self) -> None:
        tree = self.bot.tree

        @tree.command(name="setup", description="Setup awal bot dengan modal form")
        async def setup(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(SetupModal())

        @tree.command(name="dashboard", description="Tampilkan dashboard monitoring")
        async def dashboard(interaction: discord.Interaction) -> None:
            embed = await self.bot.build_dashboard_embed(interaction.guild_id)
            view = self.bot.dashboard_view
            await interaction.response.send_message(embed=embed, view=view)

        @tree.command(name="stats", description="Tampilkan statistik bot")
        async def stats(interaction: discord.Interaction) -> None:
            snapshot = self.bot.stats.snapshot()
            embed = self.bot.build_stats_embed(snapshot)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @tree.command(
            name="quickadd",
            description="Tambah channel cepat",
        )
        @app_commands.describe(
            channel="Channel tujuan",
            message="Pesan yang akan dikirim",
            min_delay="Delay minimal (detik)",
            max_delay="Delay maksimal (detik)",
        )
        async def quickadd(
            interaction: discord.Interaction,
            channel: discord.TextChannel,
            message: str,
            min_delay: int,
            max_delay: int,
        ) -> None:
            channel_cfg = ChannelConfig(
                channel_id=channel.id,
                message=message,
                min_delay=min_delay,
                max_delay=max_delay,
            )
            await self.bot.config.add_channel(interaction.guild_id, channel_cfg)
            await interaction.response.send_message(
                f"Channel {channel.mention} ditambahkan.", ephemeral=True
            )

        @tree.command(name="stop", description="Hentikan semua postingan")
        @is_owner()
        async def stop(interaction: discord.Interaction) -> None:
            await self.bot.scheduler.stop_all()
            await interaction.response.send_message("Posting dihentikan.", ephemeral=True)

        @tree.command(name="start", description="Mulai semua postingan")
        @is_owner()
        async def start(interaction: discord.Interaction) -> None:
            await self.bot.scheduler.start_all()
            await interaction.response.send_message("Posting dimulai.", ephemeral=True)

        @tree.command(name="config", description="Tampilkan pengaturan bot")
        async def config(interaction: discord.Interaction) -> None:
            embed = await self.bot.build_config_embed(interaction.guild_id)
            await interaction.response.send_message(embed=embed, ephemeral=True)
