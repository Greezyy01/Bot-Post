from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ChannelConfig:
    channel_id: int
    message: str
    min_delay: int
    max_delay: int
    enabled: bool = True
    group: str = "default"
    schedule: str = "daily"
    templates: List[str] = field(default_factory=list)


@dataclass
class GuildConfig:
    owner_id: Optional[int] = None
    webhook_url: Optional[str] = None
    default_min_delay: int = 60
    default_max_delay: int = 300
    channels: List[ChannelConfig] = field(default_factory=list)
    dashboard_message_id: Optional[int] = None


@dataclass
class BotConfig:
    token_encrypted: Optional[str] = None
    guilds: Dict[str, GuildConfig] = field(default_factory=dict)


@dataclass
class ChannelStats:
    success: int = 0
    failed: int = 0
    last_error: Optional[str] = None
    last_posted_at: Optional[str] = None
    last_duration: float = 0.0


@dataclass
class StatsSnapshot:
    total_success: int = 0
    total_failed: int = 0
    avg_post_time: float = 0.0
    uptime: str = "0s"
    channel_stats: Dict[int, ChannelStats] = dataclasses.field(default_factory=dict)
