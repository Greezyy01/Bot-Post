from __future__ import annotations

import asyncio
import datetime as dt
import os
from typing import Optional

import discord
from discord.ext import commands

from commands import CommandRegistrar
from config import ConfigManager
from dashboard import DashboardManager, DashboardView
from models import ChannelConfig, ChannelStats, StatsSnapshot
from scheduler import PostScheduler
from utils import format_uptime, render_template, send_webhook_log, setup_logger, utcnow


class StatsTracker:
    def __init__(self) -> None:
        self.started_at: Optional[dt.datetime] = None
        self.channel_stats: dict[int, ChannelStats] = {}

    def start(self) -> None:
        self.started_at = utcnow()

    def record_success(self, channel_id: int, duration: float) -> None:
        stats = self.channel_stats.setdefault(channel_id, ChannelStats())
        stats.success += 1
        stats.last_duration = duration

    def record_failure(self, channel_id: int, error: str) -> None:
        stats = self.channel_stats.setdefault(channel_id, ChannelStats())
        stats.failed += 1
        stats.last_error = error

    def snapshot(self) -> StatsSnapshot:
        total_success = sum(stat.success for stat in self.channel_stats.values())
        total_failed = sum(stat.failed for stat in self.channel_stats.values())
        durations = [stat.last_duration for stat in self.channel_stats.values() if stat.last_duration]
        avg_post_time = sum(durations) / len(durations) if durations else 0.0
        return StatsSnapshot(
            total_success=total_success,
            total_failed=total_failed,
            avg_post_time=avg_post_time,
            uptime=format_uptime(self.started_at),
            channel_stats=self.channel_stats,
        )


class AutoPostBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.config = ConfigManager()
        self.scheduler = PostScheduler(self)
        self.dashboard = DashboardManager(self)
        self.dashboard_view = DashboardView(self)
        self.stats = StatsTracker()
        self.started_at: Optional[dt.datetime] = None
        self.logger = setup_logger("autopost", "logs/autopost.log")

    async def setup_hook(self) -> None:
        await self.config.load()
        self.stats.start()
        self.started_at = utcnow()
        self.add_view(self.dashboard_view)
        CommandRegistrar(self).register()
        await self.tree.sync()

    async def on_ready(self) -> None:
        self.logger.info("Bot ready as %s", self.user)

    async def post_to_channel(self, guild_id: int, channel_cfg: ChannelConfig) -> None:
        channel = self.get_channel(channel_cfg.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        guild = self.get_guild(guild_id)
        message = self._select_message(channel_cfg)
        if guild:
            message = render_template(message, channel_name=channel.name, guild_name=guild.name)

        await self._send_with_retry(channel, message, channel_cfg, guild_id)

    async def _send_with_retry(
        self,
        channel: discord.TextChannel,
        message: str,
        channel_cfg: ChannelConfig,
        guild_id: int,
    ) -> None:
        retries = 0
        backoff = 2
        start = asyncio.get_event_loop().time()
        while retries < 5:
            try:
                await channel.send(message)
                duration = asyncio.get_event_loop().time() - start
                self.stats.record_success(channel.id, duration)
                await self._log_success(channel, guild_id)
                return
            except discord.HTTPException as exc:
                self.stats.record_failure(channel.id, str(exc))
                if exc.status == 429 and exc.retry_after:
                    await asyncio.sleep(exc.retry_after)
                    continue
                await asyncio.sleep(backoff)
                backoff *= 2
                retries += 1
            except Exception as exc:  # noqa: BLE001
                self.stats.record_failure(channel.id, str(exc))
                await asyncio.sleep(backoff)
                backoff *= 2
                retries += 1

    async def _log_success(self, channel: discord.TextChannel, guild_id: int) -> None:
        guild_config = self.config.get_guild(guild_id)
        self.logger.info("Posted to #%s", channel.name)
        await send_webhook_log(
            guild_config.webhook_url or "",
            {"content": f"✅ Posted to {channel.mention}"},
        )

    def _select_message(self, channel_cfg: ChannelConfig) -> str:
        if channel_cfg.templates:
            return channel_cfg.templates[0]
        return channel_cfg.message

    async def build_dashboard_embed(self, guild_id: Optional[int]) -> discord.Embed:
        snapshot = self.stats.snapshot()
        status = "RUNNING" if self.scheduler.running else "STOPPED"
        summary = await self._guild_summary(guild_id)
        return self.dashboard.build_embed(snapshot, status, summary)

    async def build_config_embed(self, guild_id: Optional[int]) -> discord.Embed:
        embed = discord.Embed(title="⚙️ Config")
        if not guild_id:
            embed.description = "Tidak ada guild."
            return embed
        guild = self.config.get_guild(guild_id)
        embed.add_field(name="Owner", value=str(guild.owner_id), inline=False)
        embed.add_field(
            name="Default Delay",
            value=f"{guild.default_min_delay}-{guild.default_max_delay}s",
            inline=False,
        )
        embed.add_field(name="Webhook", value=str(guild.webhook_url), inline=False)
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=False)
        return embed

    def build_stats_embed(self, snapshot: StatsSnapshot) -> discord.Embed:
        embed = discord.Embed(title="📊 AutoPost Stats")
        embed.add_field(
            name="Totals",
            value=f"{snapshot.total_success} ✅ | {snapshot.total_failed} ❌",
            inline=False,
        )
        embed.add_field(name="Avg Post Time", value=f"{snapshot.avg_post_time:.2f}s")
        embed.add_field(name="Uptime", value=snapshot.uptime)
        return embed

    async def _guild_summary(self, guild_id: Optional[int]) -> str:
        if not guild_id:
            return "N/A"
        guild = self.config.get_guild(guild_id)
        lines = []
        for idx, channel_cfg in enumerate(guild.channels[:4], start=1):
            status = "✅" if channel_cfg.enabled else "⏸️"
            lines.append(f"CHANNEL #{idx}: {status} {channel_cfg.min_delay}s-{channel_cfg.max_delay}s")
        if not lines:
            lines.append("Belum ada channel aktif.")
        return "\n".join(lines)


async def main() -> None:
    bot = AutoPostBot()
    token = bot.config.get_token()
    if not token:
        raise RuntimeError("Token belum diset. Jalankan /setup atau set BOT_TOKEN env.")
    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
