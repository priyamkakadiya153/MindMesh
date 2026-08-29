import logging
from datetime import datetime, timedelta, timezone as dt_timezone
import zoneinfo
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

DAY_MAP = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6
}

class ScheduleCalculator:
    """Calculates next execution UTC datetimes for scheduled automations."""

    @classmethod
    def calculate_next_run(
        cls,
        schedule_type: str,
        time_str: Optional[str] = None,
        day_of_week: Optional[str] = None,
        tz_name: str = "Asia/Kolkata",
        from_utc: Optional[datetime] = None,
        recurrence_rule: Optional[str] = None
    ) -> Optional[datetime]:
        try:
            tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            tz = zoneinfo.ZoneInfo("UTC")

        if recurrence_rule and not day_of_week and "every_" in recurrence_rule:
            day_of_week = recurrence_rule.replace("every_", "").title()

        now_utc = from_utc or datetime.now(dt_timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=dt_timezone.utc)
        now_local = now_utc.astimezone(tz)

        target_hour = 9
        target_minute = 0

        if time_str:
            import re
            m = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_str.lower())
            if m:
                hr = int(m.group(1))
                mn = int(m.group(2)) if m.group(2) else 0
                ampm = m.group(3)
                if ampm == "pm" and hr < 12:
                    hr += 12
                elif ampm == "am" and hr == 12:
                    hr = 0
                target_hour = hr
                target_minute = mn

        st = schedule_type.upper()

        if st == "ONE_TIME":
            # If from_utc is in the future, use it directly
            if from_utc and from_utc > datetime.now(dt_timezone.utc):
                return from_utc.replace(tzinfo=None) if from_utc.tzinfo else from_utc
            # Default one-time offset (e.g. 2 minutes if unspecified)
            return (now_utc + timedelta(minutes=2)).replace(tzinfo=None) if now_utc.tzinfo else now_utc + timedelta(minutes=2)

        elif st == "DAILY":
            next_local = now_local.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if next_local <= now_local:
                next_local += timedelta(days=1)
            return next_local.astimezone(dt_timezone.utc).replace(tzinfo=None)

        elif st == "WEEKLY":
            target_dow = 0 # Default Monday
            if day_of_week and day_of_week.lower() in DAY_MAP:
                target_dow = DAY_MAP[day_of_week.lower()]

            current_dow = now_local.weekday()
            days_ahead = target_dow - current_dow
            if days_ahead < 0 or (days_ahead == 0 and now_local.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0) <= now_local):
                days_ahead += 7

            next_local = now_local.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0) + timedelta(days=days_ahead)
            return next_local.astimezone(dt_timezone.utc).replace(tzinfo=None)

        elif st == "WEEKDAYS":
            next_local = now_local.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if next_local <= now_local:
                next_local += timedelta(days=1)

            # Skip Saturday (5) and Sunday (6)
            while next_local.weekday() in (5, 6):
                next_local += timedelta(days=1)

            return next_local.astimezone(dt_timezone.utc).replace(tzinfo=None)

        elif st == "MONTHLY":
            next_local = now_local.replace(day=1, hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if next_local <= now_local:
                # Advance month
                if next_local.month == 12:
                    next_local = next_local.replace(year=next_local.year + 1, month=1)
                else:
                    next_local = next_local.replace(month=next_local.month + 1)
            return next_local.astimezone(dt_timezone.utc).replace(tzinfo=None)

        else:
            # Fallback daily
            next_local = now_local.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0) + timedelta(days=1)
            return next_local.astimezone(dt_timezone.utc).replace(tzinfo=None)
