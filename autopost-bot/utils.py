import asyncio
import base64
import datetime as dt
import logging
from pathlib import Path
import random
from typing import Any, Dict, Optional

import aiohttp
import humanize
import pytz
from colorama import Fore, Style

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logger(name: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


def colorize(level: str, message: str) -> str:
    color = {
        "INFO": Fore.CYAN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "SUCCESS": Fore.GREEN,
    }.get(level, Fore.WHITE)
    return f"{color}{message}{Style.RESET_ALL}"


def encrypt_token(token: str) -> str:
    encoded = base64.b64encode(token.encode("utf-8")).decode("utf-8")
    return encoded


def decrypt_token(token: str) -> str:
    try:
        return base64.b64decode(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return token


def utcnow() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


def format_uptime(started_at: Optional[dt.datetime]) -> str:
    if not started_at:
        return "0s"
    delta = utcnow() - started_at
    return humanize.naturaldelta(delta)


def render_template(
    template: str, *, channel_name: str, guild_name: str
) -> str:
    now = dt.datetime.now(tz=pytz.UTC)
    replacements = {
        "{channel}": channel_name,
        "{guild}": guild_name,
        "{date}": now.strftime("%Y-%m-%d"),
        "{time}": now.strftime("%H:%M:%S UTC"),
    }
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    return rendered


async def send_webhook_log(webhook_url: str, payload: Dict[str, Any]) -> None:
    if not webhook_url:
        return
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(webhook_url, json=payload, timeout=10) as resp:
                await resp.read()
        except Exception:
            return


def random_delay(min_delay: int, max_delay: int) -> int:
    return random.randint(min_delay, max_delay)


async def sleep_with_jitter(min_delay: int, max_delay: int) -> None:
    await asyncio.sleep(random_delay(min_delay, max_delay))
