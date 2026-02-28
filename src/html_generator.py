from datetime import datetime
from pathlib import Path

from jinja2 import Template

from .models import Itinerary, ItemCategory


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ itinerary.title }}</title>
    <style>
        :root {
            --flight: #3b82f6;
            --hotel: #8b5cf6;
            --transfer: #06b6d4;
            --activity: #ec4899;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
            padding: 2rem;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        h1 {
            font-size: 2rem;
            color: #111827;
            margin-bottom: 0.5rem;
        }

        .dates {
            font-size: 1.1rem;
            color: #6b7280;
        }

        .participants {
            margin-top: 1rem;
            font-size: 0.9rem;
            color: #9ca3af;
        }

        .view-toggle {
            display: flex;
            gap: 0.5rem;
            justify-content: center;
            margin-bottom: 2rem;
        }

        .view-toggle button {
            padding: 0.75rem 1.5rem;
            border: 2px solid #e5e7eb;
            background: white;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.2s;
        }

        .view-toggle button.active {
            border-color: #3b82f6;
            background: #eff6ff;
            color: #1d4ed8;
        }

        .view-toggle button:hover:not(.active) {
            border-color: #9ca3af;
        }

        .day-section {
            margin-bottom: 2rem;
        }

        .day-header {
            position: sticky;
            top: 0;
            background: #f9fafb;
            padding: 0.75rem 0;
            font-size: 1.25rem;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #e5e7eb;
            z-index: 10;
        }

        .item {
            background: white;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin: 0.75rem 0;
            border-left: 4px solid #e5e7eb;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .item.flight { border-left-color: var(--flight); }
        .item.hotel { border-left-color: var(--hotel); }
        .item.transfer { border-left-color: var(--transfer); }
        .item.activity { border-left-color: var(--activity); }

        .item-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }

        .category-icon {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            color: white;
        }

        .category-icon.flight { background: var(--flight); }
        .category-icon.hotel { background: var(--hotel); }
        .category-icon.transfer { background: var(--transfer); }
        .category-icon.activity { background: var(--activity); }

        .item-title {
            font-weight: 600;
            font-size: 1.1rem;
            flex: 1;
        }

        .item-location {
            color: #6b7280;
            font-size: 0.9rem;
        }

        .item-details {
            margin-left: 2.75rem;
            font-size: 0.9rem;
            color: #6b7280;
        }

        .item-details ul {
            list-style: none;
            padding: 0;
        }

        .item-details li {
            padding: 0.2rem 0;
        }

        .item-details li strong {
            color: #374151;
        }

        .highlights {
            margin-top: 0.5rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .highlight-tag {
            background: #f3f4f6;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.8rem;
            color: #4b5563;
        }

        /* Category view */
        .category-section {
            margin-bottom: 2rem;
        }

        .category-header {
            font-size: 1.25rem;
            font-weight: 600;
            color: #374151;
            padding: 0.75rem 0;
            border-bottom: 2px solid #e5e7eb;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        #category-view {
            display: none;
        }

        /* Print styles */
        @media print {
            body {
                background: white;
                padding: 0;
            }

            .view-toggle {
                display: none;
            }

            .item {
                break-inside: avoid;
            }
        }

        @media (max-width: 600px) {
            body {
                padding: 1rem;
            }

            .item-details {
                margin-left: 0;
                margin-top: 0.75rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ itinerary.title }}</h1>
            <p class="dates">{{ itinerary.formatted_dates }}</p>
            <p class="participants">{{ itinerary.participants | join(' • ') }}</p>
        </header>

        <nav class="view-toggle">
            <button data-view="timeline" class="active">Timeline</button>
            <button data-view="category">By Category</button>
        </nav>

        <main id="timeline-view">
            {% for date_str, items in items_by_date.items() %}
            <section class="day-section">
                <h2 class="day-header">{{ format_date(date_str) }}</h2>
                {% for item in items %}
                {{ render_item(item) }}
                {% endfor %}
            </section>
            {% endfor %}
        </main>

        <main id="category-view">
            {% for category, items in items_by_category.items() %}
            <section class="category-section">
                <h2 class="category-header">
                    <span class="category-icon {{ category.value }}">{{ category_icons[category] }}</span>
                    {{ category.value | title }}s
                </h2>
                {% for item in items %}
                {{ render_item(item) }}
                {% endfor %}
            </section>
            {% endfor %}
        </main>
    </div>

    <script>
        document.querySelectorAll('[data-view]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('[data-view]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const view = btn.dataset.view;
                document.getElementById('timeline-view').style.display = view === 'timeline' ? 'block' : 'none';
                document.getElementById('category-view').style.display = view === 'category' ? 'block' : 'none';
            });
        });
    </script>
</body>
</html>
"""

ITEM_TEMPLATE = """
<article class="item {{ item.category.value }}">
    <div class="item-header">
        <span class="category-icon {{ item.category.value }}">{{ icon }}</span>
        <div>
            <span class="item-title">{{ item.title }}</span>
            {% if item.location %}
            <div class="item-location">{{ item.location }}</div>
            {% endif %}
        </div>
    </div>
    <div class="item-details">
        <ul>
            {% if item.formatted_date and item.category.value == 'hotel' %}
            <li><strong>Dates:</strong> {{ item.formatted_date }}</li>
            {% endif %}
            {% for key, value in item.details.items() if key != 'highlights' %}
            <li><strong>{{ key | replace('_', ' ') | title }}:</strong> {{ value }}</li>
            {% endfor %}
        </ul>
        {% if item.details.get('highlights') %}
        <div class="highlights">
            {% for highlight in item.details.get('highlights', []) %}
            <span class="highlight-tag">{{ highlight }}</span>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</article>
"""


CATEGORY_ICONS = {
    ItemCategory.FLIGHT: "✈",
    ItemCategory.HOTEL: "🏨",
    ItemCategory.TRANSFER: "⛴",
    ItemCategory.ACTIVITY: "🎯",
}


def format_date(date_str: str) -> str:
    """Format ISO date string for display."""
    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%A, %B %d")


class HTMLGenerator:
    """Generate interactive HTML itinerary."""

    def __init__(self, itinerary: Itinerary):
        self.itinerary = itinerary

    def generate(self, output_path: Path) -> None:
        """Render itinerary to HTML file."""
        # Create the item renderer
        item_template = Template(ITEM_TEMPLATE)

        def render_item(item):
            return item_template.render(
                item=item,
                icon=CATEGORY_ICONS.get(item.category, "📌"),
            )

        # Render the main template
        template = Template(HTML_TEMPLATE)
        html = template.render(
            itinerary=self.itinerary,
            items_by_date=self.itinerary.items_by_date(),
            items_by_category=self.itinerary.items_by_category(),
            render_item=render_item,
            format_date=format_date,
            category_icons=CATEGORY_ICONS,
        )

        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
