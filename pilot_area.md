# Field Shift - Pilot Area

This is the area the whole team works on. Download data for this area only.

---

## The area

**Sidi Salem - Qallin area, west of Kafr El-Sheikh city, North Nile Delta, Egypt**

Almost all of it is inside Kafr El-Sheikh governorate. The south edge is close to the border with Gharbia governorate.

| | Value |
|---|---|
| North | 31.30 |
| South | 31.05 |
| West | 30.70 |
| East | 30.91 |
| bbox (W, S, E, N) | `30.70, 31.05, 30.91, 31.30` |
| Center point (lat, lon) | `31.175, 30.805` |
| Size | about 20 km (west to east) x 28 km (south to north) |
| Projection for maps in meters | UTM zone 36N (EPSG:32636) |

---

## ⚠️ How to type the area in each tool

Different tools want the numbers in a different order. Be careful.

| Tool | What to type |
|---|---|
| Python (STAC, rasterio, Earth Engine, most APIs) | bbox = `[30.70, 31.05, 30.91, 31.30]` (W, S, E, N) |
| NASA POWER (one point) | `latitude=31.175`, `longitude=30.805` |
| Google Maps | `31.175, 30.805` (lat first) |

### Quick check - do this every time

> **Latitude must start with 31.** Longitude must start with 30.
>
> If your latitude starts with 30, you swapped them.

Why this matters: if you swap them, the box moves to another part of the Delta (near Tanta, in Gharbia). It is also farmland, so **you will not notice the mistake**.

---

## Time range

| | Download | Use for yearly numbers and trends |
|---|---|---|
| Landsat | 1985 to latest | **1985 to 2025** (full years only) |
| NASA POWER, GPM, SMAP, Sentinel-2 | 2015 to latest | **2016 to 2025** (full years only) |
| SRTM, FAO GAEZ | One-time maps | No time range. Download once. |

Why not 2015 and 2026 for yearly numbers:

- 2015 is not complete. SMAP starts on 31 March 2015. Sentinel-2 starts on 4 July 2015.
- 2026 is not finished yet.

A yearly average with missing months gives a wrong result.
You can still use 2015 and 2026 data for monthly plots.

---

## What each source can see in our area

Each source has a different pixel size. Our area is about 20 x 28 km.

| Source | Pixel size | What it means for us |
|---|---|---|
| NASA POWER | about 50 km (weather), about 100 km (sun) | Bigger than our whole area. Use **one point** (the center). |
| SMAP | the sensor sees about 36 km (the 9 km grid is made by processing) | **One soil moisture trend** for the whole area. Do not trust differences between SMAP pixels inside the area. |
| GPM | about 10 km | About 2 x 3 cells |
| FAO GAEZ | about 1 km | About 25 x 30 cells |
| Landsat | 30 m | Good detail |
| SRTM | 30 m | Good detail |
| Sentinel-2 | 10 m | Field-level detail |

---

## Why North Delta

We compared 8 farming regions in Egypt: North Delta, Middle Delta, West Delta, East Delta, Fayoum, Upper Egypt, Toshka, and the North Coast.

North Delta was the best for 4 reasons:

1. **Strong climate change story.**
   A 2007 IPCC report listed the Nile Delta as one of the 3 places in the world most at risk from climate change, including sea level rise.
   Sea water is pushing salt into the soil from the north.

2. **A real event we can test our work on.**
   In 2018 the government cut rice areas to save water. Kafr El-Sheikh was one of the few governorates allowed to grow rice under these limits (for example, one of 6 governorates in the 2017 decision).
   We can look at the years before and after 2018:
   - Sentinel-2 starts in July 2015 (only one satellite until March 2017, so fewer images at the start)
   - Landsat 8 starts in 2013
   Together they give us several years before 2018.

3. **Published studies in the same governorate.**
   Other researchers used Sentinel-2 and Landsat in Kafr El-Sheikh governorate. One study mapped rice with Sentinel-2 NDVI, which is very close to what we will do. We can compare our results with theirs.

4. **The main signals give useful data here.**
   Rain (GPM), heat and frost (NASA POWER), bare-field months (Sentinel-2), and soil moisture (SMAP, as one trend for the whole area).

### Why not the others

- **East Delta:** very similar to our choice. We picked Kafr El-Sheikh because we found a Sentinel-2 NDVI rice study there.
- **West Delta:** much of it is reclaimed desert land, so the farm area touches the desert and SMAP mixes farm and sand.
- **Middle Delta (Menoufia):** very small fields, many villages, rice is not allowed, no sea water problem.
- **Fayoum:** almost no rain (about 7 to 10 mm per year), so GPM gives nothing.
- **Upper Egypt:** the farm strip is narrow with desert on both sides, so SMAP mixes farm and sand.
- **Toshka / East Owainat:** big company farms, not small farmers.
- **North Coast:** little farming compared to the Delta.

---

## Why these exact edges

| Edge | Reason |
|---|---|
| North = 31.30 | Nashawein (31.35, 30.88) is described as being inside the fish farm area near Lake Burullus. Our map check at 3 points along the north edge found no fish ponds. Fish ponds are water and would break SMAP readings. |
| East = 30.91 | Kafr El-Sheikh city center is at about 30.94, so it is about 3 km outside. |
| West = 30.70 | Desouk city center is at about 30.65, so it is about 5 km outside. |
| North to South | We expect more salt in the north (closer to the sea, and salt patches were reported near Sidi Salem). We will check this with GAEZ data. |

### Towns inside or on the edge

| Town | Location | Where |
|---|---|---|
| Sidi Salem | 31.27, 30.78 | Inside, near the north edge |
| Qallin | 31.05, 30.85 | On the south edge, partly inside |
| El-Mansha'a El-Kubra (Qallin district) | South-east corner | Inside |

All of them are removed with the NDVI rule below.

---

## Map check (done on Google Maps satellite view)

| Point | What we saw | Result |
|---|---|---|
| North-West (31.30, 30.70) | Farm fields + a village | OK |
| North-Middle (31.30, 30.80) | Farm fields only, long narrow plots | OK |
| North-East (31.30, 30.91) | Farm fields | OK |
| South-West (31.05, 30.70) | Farm fields, a village next to it | OK |
| South-East (31.05, 30.91) | Inside a small town (El-Mansha'a El-Kubra) | Accepted |

**No fish ponds at any checked point.** All 3 points on the north edge (west, middle, east) are farmland.

---

## Known problems and how we handle them

| Problem | What we do |
|---|---|
| Land is flat, so SRTM slope is almost zero | Use SRTM for low spots only, and say this in the presentation |
| SMAP is coarse (see the table above) | Use SMAP as one soil moisture trend for the whole area |
| NASA POWER is bigger than our area | Use one point (the center) |
| Villages and towns inside the area | Remove them with the rule below |
| Some fish ponds may be near the north edge | Same rule for Sentinel-2. For SMAP, the anomaly compares the area with itself over time, so a fixed difference cancels out. This only works if the fish ponds did not grow over the years. |
| Old Landsat years (1985-1999) may have few clear images | Count clear images per year during EDA |
| GPM Final Run comes out a few months late | The newest months may be missing. Use full years only (see Time range). |

### The rule to remove non-farm pixels

> If a pixel's NDVI **never goes above 0.3 during the whole year**, it is not farmland. Remove it.

Why it works: an empty farm field turns green for part of the year. Buildings, roads and water never turn green.

**Note:** 0.3 is a starting value. We will check it and adjust it during EDA.

---

## Still to check during EDA

1. Is there really more salt in the north of the area? (GAEZ)
2. Is 0.3 the right NDVI value to remove non-farm pixels?
3. How many clear Landsat images exist per year, especially 1985-1999?
