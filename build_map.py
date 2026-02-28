#!/usr/bin/env python3
"""
Build the interactive map HTML from JSON data files.
This keeps the data separate and maintainable.
"""

import json
from pathlib import Path

def load_json(filename):
    """Load a JSON file from the data directory."""
    data_dir = Path(__file__).parent / 'data'
    with open(data_dir / filename) as f:
        return json.load(f)

def build_map():
    """Build the map HTML from data files."""

    # Load data
    locations = load_json('locations.json')
    hotels = load_json('hotels.json')
    pois = load_json('pois.json')

    # Group POIs by hotel_id
    pois_by_hotel = {}
    for poi in pois['pois']:
        hotel_id = poi['hotel_id']
        if hotel_id not in pois_by_hotel:
            pois_by_hotel[hotel_id] = {'dinner': [], 'lunch': [], 'diving': [], 'attraction': [], 'bar': []}
        pois_by_hotel[hotel_id][poi['category']].append(poi)

    # Build stays data structure
    stays = []
    for hotel in hotels['hotels']:
        hotel_pois = pois_by_hotel.get(hotel['id'], {})
        stay = {
            'location': hotel['location'],
            'hotel': hotel['name'],
            'hotelLat': hotel['lat'],
            'hotelLng': hotel['lng'],
            'start': hotel['start'],
            'end': hotel['end'],
            'nights': hotel['nights'],
            'arrival': hotel['arrival'],
            'arrivalTime': hotel['arrivalTime'],
            'departure': hotel['departure'],
            'departureTime': hotel['departureTime'],
            'weather': hotel['weather'],
            'attractions': [
                {'name': p['name'], 'type': p['type'], 'desc': p['desc'], 'lat': p['lat'], 'lng': p['lng'], 'website': p.get('website')}
                for p in hotel_pois.get('attraction', [])
            ],
            'dinner': [
                {'name': p['name'], 'cuisine': p['type'], 'desc': p['desc'], 'lat': p['lat'], 'lng': p['lng'], 'website': p.get('website')}
                for p in hotel_pois.get('dinner', [])
            ],
            'lunch': [
                {'name': p['name'], 'cuisine': p['type'], 'desc': p['desc'], 'lat': p['lat'], 'lng': p['lng'], 'website': p.get('website')}
                for p in hotel_pois.get('lunch', [])
            ],
            'bars': [
                {'name': p['name'], 'type': p['type'], 'desc': p['desc'], 'lat': p['lat'], 'lng': p['lng'], 'website': p.get('website')}
                for p in hotel_pois.get('bar', [])
            ],
            'diving': [
                {'name': p['name'], 'depth': p['type'], 'desc': p['desc'], 'lat': p['lat'], 'lng': p['lng']}
                for p in hotel_pois.get('diving', [])
            ] if hotel_pois.get('diving') else None,
            'summary': hotel.get('summary', '')
        }
        stays.append(stay)

    # Build complete data object
    data = {
        'locations': locations['locations'],
        'route': locations['route'],
        'stays': stays
    }

    # Generate HTML
    html = generate_html(data)

    # Write output
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / 'map.html'
    output_file.write_text(html, encoding='utf-8')
    print(f"Built map to {output_file}")

def generate_html(data):
    """Generate the complete HTML with embedded data."""

    data_json = json.dumps(data, indent=2)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thailand 2026 - Birkencrocs Crew</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600&display=swap');
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Prompt', -apple-system, BlinkMacSystemFont, sans-serif; background: linear-gradient(135deg, #fff8e7 0%, #ffe4c4 100%); color: #4a3728; }}

        /* Login Page Styles */
        .login-page {{ display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 2rem; }}
        .login-card {{ background: linear-gradient(135deg, #ffffff 0%, #fffbf5 100%); border-radius: 20px; padding: 3rem; max-width: 420px; width: 100%; box-shadow: 0 10px 40px rgba(180,130,70,0.2); border: 1px solid #e8d4b8; text-align: center; }}
        .login-logo {{ font-size: 4rem; margin-bottom: 1rem; }}
        .login-title {{ font-size: 2rem; color: #c9a227; font-weight: 600; margin-bottom: 0.5rem; }}
        .login-subtitle {{ color: #8b7355; font-size: 1rem; margin-bottom: 0.5rem; }}
        .login-dates {{ color: #e07b39; font-size: 0.9rem; font-weight: 500; margin-bottom: 2rem; }}
        .login-form {{ display: flex; flex-direction: column; gap: 1rem; }}
        .login-input {{ padding: 1rem 1.25rem; border: 2px solid #e8d4b8; border-radius: 12px; font-size: 1rem; font-family: inherit; background: #fffaf0; color: #4a3728; transition: all 0.2s; text-align: center; }}
        .login-input:focus {{ outline: none; border-color: #c9a227; background: #fff; }}
        .login-input::placeholder {{ color: #b8a080; }}
        .login-btn {{ padding: 1rem 2rem; background: linear-gradient(135deg, #c9a227 0%, #daa520 100%); color: white; border: none; border-radius: 12px; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.2s; font-family: inherit; }}
        .login-btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(201,162,39,0.4); }}
        .login-btn:active {{ transform: translateY(0); }}
        .login-error {{ color: #e74c3c; font-size: 0.85rem; margin-top: 0.5rem; display: none; }}
        .login-error.show {{ display: block; }}
        .login-crew {{ margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #e8d4b8; }}
        .login-crew-title {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: #b8a080; margin-bottom: 0.75rem; }}
        .login-avatars {{ display: flex; justify-content: center; gap: 0.5rem; flex-wrap: wrap; }}
        .login-avatar {{ width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #26a69a 0%, #00897b 100%); display: flex; align-items: center; justify-content: center; font-size: 0.7rem; color: white; font-weight: 500; text-transform: uppercase; cursor: pointer; transition: all 0.2s; }}
        .login-avatar:hover {{ transform: scale(1.1); }}
        .login-avatar.cal {{ background: linear-gradient(135deg, #e07b39 0%, #d35400 100%); }}
        .login-avatar.lau {{ background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%); }}
        .login-avatar.and {{ background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); }}
        .login-avatar.andr {{ background: linear-gradient(135deg, #27ae60 0%, #1e8449 100%); }}
        .login-avatar.jud {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }}
        .login-avatar.judi {{ background: linear-gradient(135deg, #f39c12 0%, #d68910 100%); }}

        /* User header in app */
        .user-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid #e8d4b8; }}
        .user-greeting {{ font-size: 0.85rem; color: #8b7355; }}
        .user-greeting strong {{ color: #c9a227; }}
        .logout-btn {{ padding: 0.3rem 0.6rem; background: transparent; border: 1px solid #e8d4b8; border-radius: 6px; font-size: 0.7rem; color: #8b7355; cursor: pointer; transition: all 0.2s; font-family: inherit; }}
        .logout-btn:hover {{ background: #fff3e0; border-color: #c9a227; color: #c9a227; }}

        .app {{ display: flex; height: 100vh; display: none; }}
        .sidebar {{ width: 400px; background: linear-gradient(180deg, #fffaf0 0%, #fff5e6 100%); overflow-y: auto; padding: 1.5rem; border-right: 1px solid #e8d4b8; box-shadow: 2px 0 20px rgba(180,130,70,0.1); }}
        .map-container {{ flex: 1; position: relative; }}
        #map {{ height: 100%; width: 100%; }}
        h1 {{ font-size: 1.6rem; margin-bottom: 0.5rem; color: #c9a227; font-weight: 600; text-shadow: 1px 1px 0 rgba(255,255,255,0.5); }}
        .subtitle {{ color: #8b7355; font-size: 0.9rem; margin-bottom: 1.5rem; font-weight: 300; }}
        .section-title {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.15em; color: #c9a227; margin: 1.5rem 0 0.75rem; padding-bottom: 0.5rem; border-bottom: 2px solid #f0d590; font-weight: 500; }}

        .stay-card {{ background: linear-gradient(135deg, #ffffff 0%, #fffbf5 100%); border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem; cursor: pointer; transition: all 0.3s; border-left: 4px solid #c9a227; box-shadow: 0 2px 8px rgba(180,130,70,0.1); }}
        .stay-card:hover, .stay-card.active {{ background: linear-gradient(135deg, #fff9e6 0%, #fff3d4 100%); transform: translateX(4px); box-shadow: 0 4px 16px rgba(180,130,70,0.2); }}
        .stay-card .location {{ font-weight: 600; font-size: 1rem; color: #2d5a4a; }}
        .stay-card .hotel {{ font-size: 0.85rem; color: #8b7355; margin-top: 0.25rem; }}
        .stay-card .dates {{ font-size: 0.8rem; color: #e07b39; margin-top: 0.5rem; font-weight: 500; }}
        .stay-card .nights {{ display: inline-block; background: linear-gradient(135deg, #c9a227 0%, #daa520 100%); color: white; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.7rem; margin-left: 0.5rem; font-weight: 500; }}
        .stay-card .times {{ display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.75rem; }}
        .time-block {{ flex: 1; }}
        .time-label {{ color: #a08060; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .time-value {{ color: #6b5344; }}
        .time-exact {{ color: #0891b2; font-weight: 500; }}
        .time-value.departure {{ color: #e07b39; }}

        .weather {{ display: flex; align-items: center; gap: 0.75rem; margin-top: 0.75rem; padding: 0.6rem 0.75rem; background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); border-radius: 8px; font-size: 0.8rem; border: 1px solid #80deea; }}
        .weather-icon {{ font-size: 1.5rem; }}
        .weather-temps {{ display: flex; flex-direction: column; gap: 0.1rem; }}
        .weather-high {{ color: #e07b39; font-weight: 600; }}
        .weather-low {{ color: #0891b2; font-size: 0.75rem; }}
        .weather-details {{ flex: 1; display: flex; flex-direction: column; gap: 0.1rem; }}
        .weather-rain {{ color: #0891b2; font-size: 0.75rem; }}
        .weather-desc {{ color: #5d8a7a; font-size: 0.7rem; }}

        .expand-btn {{ width: 100%; padding: 0.5rem; margin-top: 0.5rem; background: #faf6f0; border: 1px solid #e8d4b8; border-radius: 6px; color: #6b5344; cursor: pointer; font-size: 0.8rem; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s; }}
        .expand-btn:hover {{ background: #fff3e0; color: #4a3728; border-color: #c9a227; }}
        .expand-btn.active {{ background: #fff3e0; border-color: #c9a227; }}
        .expand-btn .arrow {{ transition: transform 0.2s; }}
        .expand-btn.active .arrow {{ transform: rotate(180deg); }}
        .expand-buttons {{ display: flex; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap; }}
        .expand-buttons .expand-btn {{ flex: 1; min-width: 80px; margin-top: 0; }}
        .expand-btn.dinner {{ border-left: 3px solid #e07b39; }}
        .expand-btn.lunch {{ border-left: 3px solid #2d9a4a; }}
        .expand-btn.bars {{ border-left: 3px solid #9b59b6; }}
        .expand-btn.diving {{ border-left: 3px solid #0891b2; }}

        .panel {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; background: #fffbf5; border-radius: 0 0 8px 8px; margin-top: -4px; border: 1px solid #e8d4b8; border-top: none; }}
        .panel.open {{ max-height: 500px; padding: 0.75rem; }}

        .attraction-item, .food-item, .dive-item {{ display: flex; gap: 0.75rem; padding: 0.6rem 0; border-bottom: 1px solid #f0e6d8; }}
        .attraction-item:last-child, .food-item:last-child, .dive-item:last-child {{ border-bottom: none; }}
        .attraction-icon, .food-icon, .dive-icon {{ width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; background: linear-gradient(135deg, #26a69a 0%, #00897b 100%); }}
        .food-icon.dinner {{ background: linear-gradient(135deg, #e07b39 0%, #d35400 100%); }}
        .food-icon.lunch {{ background: linear-gradient(135deg, #2d9a4a 0%, #1e8449 100%); }}
        .food-icon.bar {{ background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%); }}
        .dive-icon {{ background: linear-gradient(135deg, #0891b2 0%, #0077b6 100%); }}
        .attraction-info, .food-info, .dive-info {{ flex: 1; min-width: 0; }}
        .attraction-name, .food-name, .dive-name {{ font-size: 0.85rem; color: #4a3728; font-weight: 500; }}
        .attraction-name a, .food-name a {{ color: #4a3728; text-decoration: none; border-bottom: 1px dotted #c9a227; transition: all 0.2s; }}
        .attraction-name a:hover, .food-name a:hover {{ color: #c9a227; border-bottom-color: #c9a227; border-bottom-style: solid; }}
        .attraction-desc, .food-desc, .dive-desc {{ font-size: 0.75rem; color: #8b7355; margin-top: 0.15rem; }}
        .food-cuisine {{ font-size: 0.7rem; color: #e07b39; background: rgba(224,123,57,0.1); padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: 500; }}
        .dive-depth {{ font-size: 0.7rem; color: #0891b2; font-weight: 500; }}

        .transfer-card {{ background: linear-gradient(135deg, #ffffff 0%, #fffbf5 100%); border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.85rem; display: flex; align-items: center; gap: 0.75rem; border: 1px solid #e8d4b8; }}
        .transfer-icon {{ font-size: 1.2rem; }}
        .transfer-details {{ flex: 1; }}
        .transfer-route {{ color: #4a3728; font-weight: 500; }}
        .transfer-type {{ font-size: 0.75rem; color: #8b7355; }}

        .legend {{ display: flex; gap: 1rem; margin-top: 1.5rem; flex-wrap: wrap; }}
        .legend-item {{ display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: #6b5344; }}
        .legend-line {{ width: 24px; height: 3px; border-radius: 2px; }}
        .legend-line.flight {{ background: linear-gradient(90deg, #e07b39, #c9a227); }}
        .legend-line.ferry {{ background: linear-gradient(90deg, #0891b2, #26a69a); }}
        .legend-line.transfer {{ background: linear-gradient(90deg, #c9a227, #f0d590); }}

        .leaflet-popup-content-wrapper {{ background: linear-gradient(135deg, #fffaf0 0%, #fff5e6 100%); color: #4a3728; border-radius: 12px; box-shadow: 0 4px 20px rgba(180,130,70,0.25); }}
        .leaflet-popup-tip {{ background: #fff5e6; }}
        .leaflet-popup-content {{ margin: 12px 16px; }}
        .popup-title {{ font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem; color: #2d5a4a; }}
        .popup-subtitle, .popup-type {{ font-size: 0.85rem; color: #8b7355; }}
        .popup-desc {{ font-size: 0.8rem; color: #6b5344; margin-top: 0.25rem; }}
        .popup-link {{ display: inline-block; margin-top: 0.5rem; padding: 0.3rem 0.6rem; background: linear-gradient(135deg, #c9a227 0%, #daa520 100%); color: #fff; font-size: 0.75rem; font-weight: 600; text-decoration: none; border-radius: 6px; transition: all 0.2s; box-shadow: 0 2px 4px rgba(180,130,70,0.3); }}
        .popup-link:hover {{ background: linear-gradient(135deg, #daa520 0%, #c9a227 100%); transform: translateY(-1px); }}

        .custom-marker {{ background: linear-gradient(135deg, #c9a227 0%, #daa520 100%); border: 3px solid #fff; border-radius: 50%; box-shadow: 0 2px 8px rgba(180,130,70,0.4); }}
        .custom-marker.island {{ background: linear-gradient(135deg, #26a69a 0%, #00897b 100%); }}
        .custom-marker.airport {{ background: linear-gradient(135deg, #e07b39 0%, #d35400 100%); }}

        .poi-marker {{ border: 2px solid #fff; border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.2); display: flex; align-items: center; justify-content: center; font-size: 12px; }}
        .poi-marker.attraction {{ background: linear-gradient(135deg, #26a69a 0%, #00897b 100%); }}
        .poi-marker.dinner {{ background: linear-gradient(135deg, #e07b39 0%, #d35400 100%); }}
        .poi-marker.lunch {{ background: linear-gradient(135deg, #2d9a4a 0%, #1e8449 100%); }}
        .poi-marker.bars {{ background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%); }}
        .poi-marker.diving {{ background: linear-gradient(135deg, #0891b2 0%, #0077b6 100%); }}

        .area-summary {{ font-size: 0.8rem; color: #6b5344; margin-top: 0.75rem; padding: 0.75rem; background: linear-gradient(135deg, #f5f0e8 0%, #efe8dd 100%); border-radius: 8px; line-height: 1.5; border-left: 3px solid #c9a227; }}

        /* Drag handle for mobile sidebar resize */
        .drag-handle {{ display: none; }}

        @media (max-width: 768px) {{
            .app {{ flex-direction: column; }}
            .sidebar {{ width: 100%; height: 40vh; order: 2; border-radius: 16px 16px 0 0; border-right: none; border-top: 1px solid #e8d4b8; padding-top: 0.5rem; }}
            .map-container {{ flex: 1; order: 1; height: auto; }}
            .drag-handle {{ display: flex; justify-content: center; align-items: center; padding: 0.5rem 0; cursor: grab; touch-action: none; }}
            .drag-handle:active {{ cursor: grabbing; }}
            .drag-handle-bar {{ width: 40px; height: 5px; background: #d4c4a8; border-radius: 3px; }}
            .sidebar.dragging {{ transition: none; }}
        }}
    </style>
</head>
<body>
    <!-- Login Page -->
    <div class="login-page" id="loginPage">
        <div class="login-card">
            <div class="login-logo">🌴</div>
            <h1 class="login-title">Thailand 2026</h1>
            <p class="login-subtitle">Birkencrocs Crew Adventure</p>
            <p class="login-dates">March 14 - 28 · Andaman Islands</p>
            <form class="login-form" id="loginForm">
                <input type="text" class="login-input" id="usernameInput" placeholder="Enter your name" autocomplete="off" autofocus>
                <button type="submit" class="login-btn">Let's Go! ✈️</button>
                <p class="login-error" id="loginError">Hmm, that name isn't on the crew list!</p>
            </form>
            <div class="login-crew">
                <p class="login-crew-title">The Crew</p>
                <div class="login-avatars">
                    <div class="login-avatar cal" data-name="callum">Cal</div>
                    <div class="login-avatar lau" data-name="laura">Lau</div>
                    <div class="login-avatar and" data-name="andy">Andy</div>
                    <div class="login-avatar jud" data-name="jude">Jude</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Main App -->
    <div class="app" id="mainApp">
        <aside class="sidebar" id="sidebar">
            <div class="drag-handle" id="dragHandle">
                <div class="drag-handle-bar"></div>
            </div>
            <div class="user-header">
                <span class="user-greeting">Welcome, <strong id="userName"></strong>!</span>
                <button class="logout-btn" id="logoutBtn">Sign out</button>
            </div>
            <h1>Thailand 2026</h1>
            <p class="subtitle">Andaman Coast Island Hopping<br>March 14 - 28</p>
            <h3 class="section-title">Stays</h3>
            <div id="stays-list"></div>
            <h3 class="section-title">Route</h3>
            <div id="transfers-list"></div>
            <div class="legend">
                <div class="legend-item"><div class="legend-line flight"></div><span>Flight</span></div>
                <div class="legend-item"><div class="legend-line ferry"></div><span>Ferry/Boat</span></div>
                <div class="legend-item"><div class="legend-line transfer"></div><span>Van/Transfer</span></div>
            </div>
        </aside>
        <div class="map-container">
            <div id="map"></div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const data = {data_json};

        const locations = data.locations;
        const route = data.route;
        const stays = data.stays;

        const map = L.map('map').setView([7.5, 99.5], 8);
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; OpenStreetMap &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }}).addTo(map);

        function createMarker(type) {{
            return L.divIcon({{
                className: 'custom-marker ' + type,
                iconSize: [16, 16],
                iconAnchor: [8, 8],
                popupAnchor: [0, -12]
            }});
        }}

        function createPoiMarker(type, icon) {{
            return L.divIcon({{
                className: 'poi-marker ' + type,
                html: icon,
                iconSize: [24, 24],
                iconAnchor: [12, 12],
                popupAnchor: [0, -14]
            }});
        }}

        const poiLayer = L.layerGroup().addTo(map);

        function clearPoiMarkers() {{
            poiLayer.clearLayers();
        }}

        function showPoiMarkers(stay, category) {{
            clearPoiMarkers();
            let items, markerType, defaultIcon;
            const typeIcons = {{ cultural: '🏛️', activity: '🎯', beach: '🏖️', nature: '🌿', wildlife: '🦭', nightlife: '🌙' }};

            if (category === 'attractions') {{
                items = stay.attractions;
                markerType = 'attraction';
            }} else if (category === 'dinner') {{
                items = stay.dinner;
                markerType = 'dinner';
                defaultIcon = '🍽️';
            }} else if (category === 'lunch') {{
                items = stay.lunch;
                markerType = 'lunch';
                defaultIcon = '🥗';
            }} else if (category === 'bars') {{
                items = stay.bars || [];
                markerType = 'bars';
                defaultIcon = '🍸';
            }} else if (category === 'diving') {{
                items = stay.diving || [];
                markerType = 'diving';
                defaultIcon = '🤿';
            }}

            if (!items || items.length === 0) return;

            const bounds = [];
            items.forEach((item) => {{
                if (!item.lat || !item.lng) return;
                const icon = category === 'attractions' ? (typeIcons[item.type] || '📍') : defaultIcon;
                const marker = L.marker([item.lat, item.lng], {{ icon: createPoiMarker(markerType, icon) }});

                let popupContent = `<div class="poi-popup"><div class="popup-title">${{item.name}}</div>`;
                if (category === 'attractions') {{
                    popupContent += `<div class="popup-type">${{item.type}}</div>`;
                }} else if (category === 'diving') {{
                    popupContent += `<div class="popup-type">${{item.depth}}</div>`;
                }} else if (category === 'bars') {{
                    popupContent += `<div class="popup-type">${{item.type}}</div>`;
                }} else {{
                    popupContent += `<div class="popup-type">${{item.cuisine}}</div>`;
                }}
                popupContent += `<div class="popup-desc">${{item.desc}}</div>`;
                if (item.website) {{
                    popupContent += `<a href="${{item.website}}" target="_blank" rel="noopener" class="popup-link">Visit website ↗</a>`;
                }}
                popupContent += `</div>`;

                marker.bindPopup(popupContent);
                marker.addTo(poiLayer);
                bounds.push([item.lat, item.lng]);
            }});

            if (bounds.length > 0) {{
                map.fitBounds(bounds, {{ padding: [50, 50], maxZoom: 14 }});
            }}
        }}

        // Add location markers
        const markers = {{}};
        Object.entries(locations).forEach(([key, loc]) => {{
            const marker = L.marker([loc.lat, loc.lng], {{ icon: createMarker(loc.type) }}).addTo(map);
            const stay = stays.find(s => s.location === key);
            let popupContent = `<div class="popup-title">${{loc.name}}</div>`;
            if (stay) {{
                popupContent += `<div class="popup-subtitle">${{stay.hotel}}<br>${{stay.nights}} night${{stay.nights > 1 ? 's' : ''}}</div>`;
            }}
            marker.bindPopup(popupContent);
            markers[key] = marker;
        }});

        // Draw route lines
        const lineColors = {{ flight: '#e07b39', ferry: '#0891b2', transfer: '#c9a227' }};
        route.forEach(segment => {{
            const from = locations[segment.from];
            const to = locations[segment.to];
            if (from && to) {{
                L.polyline([[from.lat, from.lng], [to.lat, to.lng]], {{
                    color: lineColors[segment.type] || '#888',
                    weight: 3,
                    opacity: 0.8,
                    dashArray: segment.type === 'flight' ? '10, 10' : null
                }}).addTo(map);
            }}
        }});

        // Render stays
        const staysList = document.getElementById('stays-list');
        stays.forEach((stay) => {{
            const loc = locations[stay.location];
            const card = document.createElement('div');
            card.className = 'stay-card';

            const typeIcons = {{ cultural: '🏛️', activity: '🎯', beach: '🏖️', nature: '🌿', wildlife: '🦭', nightlife: '🌙' }};
            const weatherIcons = {{ sunny: '☀️', partly_cloudy: '⛅', cloudy: '☁️', rain: '🌧️', storm: '⛈️' }};

            const attractionsHtml = stay.attractions.map(a => `
                <div class="attraction-item">
                    <div class="attraction-icon">${{typeIcons[a.type] || '📍'}}</div>
                    <div class="attraction-info">
                        <div class="attraction-name">${{a.website ? `<a href="${{a.website}}" target="_blank" rel="noopener" title="View on map">${{a.name}} ↗</a>` : a.name}}</div>
                        <div class="attraction-desc">${{a.desc}}</div>
                    </div>
                </div>
            `).join('');

            const dinnerHtml = stay.dinner.map(d => `
                <div class="food-item">
                    <div class="food-icon dinner">🍽️</div>
                    <div class="food-info">
                        <div class="food-name">${{d.website ? `<a href="${{d.website}}" target="_blank" rel="noopener" title="Visit website">${{d.name}} ↗</a>` : d.name}}</div>
                        <div><span class="food-cuisine">${{d.cuisine}}</span></div>
                        <div class="food-desc">${{d.desc}}</div>
                    </div>
                </div>
            `).join('');

            const lunchHtml = stay.lunch.map(l => `
                <div class="food-item">
                    <div class="food-icon lunch">🥗</div>
                    <div class="food-info">
                        <div class="food-name">${{l.website ? `<a href="${{l.website}}" target="_blank" rel="noopener" title="Visit website">${{l.name}} ↗</a>` : l.name}}</div>
                        <div><span class="food-cuisine">${{l.cuisine}}</span></div>
                        <div class="food-desc">${{l.desc}}</div>
                    </div>
                </div>
            `).join('');

            const barsHtml = stay.bars ? stay.bars.map(b => `
                <div class="food-item">
                    <div class="food-icon bar">🍸</div>
                    <div class="food-info">
                        <div class="food-name">${{b.website ? `<a href="${{b.website}}" target="_blank" rel="noopener" title="Visit website">${{b.name}} ↗</a>` : b.name}}</div>
                        <div><span class="food-cuisine" style="color:#9b59b6;background:rgba(155,89,182,0.1)">${{b.type}}</span></div>
                        <div class="food-desc">${{b.desc}}</div>
                    </div>
                </div>
            `).join('') : '';

            const divingHtml = stay.diving ? stay.diving.map(d => `
                <div class="dive-item">
                    <div class="dive-icon">🤿</div>
                    <div class="dive-info">
                        <div class="dive-name">${{d.name}}</div>
                        <div><span class="dive-depth">${{d.depth}}</span></div>
                        <div class="dive-desc">${{d.desc}}</div>
                    </div>
                </div>
            `).join('') : '';

            const weatherHtml = stay.weather ? `
                <div class="weather">
                    <div class="weather-icon">${{weatherIcons[stay.weather.condition] || '☀️'}}</div>
                    <div class="weather-temps">
                        <span class="weather-high">${{stay.weather.high}}°C</span>
                        <span class="weather-low">${{stay.weather.low}}°C</span>
                    </div>
                    <div class="weather-details">
                        <span class="weather-rain">💧 ${{stay.weather.rain}}% rain</span>
                        <span class="weather-desc">${{stay.weather.desc}}</span>
                    </div>
                </div>
            ` : '';

            const formatDate = (dateStr) => {{
                const date = new Date(dateStr);
                return date.toLocaleDateString('en-GB', {{ day: 'numeric', month: 'short' }});
            }};

            card.innerHTML = `
                <div class="location">${{loc.name}}</div>
                <div class="hotel">${{stay.hotel}}</div>
                <div class="dates">
                    ${{formatDate(stay.start)}} - ${{formatDate(stay.end)}}
                    <span class="nights">${{stay.nights}} night${{stay.nights > 1 ? 's' : ''}}</span>
                </div>
                <div class="times">
                    <div class="time-block">
                        <span class="time-label">Arrive</span>
                        <span class="time-value">${{stay.arrival}} <span class="time-exact">${{stay.arrivalTime}}</span></span>
                    </div>
                    <div class="time-block">
                        <span class="time-label">Leave</span>
                        <span class="time-value departure">${{stay.departure}} <span class="time-exact">${{stay.departureTime}}</span></span>
                    </div>
                </div>
                ${{weatherHtml}}
                ${{stay.summary ? `<div class="area-summary">${{stay.summary}}</div>` : ''}}
                <button class="expand-btn" data-panel="attractions">
                    <span>🎯 Things to do</span>
                    <span class="arrow">▼</span>
                </button>
                <div class="panel attractions-panel" data-panel="attractions">
                    ${{attractionsHtml}}
                </div>
                <div class="expand-buttons">
                    <button class="expand-btn dinner" data-panel="dinner">
                        <span>🍽️ Dinner</span>
                        <span class="arrow">▼</span>
                    </button>
                    <button class="expand-btn lunch" data-panel="lunch">
                        <span>🥗 Casual</span>
                        <span class="arrow">▼</span>
                    </button>
                    ${{stay.bars && stay.bars.length ? `<button class="expand-btn bars" data-panel="bars">
                        <span>🍸 Bars</span>
                        <span class="arrow">▼</span>
                    </button>` : ''}}
                    ${{stay.diving ? `<button class="expand-btn diving" data-panel="diving">
                        <span>🤿 Diving</span>
                        <span class="arrow">▼</span>
                    </button>` : ''}}
                </div>
                <div class="panel dinner-panel" data-panel="dinner">
                    ${{dinnerHtml}}
                </div>
                <div class="panel lunch-panel" data-panel="lunch">
                    ${{lunchHtml}}
                </div>
                ${{stay.bars && stay.bars.length ? `<div class="panel bars-panel" data-panel="bars">
                    ${{barsHtml}}
                </div>` : ''}}
                ${{stay.diving ? `<div class="panel diving-panel" data-panel="diving">
                    ${{divingHtml}}
                </div>` : ''}}
            `;

            card.addEventListener('click', (e) => {{
                if (!e.target.closest('.expand-btn') && !e.target.closest('.panel')) {{
                    map.setView([stay.hotelLat || loc.lat, stay.hotelLng || loc.lng], 13);
                    markers[stay.location]?.openPopup();
                    document.querySelectorAll('.stay-card').forEach(c => c.classList.remove('active'));
                    card.classList.add('active');
                }}
            }});

            card.querySelectorAll('.expand-btn').forEach(btn => {{
                btn.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    const panelType = btn.dataset.panel;
                    const panel = card.querySelector(`.panel[data-panel="${{panelType}}"]`);
                    const isOpen = panel.classList.contains('open');

                    card.querySelectorAll('.panel').forEach(p => p.classList.remove('open'));
                    card.querySelectorAll('.expand-btn').forEach(b => b.classList.remove('active'));
                    clearPoiMarkers();

                    if (!isOpen) {{
                        panel.classList.add('open');
                        btn.classList.add('active');
                        showPoiMarkers(stay, panelType);
                    }}
                }});
            }});

            staysList.appendChild(card);
        }});

        // Render transfers
        const transfersList = document.getElementById('transfers-list');
        const icons = {{ flight: '✈️', ferry: '⛴️', transfer: '🚐' }};
        route.forEach(segment => {{
            const from = locations[segment.from];
            const to = locations[segment.to];
            const card = document.createElement('div');
            card.className = 'transfer-card';
            const formatDate = (dateStr) => {{
                const date = new Date(dateStr);
                return date.toLocaleDateString('en-GB', {{ day: 'numeric', month: 'short' }});
            }};
            card.innerHTML = `
                <span class="transfer-icon">${{icons[segment.type] || '🚗'}}</span>
                <div class="transfer-details">
                    <div class="transfer-route">${{from.name}} → ${{to.name}}</div>
                    <div class="transfer-type">${{segment.label}} · ${{formatDate(segment.date)}}</div>
                </div>
            `;
            transfersList.appendChild(card);
        }});

        // Fit map to Thailand
        map.fitBounds([[6.0, 98.5], [14.5, 101.5]]);

        // ========== LOGIN SYSTEM ==========
        const allowedUsers = ['callum', 'laura', 'andy', 'andrew', 'jude', 'judith'];
        const loginPage = document.getElementById('loginPage');
        const mainApp = document.getElementById('mainApp');
        const loginForm = document.getElementById('loginForm');
        const usernameInput = document.getElementById('usernameInput');
        const loginError = document.getElementById('loginError');
        const userNameDisplay = document.getElementById('userName');
        const logoutBtn = document.getElementById('logoutBtn');

        function showApp(username) {{
            const displayName = username.charAt(0).toUpperCase() + username.slice(1);
            userNameDisplay.textContent = displayName;
            loginPage.style.display = 'none';
            mainApp.style.display = 'flex';
            // Trigger map resize and fit to all stay locations
            setTimeout(() => {{
                map.invalidateSize();
                // Collect all hotel coordinates to fit bounds
                const bounds = stays.map(stay => [stay.hotelLat, stay.hotelLng]);
                if (bounds.length > 0) {{
                    map.fitBounds(bounds, {{ padding: [40, 40] }});
                }}
            }}, 100);
        }}

        function showLogin() {{
            loginPage.style.display = 'flex';
            mainApp.style.display = 'none';
            usernameInput.value = '';
            loginError.classList.remove('show');
        }}

        function login(username) {{
            const normalized = username.toLowerCase().trim();
            if (allowedUsers.includes(normalized)) {{
                showApp(normalized);
                return true;
            }}
            return false;
        }}

        function logout() {{
            showLogin();
        }}

        // Always start at login
        showLogin();

        // Login form submit
        loginForm.addEventListener('submit', (e) => {{
            e.preventDefault();
            if (!login(usernameInput.value)) {{
                loginError.classList.add('show');
                usernameInput.focus();
            }}
        }});

        // Avatar click to login
        document.querySelectorAll('.login-avatar').forEach(avatar => {{
            avatar.addEventListener('click', () => {{
                login(avatar.dataset.name);
            }});
        }});

        // Logout button
        logoutBtn.addEventListener('click', logout);

        // Clear error on input
        usernameInput.addEventListener('input', () => {{
            loginError.classList.remove('show');
        }});

        // ========== MOBILE SIDEBAR DRAG RESIZE ==========
        const sidebar = document.getElementById('sidebar');
        const dragHandle = document.getElementById('dragHandle');
        let isDragging = false;
        let startY = 0;
        let startHeight = 0;

        function startDrag(e) {{
            if (window.innerWidth > 768) return;
            isDragging = true;
            startY = e.type === 'mousedown' ? e.clientY : e.touches[0].clientY;
            startHeight = sidebar.offsetHeight;
            sidebar.classList.add('dragging');
            e.preventDefault();
        }}

        function doDrag(e) {{
            if (!isDragging) return;
            const currentY = e.type === 'mousemove' ? e.clientY : e.touches[0].clientY;
            const deltaY = startY - currentY;
            const newHeight = Math.min(Math.max(startHeight + deltaY, window.innerHeight * 0.15), window.innerHeight * 0.85);
            sidebar.style.height = newHeight + 'px';
            map.invalidateSize();
        }}

        function endDrag() {{
            if (!isDragging) return;
            isDragging = false;
            sidebar.classList.remove('dragging');
        }}

        dragHandle.addEventListener('mousedown', startDrag);
        dragHandle.addEventListener('touchstart', startDrag, {{ passive: false }});
        document.addEventListener('mousemove', doDrag);
        document.addEventListener('touchmove', doDrag, {{ passive: false }});
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);
    </script>
</body>
</html>'''

if __name__ == '__main__':
    build_map()
