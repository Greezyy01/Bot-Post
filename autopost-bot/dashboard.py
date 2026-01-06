from __future__ import annotations

import discord

from models import StatsSnapshot
from utils import format_uptime


class DashboardView(discord.ui.View):
    def __init__(self, bot: discord.Client) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    async def _refresh(self, interaction: discord.Interaction) -> None:
        embed = await self.bot.build_dashboard_embed(interaction.guild_id)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="START ALL", style=discord.ButtonStyle.success, emoji="▶️")
    async def start_all(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await self.bot.scheduler.start_all()
        await self._refresh(interaction)

    @discord.ui.button(label="PAUSE ALL", style=discord.ButtonStyle.secondary, emoji="⏸️")
    async def pause_all(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        if interaction.guild_id:
            await self.bot.scheduler.pause_guild(interaction.guild_id)
        await self._refresh(interaction)

    @discord.ui.button(label="STOP ALL", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_all(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await self.bot.scheduler.stop_all()
        await self._refresh(interaction)

    @discord.ui.button(label="STATS", style=discord.ButtonStyle.primary, emoji="📊")
    async def stats(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        snapshot = self.bot.stats.snapshot()
        embed = self.bot.build_stats_embed(snapshot)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="SETTINGS", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def settings(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        embed = await self.bot.build_config_embed(interaction.guild_id)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="REFRESH", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await self._refresh(interaction)

    @discord.ui.button(label="ADD CHANNEL", style=discord.ButtonStyle.success, emoji="➕")
    async def add_channel(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_message(
            "Gunakan `/quickadd` untuk menambah channel.", ephemeral=True
        )

    @discord.ui.button(label="EDIT ALL", style=discord.ButtonStyle.secondary, emoji="✏️")
    async def edit_all(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_message(
            "Gunakan `/config` untuk melihat pengaturan.", ephemeral=True
        )

    @discord.ui.button(label="REMOVE ALL", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def remove_all(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        if interaction.guild_id:
            await self.bot.config.remove_all_channels(interaction.guild_id)
        await interaction.response.send_message(
            "Semua channel dihapus dari konfigurasi.", ephemeral=True
        )

    @discord.ui.button(label="LIST CHANNELS", style=discord.ButtonStyle.primary, emoji="📋")
    async def list_channels(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        if not interaction.guild_id:
            return
        guild = self.bot.config.get_guild(interaction.guild_id)
        lines = [
            f"<#{ch.channel_id}> | {ch.min_delay}-{ch.max_delay}s | {ch.group}"
            for ch in guild.channels
        ]
        content = "\n".join(lines) if lines else "Belum ada channel."
        await interaction.response.send_message(content, ephemeral=True)

    @discord.ui.button(label="EXPORT", style=discord.ButtonStyle.secondary, emoji="📁")
    async def export_config(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        backup = await self.bot.config.backup()
        await interaction.response.send_message(
            f"Backup dibuat: `{backup}`", ephemeral=True
        )

    @discord.ui.button(label="IMPORT", style=discord.ButtonStyle.secondary, emoji="📤")
    async def import_config(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_message(
            "Gunakan `/setup` untuk mengatur konfigurasi ulang.",
            ephemeral=True,
        )

    @discord.ui.button(label="REAL-TIME LOGS", style=discord.ButtonStyle.primary, emoji="📈")
    async def logs(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_message(
            "Logs realtime tersedia di file logs/.", ephemeral=True
        )

    @discord.ui.button(label="ALERTS", style=discord.ButtonStyle.secondary, emoji="🔔")
    async def alerts(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_message(
            "Alerts akan dikirim via webhook jika diatur.", ephemeral=True
        )

    @discord.ui.button(label="TOGGLE WEBHOOK", style=discord.ButtonStyle.secondary, emoji="🎛️")
    async def toggle_webhook(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_message(
            "Gunakan `/setup` untuk mengubah webhook.", ephemeral=True
        )

    @discord.ui.button(label="RUNTIME", style=discord.ButtonStyle.secondary, emoji="🕐")
    async def runtime(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        uptime = format_uptime(self.bot.started_at)
        await interaction.response.send_message(
            f"Runtime bot: {uptime}", ephemeral=True
        )

    @discord.ui.button(label="PERFORMANCE", style=discord.ButtonStyle.secondary, emoji="📉")
    async def performance(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        snapshot = self.bot.stats.snapshot()
        await interaction.response.send_message(
            f"Avg post time: {snapshot.avg_post_time:.2f}s", ephemeral=True
        )

    @discord.ui.button(label="LOG FILE", style=discord.ButtonStyle.secondary, emoji="📄")
    async def log_file(
        self, interaction: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await interaction.response.send_message(
            "Log file berada di folder logs/.", ephemeral=True
        )


class DashboardManager:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot

    def build_embed(self, snapshot: StatsSnapshot, status: str, guild_summary: str) -> discord.Embed:
        embed = discord.Embed(
            title="🤖 AUTOPOST DASHBOARD",
            color=discord.Color.green() if status == "RUNNING" else discord.Color.red(),
        )
        embed.add_field(
            name="Status",
            value=f"🟢 STATUS: {status}\n⏱️ Runtime: {snapshot.uptime}",
            inline=False,
        )
        embed.add_field(
            name="Totals",
            value=f"📊 TOTAL: {snapshot.total_success} ✅ | {snapshot.total_failed} ❌",
            inline=False,
        )
        embed.add_field(
            name="Channels",
            value=guild_summary,
            inline=False,
        )
        embed.add_field(
            name="Performance",
            value=(
                f"📈 SUCCESS RATE: {self._success_rate(snapshot):.1f}%\n"
                f"⚡ AVG POST TIME: {snapshot.avg_post_time:.2f}s\n"
                f"🚨 LAST ERROR: {self._last_error(snapshot)}"
            ),
            inline=False,
        )
        return embed

    def _success_rate(self, snapshot: StatsSnapshot) -> float:
        total = snapshot.total_success + snapshot.total_failed
        return (snapshot.total_success / total * 100) if total else 0.0

    def _last_error(self, snapshot: StatsSnapshot) -> str:
        last_errors = [stat.last_error for stat in snapshot.channel_stats.values() if stat.last_error]
        return last_errors[-1] if last_errors else "N/A"
