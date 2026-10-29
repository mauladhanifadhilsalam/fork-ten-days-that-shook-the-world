#!/usr/bin/env bash
# Rebuild index.html from the data.
#   tools/build.sh            full pipeline: OSM tiles into ./cache on the first run, then the map,
#                             the story and the page
#   tools/build.sh --bundle   only re-pack src/app.html with the committed build/*.json
# The map step needs Shapely (pip install shapely); everything else is the standard library.
set -euo pipefail
cd "$(dirname "$0")/.."
CACHE=cache

if [[ "${1:-}" != "--bundle" ]]; then
  python3 -I tools/text.py "$CACHE"
  python3 -I tools/check_story.py                      # the data must be clean before it is drawn
  python3 -I tools/fetch_osm.py "$CACHE"
  python3 -I tools/build_map.py "$CACHE" data build/map.json        # also writes $CACHE/build/graph.pkl
  python3 -I tools/build_story.py data build/map.json "$CACHE/build/graph.pkl" build/story.json
fi
python3 -I tools/bundle.py build/map.json build/story.json src/app.html "$CACHE/out"
cp "$CACHE/out/index.html" index.html
echo "index.html rebuilt ($(du -h index.html | cut -f1))"
