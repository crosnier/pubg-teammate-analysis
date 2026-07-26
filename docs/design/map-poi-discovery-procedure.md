# Map POI Discovery + Validation Procedure

Precise, tested procedure for adding a new map's named-POI reference data to
Drop Zone + Flow (issue #44). Written so this can be handed to a fresh
Claude/LLM session with no prior context and reproduce the same result.
Every step below has actually been run, on Erangel, Taego, Miramar,
Vikendi, Sanhok, and Rondo - this is not a theoretical process.

## Prerequisite: confirm the map's coordinate range

Before touching any image, `utils/map_regions_data.py`'s `MAP_SIZE_CM` dict
must have a real entry for the map's telemetry `mapName` (e.g.
`Baltic_Main`, `Neon_Main`). Never guess this number or copy it from a wiki
without checking.

1. Check if it's already present in `MAP_SIZE_CM`. If so, and it's not
   marked unverified in a comment, skip to the next section.
2. If missing or unverified: search official/community sources for the
   map's size (usually stated as an NxN grid, e.g. "8x8" = 8km x 8km), but
   treat that as a hypothesis, not a fact - unit is often ambiguous
   (community sources rarely specify whether "8x8" means exactly 8000m or
   PUBG's actual slightly-larger playable buffer).
3. **Empirically verify against real cached telemetry** before writing the
   number down. Scan cached telemetry files for the map's real
   `LogParachuteLanding` (or any position) events and find the max
   observed x/y coordinate:
   ```python
   import glob, json
   maxx = maxy = 0
   for f in glob.glob('match-telemetry/*.json'):
       with open(f) as fh:
           data = json.load(fh)
       if not isinstance(data, list):
           continue
       if not any(ev.get('_T') == 'LogMatchStart' and ev.get('mapName') == '<MAP_NAME>' for ev in data):
           continue
       for ev in data:
           if ev.get('_T') == 'LogParachuteLanding':
               loc = ev.get('character', {}).get('location', {})
               maxx = max(maxx, loc.get('x', 0))
               maxy = max(maxy, loc.get('y', 0))
   ```
   **Pitfall already hit**: don't restrict the `LogMatchStart` check (or any
   event-type check) to only the first few events in the file - on some
   maps' telemetry that event isn't near the front, and doing so silently
   undercounts matches to zero. Scan the full event list.
4. If every other confirmed map in `MAP_SIZE_CM` sharing the same "NxN"
   description uses the same value (e.g. all confirmed 8x8 maps use
   `816000` cm), and the observed max real coordinate sits comfortably
   below that value, that's sufficient confirmation - don't require an
   exact match to the max observed value, since real landings cluster
   inward from the true edge by nature (players rarely parachute into the
   map boundary itself).
5. Write the confirmed value into `MAP_SIZE_CM` with a comment stating how
   it was confirmed (source + empirical check), remove any "NOT YET
   VERIFIED" comment for that map.

## Step 1: source the official map image

Official, IP-clean map assets live at `github.com/pubg/api-assets`,
`Assets/Maps/` directory. List the directory first to get the exact
filename - **do not guess the filename from the telemetry `mapName`**.

**Pitfall already hit**: asset filenames use the map's marketing name, not
its telemetry codename. Rondo's telemetry `mapName` is `Neon_Main`, but its
asset file is `Rondo_Main_Low_Res.png` - `Neon_Main_Low_Res.png` 404s.

```bash
curl -s "https://api.github.com/repos/pubg/api-assets/contents/Assets/Maps" \
  | python3 -c "import json,sys; [print(i['name']) for i in json.load(sys.stdin)]"
```

Find the `<MapMarketingName>_Main_Low_Res.png` entry (not `No_Text` - we
want the labels), download it:

```bash
curl -sL "https://raw.githubusercontent.com/pubg/api-assets/master/Assets/Maps/<Name>_Main_Low_Res.png" \
  -o docs/design/maps/<mapname>_official.png
```

Confirm it downloaded as a real image (not a 404 HTML page) and note its
pixel dimensions (`file docs/design/maps/<mapname>_official.png`) - every
map so far has been 819x819px, but verify, don't assume.

## Step 2: read POI pixel positions off the image

This step is **not automatable** - it requires a vision-capable pass over
the actual image. Read the full map image first to get an overview and a
first-pass list of every named POI label visible.

Then, for **every** POI (not just ones that look ambiguous), read pixel
coordinates precisely:

1. Take an initial pixel estimate per POI from the full-image view.
2. Generate a zoomed, grid-overlaid crop centered on that estimate to
   verify/correct it before ever running validation. This catches the most
   common mistake up front instead of after a failed validation pass:

   ```python
   from PIL import Image, ImageDraw
   im = Image.open('docs/design/maps/<mapname>_official.png').convert('RGB')
   x, y = <initial_estimate>
   half = 100
   box = (max(0,x-half), max(0,y-half), min(819,x+half), min(819,y+half))
   crop = im.crop(box)
   scale = 4
   crop = crop.resize((crop.width*scale, crop.height*scale), Image.LANCZOS)
   draw = ImageDraw.Draw(crop)
   step = 20
   ox, oy = box[0], box[1]
   gx = ox - (ox % step)
   while gx < box[2]:
       lx = (gx-ox)*scale
       draw.line([(lx,0),(lx,crop.height)], fill=(255,0,255), width=1)
       draw.text((lx+2,2), str(gx), fill=(255,0,255))
       gx += step
   gy = oy - (oy % step)
   while gy < box[3]:
       ly = (gy-oy)*scale
       draw.line([(0,ly),(crop.width,ly)], fill=(255,0,255), width=1)
       draw.text((2,ly+2), str(gy), fill=(255,0,255))
       gy += step
   crop.save('/tmp/poi_grid_<name>.png')
   ```

   The magenta gridlines are labeled in absolute source-image pixel
   coordinates, so reading the actual building cluster's position directly
   off the grid is precise, not eyeballed against a raw unlabeled crop.

3. **Pitfall already hit, target the building cluster, not the label
   text.** Map labels are usually offset from the actual POI (often above
   or overlapping it). Erangel's Kameshki/Stalber and several of Rondo's
   POIs (Mai Hu, Hernay Town, Jadena City) were initially misread as the
   text position instead of the visible cluster of buildings/roads. Always
   center the final pixel coordinate on the visual settlement cluster
   itself.
4. If a previous crop tool assumption is suspect (e.g. an OS image-crop
   utility's offset convention), verify it against a known-correct
   reference point before trusting a batch of crops from it. This bit
   Erangel's Kameshki/Stalber once already (`sips --cropOffset` turned out
   to be centered on the source image, not top-left-relative) - the PIL
   `Image.crop(box)` approach above uses explicit absolute pixel boxes and
   has no such ambiguity, prefer it over shell image tools.

## Step 3: run the validation tool

```bash
python regenerate_map_data.py --map <MapName_Main> --image-size 819 \
  --pixels '{"POI Name": [px, py], ...}'
```

This scans the entire cached telemetry directory (currently ~1,750 files,
takes a few minutes - run it as a background/long-running command, don't
block waiting synchronously) and prints:
- `<MAP>_POI_PIXELS` - the pixel dict, ready to paste
- `<MAP>_LANDING_VALIDATION_400M` - real landing counts per POI within
  400m, sorted descending, with `NEEDS_REVIEW` flagged on any POI whose
  count is below 50% of that map's median POI count.

If the map has few cached matches (dozens rather than hundreds), thresholds
will be noisier - note that in the write-up, don't treat noise as a
placement error.

## Step 4: interpret results / decide whether to loop back

**What "done, no loop-back needed" looks like:**
- The relative ranking of landing counts matches known/plausible
  popularity - well-known or visually prominent hot-drops (large
  labeled cities, POIs near the center or with obvious loot value) rank
  near the top; small/remote/mountainous named spots rank near the
  bottom. You don't need external confirmation of "popularity" beyond
  what's visually obvious from the map (city size, centrality,
  connectivity) plus the count itself being non-degenerate (not all POIs
  reading near-identical, not one POI absorbing an implausible share).
- No `NEEDS_REVIEW` flags, or every flagged POI has been individually
  re-examined and its low count is explained by real geography (small,
  isolated, mountainous, edge-of-map) rather than a placement error.
- No POI shows a suspiciously low count relative to its own visual
  prominence even if not auto-flagged (e.g. the map's largest labeled
  city landing far below smaller towns) - this caught a real Rondo
  placement error (Jadena City) that the automatic threshold missed,
  because the threshold only compares to the map's median, not to a
  POI's own apparent size/importance.

**When to loop back (repeat steps 2-3 for specific POIs):**
1. Any `NEEDS_REVIEW` flag.
2. Any POI whose count looks wrong relative to its own visual prominence,
   flagged or not (see Jadena City above).
3. A `0` or near-`0` count for any named POI - almost always a placement
   error (landed nowhere near the estimate), not real signal, unless the
   POI is genuinely tiny/impossible to land at cleanly.

**How to loop back:**
1. Generate a fresh grid-overlaid crop (Step 2's method) centered on the
   suspect pixel estimate, sized a bit larger if the first crop didn't
   contain the actual cluster.
2. Identify the real building/settlement cluster's precise grid
   coordinates, not the label.
3. Re-run Step 3 with corrected coordinates for **all** POIs (not just the
   corrected ones) in one pass - it's the same one script call, and
   partial re-runs risk copy-paste inconsistency in the final pasted
   block.
4. Compare the new counts against the previous run for just the corrected
   POIs to confirm the fix actually moved the number in a sane direction
   (a real fix should raise a previously-near-zero count meaningfully,
   not leave it flat).
5. If a corrected POI still reads anomalously low after a careful re-crop,
   stop looping and accept it as real geography (same resolution
   Kameshki/Stalber got on Erangel) - document the reasoning inline in
   `map_regions_data.py`'s docstring rather than iterating indefinitely.

## Step 5: commit the data

1. Paste the reviewed `<MAP>_POI_PIXELS` and `<MAP>_LANDING_VALIDATION_400M`
   dicts into `utils/map_regions_data.py`, following the existing per-map
   section pattern (image path/size constants, POI pixel dict, validation
   dict, a `*_poi_world_coordinates()` helper function).
2. Add a docstring entry at the top of the file documenting: date, source
   of the image, total real landings the validation was cross-checked
   against, any POIs that needed re-review and why they were resolved the
   way they were.
3. Add the new map's entry to `MAP_POI_LOOKUP` in `utils/drop_zone.py`,
   importing the new `*_poi_world_coordinates` function.
4. Run the full test suite - adding a map should never break existing
   tests. No new tests are required for the data itself (the classifier
   logic is already map-agnostic and tested); only add tests if you
   changed shared code, not for the data addition alone.

## What this procedure deliberately does NOT cover

- Auto-detecting POI label positions via OCR/CV - considered and rejected
  early in this project; a real effort of its own, and risky to get
  silently wrong compared to a direct visual read.
- Squad-level consolidation logic (`utils/squad_drop_zone.py`) generalizing
  to a new map - that module is currently Erangel-only by design and needs
  its own follow-up generalization pass, independent of this procedure.
