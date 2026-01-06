import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles

from models import BotConfig, ChannelConfig, GuildConfig
from utils import decrypt_token, encrypt_token


class ConfigManager:
    def __init__(self, path: str = "config.json") -> None:
        self.path = Path(path)
        self.data = BotConfig()

    async def load(self) -> None:
        if not self.path.exists():
            await self.save()
            return
        async with aiofiles.open(self.path, "r", encoding="utf-8") as handle:
            raw = await handle.read()
        payload = json.loads(raw) if raw else {}
        self.data = self._deserialize(payload)

    async def save(self) -> None:
        payload = self._serialize()
        async with aiofiles.open(self.path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(payload, indent=2))

    def get_token(self) -> Optional[str]:
        env_token = os.getenv("BOT_TOKEN")
        if env_token:
            return env_token
        if not self.data.token_encrypted:
            return None
        return decrypt_token(self.data.token_encrypted)

    async def set_token(self, token: str) -> None:
        self.data.token_encrypted = encrypt_token(token)
        await self.save()

    def get_guild(self, guild_id: int) -> GuildConfig:
        key = str(guild_id)
        if key not in self.data.guilds:
            self.data.guilds[key] = GuildConfig()
        return self.data.guilds[key]

    async def update_guild(self, guild_id: int, updates: Dict[str, Any]) -> None:
        guild = self.get_guild(guild_id)
        for key, value in updates.items():
            if hasattr(guild, key):
                setattr(guild, key, value)
        await self.save()

    async def add_channel(self, guild_id: int, channel: ChannelConfig) -> None:
        guild = self.get_guild(guild_id)
        guild.channels.append(channel)
        await self.save()

    async def remove_all_channels(self, guild_id: int) -> None:
        guild = self.get_guild(guild_id)
        guild.channels = []
        await self.save()

    async def backup(self, directory: str = "backups") -> Path:
        directory_path = Path(directory)
        directory_path.mkdir(parents=True, exist_ok=True)
        backup_path = directory_path / f"config-backup-{os.urandom(4).hex()}.json"
        async with aiofiles.open(self.path, "r", encoding="utf-8") as handle:
            content = await handle.read()
        async with aiofiles.open(backup_path, "w", encoding="utf-8") as handle:
            await handle.write(content)
        return backup_path

    async def restore(self, backup_path: str) -> None:
        async with aiofiles.open(backup_path, "r", encoding="utf-8") as handle:
            content = await handle.read()
        async with aiofiles.open(self.path, "w", encoding="utf-8") as handle:
            await handle.write(content)
        await self.load()

    def _serialize(self) -> Dict[str, Any]:
        payload = asdict(self.data)
        payload["guilds"] = {
            guild_id: self._serialize_guild(guild)
            for guild_id, guild in self.data.guilds.items()
        }
        return payload

    def _serialize_guild(self, guild: GuildConfig) -> Dict[str, Any]:
        return {
            "owner_id": guild.owner_id,
            "webhook_url": guild.webhook_url,
            "default_min_delay": guild.default_min_delay,
            "default_max_delay": guild.default_max_delay,
            "dashboard_message_id": guild.dashboard_message_id,
            "channels": [asdict(channel) for channel in guild.channels],
        }

    def _deserialize(self, payload: Dict[str, Any]) -> BotConfig:
        config = BotConfig()
        config.token_encrypted = payload.get("token_encrypted")
        guilds_raw = payload.get("guilds", {})
        for guild_id, guild_data in guilds_raw.items():
            guild = GuildConfig(
                owner_id=guild_data.get("owner_id"),
                webhook_url=guild_data.get("webhook_url"),
                default_min_delay=guild_data.get("default_min_delay", 60),
                default_max_delay=guild_data.get("default_max_delay", 300),
                dashboard_message_id=guild_data.get("dashboard_message_id"),
                channels=[
                    ChannelConfig(
                        channel_id=ch.get("channel_id"),
                        message=ch.get("message"),
                        min_delay=ch.get("min_delay"),
                        max_delay=ch.get("max_delay"),
                        enabled=ch.get("enabled", True),
                        group=ch.get("group", "default"),
                        schedule=ch.get("schedule", "daily"),
                        templates=ch.get("templates", []),
                    )
                    for ch in guild_data.get("channels", [])
                ],
            )
            config.guilds[guild_id] = guild
        return config
