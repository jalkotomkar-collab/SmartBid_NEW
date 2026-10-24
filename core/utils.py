"""Formatting and time helpers shared across pages."""
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from .config import CURRENCY_SYMBOL, DISPLAY_TIMEZONE

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _group_indian(n: int) -> str:
    """12345678 -> '1,23,45,678' (lakh / crore grouping)."""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def format_inr(paise) -> str:
    """Format an integer amount in paise as rupees, e.g. 123456700 -> '₹12,34,567'."""
    paise = int(paise or 0)
    sign = "-" if paise < 0 else ""
    rupees, rem = divmod(abs(paise), 100)
    text = _group_indian(rupees)
    if rem:
        text += f".{rem:02d}"
    return f"{sign}{CURRENCY_SYMBOL}{text}"


def to_paise(amount) -> int:
    """Convert a rupee amount (number or string) to integer paise."""
    try:
        return int((Decimal(str(amount)) * 100).quantize(Decimal("1")))
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid amount in rupees.")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(ISO_FMT)


def parse_iso(value: str) -> datetime:
    return datetime.strptime(value[:19] + "Z", ISO_FMT).replace(tzinfo=timezone.utc)


def format_local(value: str, fmt: str = "%d %b %Y, %I:%M %p") -> str:
    """Show a stored UTC timestamp in the configured display timezone."""
    if not value:
        return ""
    return parse_iso(value).astimezone(ZoneInfo(DISPLAY_TIMEZONE)).strftime(fmt)


def time_left_text(end_iso: str) -> str:
    """Human-friendly countdown such as '2d 4h', '3h 12m' or '45s'."""
    seconds = int((parse_iso(end_iso) - now_utc()).total_seconds())
    if seconds <= 0:
        return "Ended"
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def local_to_iso(d: date, t: time) -> str:
    """Interpret a date and time entered in the display timezone; return UTC ISO."""
    return to_iso(datetime.combine(d, t).replace(tzinfo=ZoneInfo(DISPLAY_TIMEZONE)))


def now_epoch() -> int:
    return int(now_utc().timestamp())


def mask_name(username: str) -> str:
    """Show bidders without exposing full usernames: 'rahul_k' -> 'r***k'."""
    if not username:
        return ""
    if len(username) <= 2:
        return username[0] + "***"
    return f"{username[0]}***{username[-1]}"


_MD_SPECIAL = set("\\`*_{}[]()#+-.!>|~$<&")


def md_escape(text: str) -> str:
    """Show user-written text literally (no markdown, links or images), keeping line breaks."""
    out = "".join("\\" + ch if ch in _MD_SPECIAL else ch for ch in (text or ""))
    return out.replace("\r\n", "\n").replace("\n", "  \n")


def mask_name(username: str) -> str:
    """Show only the edges of a username, e.g. 'bobby' -> 'b***y'."""
    username = username or ""
    if len(username) <= 2:
        return username[:1] + "***"
    return username[0] + "***" + username[-1]
