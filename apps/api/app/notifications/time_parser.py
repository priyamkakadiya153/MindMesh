import re
import logging
from typing import Tuple
from datetime import datetime, timedelta, timezone, time

logger = logging.getLogger(__name__)

# Default offset for Asia/Kolkata (IST = UTC+5:30)
DEFAULT_TIMEZONE = "Asia/Kolkata"
IST_OFFSET = timedelta(hours=5, minutes=30)

class NaturalTimeParser:
    """Parses natural language date/time strings into UTC datetime objects."""

    @classmethod
    def parse_time(cls, text: str, user_timezone: str = DEFAULT_TIMEZONE) -> Tuple[datetime, str]:
        """
        Parses text like 'in 2 minutes', 'tomorrow at 10 AM', 'in 1 hour'
        Returns (utc_datetime, formatted_local_time_str).
        """
        q_lower = text.lower().strip()
        now_utc = datetime.now(timezone.utc)

        # Local reference time (IST: UTC + 5:30)
        now_local = now_utc + IST_OFFSET

        # 1. Check relative "in X minutes" or "in X hours" or "in X days"
        rel_match = re.search(r'\bin\s+(\d+)\s+(minute|min|hour|hr|day|sec|second)s?\b', q_lower)
        if rel_match:
            amount = int(rel_match.group(1))
            unit = rel_match.group(2)
            if "min" in unit or "sec" in unit:
                target_local = now_local + timedelta(minutes=amount)
            elif "hour" in unit or "hr" in unit:
                target_local = now_local + timedelta(hours=amount)
            elif "day" in unit:
                target_local = now_local + timedelta(days=amount)
            else:
                target_local = now_local + timedelta(minutes=amount)

            target_utc = target_local - IST_OFFSET
            return target_utc, target_local.strftime("%B %d, %Y at %I:%M %p")

        # 2. Check "tomorrow at HH:MM AM/PM" or "tomorrow morning/evening"
        if "tomorrow" in q_lower:
            tomorrow_date = (now_local + timedelta(days=1)).date()
            hour, minute = 10, 0 # default 10 AM

            time_match = re.search(r'\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', q_lower)
            if time_match:
                h = int(time_match.group(1))
                m = int(time_match.group(2)) if time_match.group(2) else 0
                ampm = time_match.group(3)
                if ampm == "pm" and h < 12:
                    h += 12
                elif ampm == "am" and h == 12:
                    h = 0
                hour, minute = h, m
            elif "evening" in q_lower:
                hour, minute = 18, 0
            elif "afternoon" in q_lower:
                hour, minute = 14, 0

            target_local = datetime.combine(tomorrow_date, time(hour, minute), tzinfo=timezone.utc)
            target_utc = target_local - IST_OFFSET
            return target_utc, target_local.strftime("%B %d, %Y at %I:%M %p")

        # 3. Default fallback: 1 hour from now if unparsed
        target_local = now_local + timedelta(hours=1)
        target_utc = target_local - IST_OFFSET
        return target_utc, target_local.strftime("%B %d, %Y at %I:%M %p")
