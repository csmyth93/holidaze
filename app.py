#!/usr/bin/env python3
"""
Holidaze Web App - Interactive trip map and itinerary viewer.
"""

import json
from pathlib import Path
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thailand 2026 - Route Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
        }

        .app {
            display: flex;
            height: 100vh;
        }

        .sidebar {
            width: 380px;
            background: #16213e;
            overflow-y: auto;
            padding: 1.5rem;
            border-right: 1px solid #0f3460;
        }

        .map-container {
            flex: 1;
            position: relative;
        }

        #map {
            height: 100%;
            width: 100%;
        }

        h1 {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            color: #e94560;
        }

        .subtitle {
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #666;
            margin: 1.5rem 0 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #0f3460;
        }

        .stay-card {
            background: #0f3460;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid #e94560;
        }

        .stay-card:hover, .stay-card.active {
            background: #1a4a7a;
            transform: translateX(4px);
        }

        .stay-card .location {
            font-weight: 600;
            font-size: 1rem;
            color: #fff;
        }

        .stay-card .hotel {
            font-size: 0.85rem;
            color: #aaa;
            margin-top: 0.25rem;
        }

        .stay-card .dates {
            font-size: 0.8rem;
            color: #e94560;
            margin-top: 0.5rem;
        }

        .stay-card .nights {
            display: inline-block;
            background: #e94560;
            color: white;
            padding: 0.15rem 0.5rem;
            border-radius: 999px;
            font-size: 0.7rem;
            margin-left: 0.5rem;
        }

        .transfer-card {
            background: #0a1628;
            border-radius: 6px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .transfer-icon {
            font-size: 1.2rem;
        }

        .transfer-details {
            flex: 1;
        }

        .transfer-route {
            color: #ccc;
        }

        .transfer-type {
            font-size: 0.75rem;
            color: #666;
        }

        .legend {
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: #888;
        }

        .legend-line {
            width: 24px;
            height: 3px;
            border-radius: 2px;
        }

        .legend-line.flight { background: #e94560; }
        .legend-line.ferry { background: #4ecdc4; }
        .legend-line.transfer { background: #ffe66d; }

        /* Leaflet customizations */
        .leaflet-popup-content-wrapper {
            background: #16213e;
            color: #eee;
            border-radius: 8px;
        }

        .leaflet-popup-tip {
            background: #16213e;
        }

        .leaflet-popup-content {
            margin: 12px 16px;
        }

        .popup-title {
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }

        .popup-subtitle {
            font-size: 0.85rem;
            color: #aaa;
        }

        .custom-marker {
            background: #e94560;
            border: 3px solid #fff;
            border-radius: 50%;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        .custom-marker.island {
            background: #4ecdc4;
        }

        .custom-marker.airport {
            background: #ffe66d;
        }

        @media (max-width: 768px) {
            .app {
                flex-direction: column;
            }
            .sidebar {
                width: 100%;
                height: 40vh;
                order: 2;
            }
            .map-container {
                height: 60vh;
                order: 1;
            }
        }
    </style>
</head>
<body>
    <div class="app">
        <aside class="sidebar">
            <h1>Thailand 2026</h1>
            <p class="subtitle">Andaman Coast Island Hopping<br>March 14 - 28</p>

            <h3 class="section-title">Stays</h3>
            <div id="stays-list"></div>

            <h3 class="section-title">Route</h3>
            <div id="transfers-list"></div>

            <div class="legend">
                <div class="legend-item">
                    <div class="legend-line flight"></div>
                    <span>Flight</span>
                </div>
                <div class="legend-item">
                    <div class="legend-line ferry"></div>
                    <span>Ferry/Boat</span>
                </div>
                <div class="legend-item">
                    <div class="legend-line transfer"></div>
                    <span>Van/Transfer</span>
                </div>
            </div>
        </aside>
        <div class="map-container">
            <div id="map"></div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const data = {{ data | tojson }};
        const locations = data.locations;
        const route = data.route;
        const stays = data.stays;

        // Initialize map centered on Thailand islands
        const map = L.map('map', {
            zoomControl: true
        }).setView([7.5, 99.5], 8);

        // Dark map tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(map);

        // Custom marker icon
        function createMarker(type) {
            const colors = {
                city: '#e94560',
                island: '#4ecdc4',
                airport: '#ffe66d'
            };
            return L.divIcon({
                className: 'custom-marker ' + type,
                iconSize: [16, 16],
                iconAnchor: [8, 8],
                popupAnchor: [0, -12]
            });
        }

        // Add markers for each location
        const markers = {};
        Object.entries(locations).forEach(([key, loc]) => {
            const marker = L.marker([loc.lat, loc.lng], {
                icon: createMarker(loc.type)
            }).addTo(map);

            // Find stay info for this location
            const stay = stays.find(s => s.location === key);
            let popupContent = `<div class="popup-title">${loc.name}</div>`;
            if (stay) {
                popupContent += `<div class="popup-subtitle">${stay.hotel}<br>${stay.nights} night${stay.nights > 1 ? 's' : ''}</div>`;
            }
            marker.bindPopup(popupContent);
            markers[key] = marker;
        });

        // Draw route lines
        const lineColors = {
            flight: '#e94560',
            ferry: '#4ecdc4',
            transfer: '#ffe66d'
        };

        route.forEach(segment => {
            const from = locations[segment.from];
            const to = locations[segment.to];
            if (from && to) {
                const color = lineColors[segment.type] || '#888';
                const dashArray = segment.type === 'flight' ? '10, 10' : null;

                L.polyline([[from.lat, from.lng], [to.lat, to.lng]], {
                    color: color,
                    weight: 3,
                    opacity: 0.8,
                    dashArray: dashArray
                }).addTo(map);
            }
        });

        // Render stays list
        const staysList = document.getElementById('stays-list');
        stays.forEach((stay, index) => {
            const loc = locations[stay.location];
            const card = document.createElement('div');
            card.className = 'stay-card';
            card.innerHTML = `
                <div class="location">${loc.name}</div>
                <div class="hotel">${stay.hotel}</div>
                <div class="dates">
                    ${formatDate(stay.start)} - ${formatDate(stay.end)}
                    <span class="nights">${stay.nights} night${stay.nights > 1 ? 's' : ''}</span>
                </div>
            `;
            card.addEventListener('click', () => {
                map.setView([loc.lat, loc.lng], 12);
                markers[stay.location].openPopup();
                document.querySelectorAll('.stay-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
            });
            staysList.appendChild(card);
        });

        // Render transfers list
        const transfersList = document.getElementById('transfers-list');
        route.forEach(segment => {
            const from = locations[segment.from];
            const to = locations[segment.to];
            const icons = {
                flight: '✈️',
                ferry: '⛴️',
                transfer: '🚐'
            };
            const card = document.createElement('div');
            card.className = 'transfer-card';
            card.innerHTML = `
                <span class="transfer-icon">${icons[segment.type] || '🚗'}</span>
                <div class="transfer-details">
                    <div class="transfer-route">${from.name} → ${to.name}</div>
                    <div class="transfer-type">${segment.label} · ${formatDate(segment.date)}</div>
                </div>
            `;
            transfersList.appendChild(card);
        });

        function formatDate(dateStr) {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
        }

        // Fit map to show Thailand region (excluding London)
        const thailandBounds = [
            [6.0, 98.5],  // SW
            [14.5, 101.5] // NE
        ];
        map.fitBounds(thailandBounds);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Load location data
    data_path = Path(__file__).parent / 'data' / 'locations.json'
    with open(data_path) as f:
        data = json.load(f)
    return render_template_string(HTML_TEMPLATE, data=data)

@app.route('/api/locations')
def api_locations():
    data_path = Path(__file__).parent / 'data' / 'locations.json'
    with open(data_path) as f:
        return jsonify(json.load(f))

if __name__ == '__main__':
    print("Starting Holidaze web app...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
