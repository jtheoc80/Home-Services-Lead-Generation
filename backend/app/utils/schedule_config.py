#!/usr/bin/env python3
"""
Cron schedule configuration utility for managing scheduled tasks.

This module provides configuration for cron schedules from environment
variables and utilities for working with cron expressions.
"""

import os
import re
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CronSchedule:
    """Individual cron schedule configuration."""

    expression: str
    name: str
    description: Optional[str] = None

    def __post_init__(self):
        """Validate cron expression."""
        if not self.is_valid_cron():
            raise ValueError(f"Invalid cron expression: {self.expression}")

    def is_valid_cron(self) -> bool:
        """Validate cron expression format."""
        # Basic validation for 5-field cron expressions (minute hour day month weekday)
        if not self.expression:
            return False

        fields = self.expression.split()
        if len(fields) != 5:
            return False

        # Validate each field
        patterns = [
            r"^(\*|[0-5]?\d)$",  # minute (0-59)
            r"^(\*|[01]?\d|2[0-3])$",  # hour (0-23)
            r"^(\*|[012]?\d|3[01])$",  # day (1-31)
            r"^(\*|[01]?\d)$",  # month (1-12)
            r"^(\*|[0-6])$",  # weekday (0-6)
        ]

        for i, field in enumerate(fields):
            # Handle ranges, lists, and step values
            if "," in field:
                # List of values
                for value in field.split(","):
                    if not self._validate_field_value(value, i):
                        return False
            elif "/" in field:
                # Step values
                if not self._validate_step_value(field, i):
                    return False
            elif "-" in field:
                # Range values
                if not self._validate_range_value(field, i):
                    return False
            else:
                # Single value or *
                if not re.match(patterns[i], field):
                    return False

        return True

    def _validate_field_value(self, value: str, field_index: int) -> bool:
        """Validate individual field value."""
        patterns = [
            r"^(\*|[0-5]?\d)$",  # minute
            r"^(\*|[01]?\d|2[0-3])$",  # hour
            r"^(\*|[012]?\d|3[01])$",  # day
            r"^(\*|[01]?\d)$",  # month
            r"^(\*|[0-6])$",  # weekday
        ]
        return re.match(patterns[field_index], value) is not None

    def _validate_step_value(self, value: str, field_index: int) -> bool:
        """Validate step value (e.g., */5, 0-30/5)."""
        if "/" not in value:
            return False

        base, step = value.split("/", 1)
        try:
            step_num = int(step)
            if step_num <= 0:
                return False
        except ValueError:
            return False

        if base == "*":
            return True

        return self._validate_field_value(base, field_index)

    def _validate_range_value(self, value: str, field_index: int) -> bool:
        """Validate range value (e.g., 1-5)."""
        if "-" not in value:
            return False

        try:
            start, end = value.split("-", 1)
            start_num = int(start)
            end_num = int(end)
            return start_num <= end_num
        except ValueError:
            return False

    def get_next_run_time(
        self, current_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """Calculate next run time (basic implementation)."""
        # This would require a full cron parser library for accurate calculation
        # For now, return a placeholder
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        logger.info(
            f"Next run calculation for '{self.name}' would require cron parser library"
        )
        return None

    def get_human_readable(self) -> str:
        """Convert cron expression to human-readable format."""
        minute, hour, day, month, weekday = self.expression.split()

        parts = []

        # Handle minute
        if minute == "*":
            parts.append("every minute")
        elif minute == "0":
            parts.append("at the start of the hour")
        else:
            parts.append(f"at minute {minute}")

        # Handle hour
        if hour != "*":
            if hour == "0":
                parts.append("at midnight")
            else:
                parts.append(f"at hour {hour}")

        # Handle day
        if day != "*":
            parts.append(f"on day {day}")

        # Handle month
        if month != "*":
            parts.append(f"in month {month}")

        # Handle weekday
        if weekday != "*":
            weekdays = [
                "Sunday",
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
            ]
            if weekday.isdigit() and 0 <= int(weekday) <= 6:
                parts.append(f"on {weekdays[int(weekday)]}")

        return " ".join(parts)


@dataclass
class ScheduleConfig:
    """Configuration for all cron schedules."""

    schedules: Dict[str, CronSchedule]

    @classmethod
    def from_env(cls) -> "ScheduleConfig":
        """Create configuration from environment variables."""
        schedules = {}

        # Define default schedules with their environment variable names
        schedule_definitions = [
            ("CRON_SCRAPE_UTC", "scrape", "Data scraping schedule", "0 5 * * *"),
            (
                "CRON_DIGEST_HOURLY",
                "digest_hourly",
                "Hourly digest schedule",
                "0 * * * *",
            ),
            (
                "CRON_DIGEST_DAILY",
                "digest_daily",
                "Daily digest schedule",
                "0 13 * * *",
            ),
        ]

        for env_var, name, description, default in schedule_definitions:
            expression = os.getenv(env_var, default)
            try:
                schedules[name] = CronSchedule(
                    expression=expression, name=name, description=description
                )
            except ValueError as e:
                logger.error(f"Invalid cron expression for {env_var}: {e}")
                # Use default if environment variable is invalid
                schedules[name] = CronSchedule(
                    expression=default, name=name, description=description
                )

        return cls(schedules=schedules)

    def get_schedule(self, name: str) -> Optional[CronSchedule]:
        """Get schedule by name."""
        return self.schedules.get(name)

    def get_all_schedules(self) -> Dict[str, CronSchedule]:
        """Get all schedules."""
        return self.schedules.copy()

    def list_schedule_names(self) -> List[str]:
        """Get list of all schedule names."""
        return list(self.schedules.keys())


class ScheduleManager:
    """Manager for cron schedule configuration and operations."""

    def __init__(self, config: Optional[ScheduleConfig] = None):
        self.config = config or ScheduleConfig.from_env()

    def get_schedule_info(self, name: str) -> Optional[Dict[str, str]]:
        """Get detailed information about a schedule."""
        schedule = self.config.get_schedule(name)
        if not schedule:
            return None

        return {
            "name": schedule.name,
            "expression": schedule.expression,
            "description": schedule.description or "",
            "human_readable": schedule.get_human_readable(),
            "is_valid": schedule.is_valid_cron(),
        }

    def get_all_schedule_info(self) -> Dict[str, Dict[str, str]]:
        """Get information about all schedules."""
        info = {}
        for name in self.config.list_schedule_names():
            info[name] = self.get_schedule_info(name)
        return info

    def validate_schedules(self) -> Tuple[bool, List[str]]:
        """Validate all schedules and return status with any errors."""
        errors = []
        all_valid = True

        for name, schedule in self.config.get_all_schedules().items():
            if not schedule.is_valid_cron():
                all_valid = False
                errors.append(
                    f"Invalid cron expression for {name}: {schedule.expression}"
                )

        return all_valid, errors

    def get_schedule_summary(self) -> Dict[str, any]:
        """Get summary of schedule configuration."""
        schedules = self.config.get_all_schedules()
        is_valid, errors = self.validate_schedules()

        return {
            "total_schedules": len(schedules),
            "schedule_names": list(schedules.keys()),
            "all_valid": is_valid,
            "errors": errors,
            "schedules": {
                name: schedule.expression for name, schedule in schedules.items()
            },
        }

    def should_run_now(
        self, schedule_name: str, current_time: Optional[datetime] = None
    ) -> bool:
        """Check if a schedule should run now (simplified check)."""
        schedule = self.config.get_schedule(schedule_name)
        if not schedule:
            return False

        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # For a full implementation, this would need a cron parser library
        # For now, just return False as this is a configuration utility
        logger.info(
            f"Schedule check for '{schedule_name}' would require cron parser for accurate timing"
        )
        return False


# Global instance for easy access
_schedule_manager: Optional[ScheduleManager] = None


def get_schedule_manager() -> ScheduleManager:
    """Get global schedule manager instance."""
    global _schedule_manager
    if _schedule_manager is None:
        _schedule_manager = ScheduleManager()
    return _schedule_manager


def get_schedule_config() -> ScheduleConfig:
    """Get schedule configuration."""
    return get_schedule_manager().config
