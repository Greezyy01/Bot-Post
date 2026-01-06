import asyncio
from typing import Dict

import discord

from models import ChannelConfig
from utils import sleep_with_jitter


class PostScheduler:
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self.running = False
        self.tasks: Dict[tuple[int, int], asyncio.Task] = {}

    async def start_all(self) -> None:
        self.running = True
        for guild in self.bot.guilds:
            await self.start_guild(guild.id)

    async def stop_all(self) -> None:
        self.running = False
        for task in list(self.tasks.values()):
            task.cancel()
        self.tasks = {}

    async def start_guild(self, guild_id: int) -> None:
        guild_config = self.bot.config.get_guild(guild_id)
        for channel in guild_config.channels:
            await self._start_channel(guild_id, channel)

    async def _start_channel(self, guild_id: int, channel_cfg: ChannelConfig) -> None:
        if not channel_cfg.enabled:
            return
        task_key = self._task_key(guild_id, channel_cfg.channel_id)
        if task_key in self.tasks:
            return
        self.tasks[task_key] = asyncio.create_task(
            self._run_channel(guild_id, channel_cfg),
            name=f"autopost:{guild_id}:{channel_cfg.channel_id}",
        )

    async def pause_guild(self, guild_id: int) -> None:
        for task_key in list(self.tasks.keys()):
            if task_key[0] == guild_id:
                self.tasks[task_key].cancel()
                self.tasks.pop(task_key, None)

    async def _run_channel(self, guild_id: int, channel_cfg: ChannelConfig) -> None:
        while self.running and channel_cfg.enabled:
            await sleep_with_jitter(channel_cfg.min_delay, channel_cfg.max_delay)
            if not self.running or not channel_cfg.enabled:
                continue
            await self.bot.post_to_channel(guild_id, channel_cfg)

    def _task_key(self, guild_id: int, channel_id: int) -> tuple[int, int]:
        return (guild_id, channel_id)
