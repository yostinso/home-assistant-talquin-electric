"""A container for daily usage data."""

from datetime import datetime


class TalquinElectricUsageEntry:
    """A class to represent a daily usage entry for Talquin Electric."""

    def __init__(self, date: datetime, usage: float) -> None:
        """Return a representation of a daily usage entry for Talquin Electric."""
        self.date = date
        self.usage = usage

    def __repr__(self) -> str:
        """Return string representation of usage."""
        return f"{{day: {self.date}, kWh: {self.usage}}}"

    def __eq__(self, value: object) -> bool:
        """Return True if TalquinElectricUsageEntry with the same date/usage."""
        if not isinstance(value, TalquinElectricUsageEntry):
            return False
        return self.date == value.date and self.usage == value.usage
