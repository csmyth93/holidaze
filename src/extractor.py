import re
from datetime import date
from typing import Optional
from urllib.parse import urlparse, parse_qs

import dateparser

from .models import Message, TravelItem, ItemCategory, ItemStatus, Itinerary


# Patterns for extraction
BOOKING_URL_PATTERN = re.compile(r"https?://(?:www\.)?booking\.com/[^\s]+", re.IGNORECASE)
COST_PATTERN = re.compile(r"£(\d{1,4}(?:\.\d{2})?)\s*(?:pp|per person|each)?", re.IGNORECASE)
DATE_PATTERN = re.compile(
    r"(\d{1,2})(?:st|nd|rd|th)?\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*(\d{4})?",
    re.IGNORECASE
)

# Airlines - use regex patterns with word boundaries to avoid false positives
AIRLINE_PATTERNS = [
    (re.compile(r"\bEtihad\b", re.IGNORECASE), "Etihad"),
    (re.compile(r"\bAir\s*Asia\b", re.IGNORECASE), "Air Asia"),
    (re.compile(r"\bThai\s*Airways\b", re.IGNORECASE), "Thai Airways"),
    (re.compile(r"\bQatar\b(?!\s+(?:hotel|resort))", re.IGNORECASE), "Qatar"),
    (re.compile(r"\bBritish\s*Airways\b", re.IGNORECASE), "British Airways"),
    (re.compile(r"\bViet\s*Jet\b", re.IGNORECASE), "VietJet"),
    (re.compile(r"\bOman\s*Air\b", re.IGNORECASE), "Oman Air"),
]

# Flight context keywords - message must contain one of these alongside airline mention
FLIGHT_CONTEXT = ["flight", "fly", "flying", "depart", "arrive", "layover", "airport", "LHR", "BKK", "booking", "£"]

TRANSFER_KEYWORDS = ["ferry", "speedboat", "longtail boat"]  # More specific to avoid false positives

# Confirmation patterns
CONFIRMATION_PATTERNS = [
    re.compile(r"\bbooked!?\b", re.IGNORECASE),
    re.compile(r"\ball done\b", re.IGNORECASE),
    re.compile(r"\ball booked\b", re.IGNORECASE),
    re.compile(r"\bjust booked\b", re.IGNORECASE),
    re.compile(r"\bsorted\b", re.IGNORECASE),
    re.compile(r"\bconfirmed\b", re.IGNORECASE),
    re.compile(r"\bThis is booked\b", re.IGNORECASE),
]


class EntityExtractor:
    """Extract travel entities from WhatsApp messages."""

    def __init__(self, messages: list[Message]):
        self.messages = [m for m in messages if not m.is_system]
        self.item_counter = 0

    def extract_all(self, confirmed_only: bool = True) -> list[TravelItem]:
        """Extract all travel items from messages.

        Args:
            confirmed_only: If True, only return items with confirmed status.
        """
        items: list[TravelItem] = []

        items.extend(self._extract_hotels())
        items.extend(self._extract_flights())
        items.extend(self._extract_transfers())

        # Filter to confirmed only if requested
        if confirmed_only:
            items = [item for item in items if item.status == ItemStatus.CONFIRMED]
            # For hotels, only keep one per location to avoid showing alternatives
            items = self._dedupe_by_location(items)

        # Sort by date
        items.sort(key=lambda x: x.start_date or date.max)
        return items

    def _dedupe_by_location(self, items: list[TravelItem]) -> list[TravelItem]:
        """Keep only the first hotel for each location."""
        # Location keywords to group by
        location_keywords = {
            "lipe": "Koh Lipe",
            "kradan": "Koh Kradan",
            "libong": "Koh Libong",
            "lanta": "Koh Lanta",
            "bangkok": "Bangkok",
            "sukhumvit": "Bangkok",
            "riverside": "Bangkok",
        }

        seen_locations: set[str] = set()
        result: list[TravelItem] = []

        for item in items:
            if item.category != ItemCategory.HOTEL:
                result.append(item)
                continue

            # Determine location from hotel name
            title_lower = item.title.lower()
            location = None
            for keyword, loc in location_keywords.items():
                if keyword in title_lower:
                    location = loc
                    break

            # If we haven't seen this location, keep the item
            if location is None or location not in seen_locations:
                result.append(item)
                if location:
                    seen_locations.add(location)

        return result

    def _generate_id(self) -> str:
        """Generate unique item ID."""
        self.item_counter += 1
        return f"item-{self.item_counter}"

    def _extract_hotels(self) -> list[TravelItem]:
        """Extract hotel bookings from booking.com links and text mentions."""
        items: list[TravelItem] = []
        seen_hotels: set[str] = set()

        # Pattern for "Check out X on Booking.com"
        checkout_pattern = re.compile(r"Check out ([^!]+?) on Booking\.com", re.IGNORECASE)

        for i, msg in enumerate(self.messages):
            urls = BOOKING_URL_PATTERN.findall(msg.content)
            hotel_name = None
            check_in = None
            check_out = None
            booking_link = None

            # First try to extract hotel name from "Check out X on Booking.com" pattern
            checkout_match = checkout_pattern.search(msg.content)
            if checkout_match:
                hotel_name = checkout_match.group(1).strip()

            # Also try to extract from URL path
            for url in urls:
                url_hotel_name = self._extract_hotel_name_from_url(url)
                if url_hotel_name and not hotel_name:
                    hotel_name = url_hotel_name
                # Extract dates from URL
                url_check_in, url_check_out = self._extract_dates_from_booking_url(url)
                if url_check_in:
                    check_in = url_check_in
                    check_out = url_check_out
                booking_link = url

            # If no dates from URL, try to extract from nearby messages
            if not check_in:
                check_in = self._extract_date_from_context(i)

            if not hotel_name:
                continue

            # Normalize hotel name for deduplication
            hotel_key = hotel_name.lower().strip()
            if hotel_key in seen_hotels:
                continue
            seen_hotels.add(hotel_key)

            # Look for confirmation in surrounding messages
            status = self._check_confirmation(i)

            item = TravelItem(
                id=self._generate_id(),
                category=ItemCategory.HOTEL,
                status=status,
                title=hotel_name,
                start_date=check_in,
                end_date=check_out,
                proposed_by=msg.sender,
                booking_links=[booking_link] if booking_link else [],
                source_messages=[msg],
            )
            items.append(item)

        return items

    def _extract_hotel_name_from_url(self, url: str) -> Optional[str]:
        """Extract hotel name from booking.com URL."""
        parsed = urlparse(url)
        path = parsed.path

        # Pattern: /hotel/th/hotel-name-here.en-gb.html
        match = re.search(r"/hotel/\w+/([^/.]+)", path)
        if match:
            name = match.group(1)
            # Convert hyphens to spaces and title case
            name = name.replace("-", " ").title()
            return name
        return None

    def _extract_dates_from_booking_url(self, url: str) -> tuple[Optional[date], Optional[date]]:
        """Extract check-in and check-out dates from booking.com URL."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        check_in = None
        check_out = None

        if "checkin" in params:
            try:
                check_in = date.fromisoformat(params["checkin"][0])
            except ValueError:
                pass

        if "checkout" in params:
            try:
                check_out = date.fromisoformat(params["checkout"][0])
            except ValueError:
                pass

        return check_in, check_out

    def _extract_flights(self) -> list[TravelItem]:
        """Extract flight information from messages."""
        items: list[TravelItem] = []
        seen_flights: set[str] = set()

        for i, msg in enumerate(self.messages):
            content_lower = msg.content.lower()

            # Must have flight context to be considered a flight message
            has_flight_context = any(ctx.lower() in content_lower for ctx in FLIGHT_CONTEXT)
            if not has_flight_context:
                continue

            # Check for airline mentions using regex patterns
            for pattern, airline_name in AIRLINE_PATTERNS:
                if pattern.search(msg.content):
                    # Extract any costs
                    costs = COST_PATTERN.findall(msg.content)
                    cost = costs[0] if costs else None

                    # Try to identify route
                    route = self._identify_route(msg.content)

                    # Extract date from booking URL if present
                    flight_date = self._extract_date_from_booking_url_in_text(msg.content)
                    if not flight_date:
                        flight_date = self._extract_date_from_context(i)

                    # Create a dedup key based on airline + route + date
                    dedup_key = f"{airline_name}-{route or 'unknown'}-{flight_date or 'nodate'}"
                    if dedup_key in seen_flights:
                        continue
                    seen_flights.add(dedup_key)

                    # Check for confirmation
                    status = self._check_confirmation(i)

                    # Only include if confirmed or has a date
                    if status != ItemStatus.CONFIRMED and not flight_date:
                        continue

                    details = {}
                    if cost:
                        details["cost"] = f"£{cost}"

                    title = f"{airline_name} Flight"
                    if route:
                        title = f"{airline_name} {route}"

                    item = TravelItem(
                        id=self._generate_id(),
                        category=ItemCategory.FLIGHT,
                        status=status,
                        title=title,
                        start_date=flight_date,
                        proposed_by=msg.sender,
                        details=details,
                        source_messages=[msg],
                    )
                    items.append(item)
                    break  # One flight per message

        return items

    def _extract_date_from_booking_url_in_text(self, text: str) -> Optional[date]:
        """Extract date from any booking URL in the text."""
        urls = BOOKING_URL_PATTERN.findall(text)
        for url in urls:
            check_in, _ = self._extract_dates_from_booking_url(url)
            if check_in:
                return check_in
        return None

    def _identify_route(self, content: str) -> Optional[str]:
        """Try to identify flight route from content."""
        # Common airport codes and cities
        airports = {
            "LHR": "London",
            "BKK": "Bangkok",
            "Phuket": "Phuket",
            "Krabi": "Krabi",
            "Lanta": "Koh Lanta",
        }

        found = []
        content_upper = content.upper()

        for code in airports.keys():
            if code.upper() in content_upper:
                found.append(code)

        if len(found) >= 2:
            return f"{found[0]} → {found[1]}"
        return None

    def _extract_transfers(self) -> list[TravelItem]:
        """Extract ferry/boat/transfer information."""
        items: list[TravelItem] = []
        seen_transfers: set[str] = set()

        for i, msg in enumerate(self.messages):
            content = msg.content.lower()

            for keyword in TRANSFER_KEYWORDS:
                if keyword in content:
                    # Check for time patterns like "10:45" or "10.45"
                    time_match = re.search(r"(\d{1,2})[:.:](\d{2})", msg.content)
                    time_str = None
                    if time_match:
                        time_str = f"{time_match.group(1)}:{time_match.group(2)}"

                    # Try to identify route/destination
                    islands = ["Koh Lipe", "Koh Lanta", "Koh Kradan", "Koh Libong", "Koh Mook", "Koh Ngai", "Lipe", "Lanta", "Kradan", "Libong"]
                    route_parts = []
                    for island in islands:
                        if island.lower() in content:
                            # Normalize island names
                            normalized = island.replace("Koh ", "")
                            if normalized not in route_parts:
                                route_parts.append(normalized)

                    status = self._check_confirmation(i)
                    transfer_date = self._extract_date_from_context(i)

                    # Only include if confirmed or has specific route/time info
                    if status != ItemStatus.CONFIRMED and not (route_parts or time_str):
                        continue

                    title = keyword.title()
                    if len(route_parts) >= 2:
                        title = f"{keyword.title()} {route_parts[0]} → {route_parts[1]}"
                    elif route_parts:
                        title = f"{keyword.title()} to {route_parts[0]}"

                    # Dedup key
                    dedup_key = f"{keyword}-{'-'.join(sorted(route_parts))}-{transfer_date or 'nodate'}"
                    if dedup_key in seen_transfers:
                        continue
                    seen_transfers.add(dedup_key)

                    details = {}
                    if time_str:
                        details["time"] = time_str

                    item = TravelItem(
                        id=self._generate_id(),
                        category=ItemCategory.TRANSFER,
                        status=status,
                        title=title,
                        start_date=transfer_date,
                        proposed_by=msg.sender,
                        details=details,
                        source_messages=[msg],
                    )
                    items.append(item)
                    break  # One transfer per message

        return items

    def _check_confirmation(self, message_index: int, window: int = 8) -> ItemStatus:
        """Check if messages around the index contain confirmation.

        Uses a narrow window to avoid catching unrelated confirmations.
        """
        start = max(0, message_index - 3)
        end = min(len(self.messages), message_index + window)

        for msg in self.messages[start:end]:
            for pattern in CONFIRMATION_PATTERNS:
                if pattern.search(msg.content):
                    return ItemStatus.CONFIRMED

        return ItemStatus.TENTATIVE

    def _extract_date_from_context(self, message_index: int, window: int = 5) -> Optional[date]:
        """Try to extract a date from nearby messages."""
        start = max(0, message_index - window)
        end = min(len(self.messages), message_index + window)

        for msg in self.messages[start:end]:
            # Look for date patterns
            match = DATE_PATTERN.search(msg.content)
            if match:
                day, month, year = match.groups()
                year = year or "2026"  # Default to trip year
                date_str = f"{day} {month} {year}"
                parsed = dateparser.parse(date_str)
                if parsed:
                    return parsed.date()

        return None

    def build_itinerary(self, title: str, participants: list[str], confirmed_only: bool = True) -> Itinerary:
        """Build complete itinerary from extracted items.

        Args:
            title: Title for the itinerary.
            participants: List of participant names.
            confirmed_only: If True, only include confirmed items.
        """
        items = self.extract_all(confirmed_only=confirmed_only)

        # Determine date range from items or use known trip dates
        dates = [item.start_date for item in items if item.start_date]
        start_date = min(dates) if dates else date(2026, 3, 14)
        end_date = max(dates) if dates else date(2026, 3, 28)

        return Itinerary(
            title=title,
            participants=participants,
            destination="Thailand",
            start_date=start_date,
            end_date=end_date,
            items=items,
        )
