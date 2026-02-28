#!/bin/bash
# Deploy script for Holidaze

set -e

echo "Building map..."
python build_map.py

echo "Copying to root for GitHub Pages..."
cp output/map.html index.html

echo "Committing changes..."
git add -A
git commit -m "Update trip itinerary"

echo "Pushing to GitHub..."
git push

echo "Done! Site will update in a minute or two."
