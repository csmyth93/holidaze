#!/usr/bin/env python3
"""
Holidaze - Travel Itinerary Generator

Generate an interactive HTML itinerary from JSON data.
"""

import argparse
import json
from pathlib import Path

from .models import Itinerary, TravelItem, ItemCategory
from .html_generator import HTMLGenerator


def load_itinerary(json_path: Path) -> Itinerary:
    """Load itinerary from JSON file."""
    with open(json_path) as f:
        data = json.load(f)

    items = []
    for item_data in data.get("items", []):
        category = ItemCategory(item_data["category"])
        item = TravelItem(
            id=item_data["id"],
            category=category,
            title=item_data["title"],
            start_date=item_data.get("start_date"),
            end_date=item_data.get("end_date"),
            location=item_data.get("location"),
            details=item_data.get("details", {}),
        )
        items.append(item)

    return Itinerary(
        title=data.get("title", "Trip Itinerary"),
        destination=data.get("destination", ""),
        participants=data.get("participants", []),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        items=items,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate interactive HTML itinerary from JSON data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("data/itinerary.json"),
        help="Path to itinerary JSON file (default: data/itinerary.json)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("output/itinerary.html"),
        help="Output HTML file path (default: output/itinerary.html)",
    )

    args = parser.parse_args()

    # Validate input
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    print(f"Loading itinerary from: {args.input}")

    # Load itinerary
    itinerary = load_itinerary(args.input)

    print(f"Title: {itinerary.title}")
    print(f"Destination: {itinerary.destination}")
    print(f"Dates: {itinerary.start_date} to {itinerary.end_date}")
    print(f"Participants: {', '.join(itinerary.participants)}")
    print(f"\n{len(itinerary.items)} items:")

    for item in itinerary.items:
        icon = {"flight": "✈", "hotel": "🏨", "transfer": "⛴", "activity": "🎯"}.get(item.category.value, "📌")
        print(f"  {icon} {item.start_date}: {item.title}")

    # Generate HTML
    generator = HTMLGenerator(itinerary)
    generator.generate(args.output)

    print(f"\nItinerary saved to: {args.output}")
    return 0


if __name__ == "__main__":
    exit(main())
