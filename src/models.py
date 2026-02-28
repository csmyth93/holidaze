from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ItemCategory(Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    TRANSFER = "transfer"
    ACTIVITY = "activity"


@dataclass
class TravelItem:
    id: str
    category: ItemCategory
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    details: dict = field(default_factory=dict)

    @property
    def start_date_obj(self) -> Optional[datetime]:
        """Parse start_date string to datetime."""
        if self.start_date:
            return datetime.fromisoformat(self.start_date)
        return None

    @property
    def end_date_obj(self) -> Optional[datetime]:
        """Parse end_date string to datetime."""
        if self.end_date:
            return datetime.fromisoformat(self.end_date)
        return None

    @property
    def formatted_date(self) -> str:
        """Format date for display."""
        if not self.start_date_obj:
            return ""
        start = self.start_date_obj.strftime("%b %d")
        if self.end_date_obj and self.end_date != self.start_date:
            end = self.end_date_obj.strftime("%b %d")
            return f"{start} - {end}"
        return start


@dataclass
class Itinerary:
    title: str
    destination: str
    participants: list[str] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    items: list[TravelItem] = field(default_factory=list)

    @property
    def formatted_dates(self) -> str:
        """Format date range for display."""
        if self.start_date and self.end_date:
            start = datetime.fromisoformat(self.start_date).strftime("%B %d")
            end = datetime.fromisoformat(self.end_date).strftime("%d, %Y")
            return f"{start} - {end}"
        return ""

    def items_by_date(self) -> dict[str, list[TravelItem]]:
        """Group items by their start date."""
        grouped: dict[str, list[TravelItem]] = {}
        for item in self.items:
            if item.start_date:
                if item.start_date not in grouped:
                    grouped[item.start_date] = []
                grouped[item.start_date].append(item)
        return dict(sorted(grouped.items()))

    def items_by_category(self) -> dict[ItemCategory, list[TravelItem]]:
        """Group items by category."""
        grouped: dict[ItemCategory, list[TravelItem]] = {}
        for item in self.items:
            if item.category not in grouped:
                grouped[item.category] = []
            grouped[item.category].append(item)
        return grouped
