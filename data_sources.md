# Field Shift - Data Sources We Will Use

Every source here comes from the official NASA Space Apps Resources list for this challenge.
We did not add any outside source.

We need to know 7 things. Each one has a source.

| # | What we want to know | Source | What it gives us |
|---|---|---|---|
| 1 | Is it hot or cold? | **NASA POWER** | Daily temperature, sun, humidity, wind |
| 2 | How much rain fell? | **GPM (IMERG)** | Rain amount, every day |
| 3 | Is the soil wet or dry? | **SMAP** | Soil moisture |
| 4 | Is the field green or empty **now**? | **Sentinel-2** | NDVI at 10 m detail, every 5 days |
| 5 | How did the area change over **40 years**? | **Landsat** | NDVI from 1984 until today |
| 6 | Is the land flat or sloped? | **SRTM** | Elevation, slope, low spots |
| 7 | Soil type, salt, and crop water need | **FAO GAEZ** | Soil constraints, water indicators, crop suitability |

---

## Why two satellites for the plants? (4 and 5)

They do two different jobs.

- **Sentinel-2** has a clear picture (10 m), but only from 2015.
  An Egyptian field is about 65 m x 65 m, so we need this detail to see one farm.
- **Landsat** is less clear (30 m), but goes back to 1984.
  We need this long history to prove the area is really changing.

Short version:
- Sentinel-2 = the farm **today**
- Landsat = the area over **40 years**

---

## Why GAEZ covers three things (7)

The challenge Resources page says GAEZ gives soil constraints, water availability indicators,
and crop suitability.

So one source gives us soil type, salt problems, and how much water each crop needs.
We do not need three separate sources for this.

---

## Not used

- **USA-only sources** (USDA, PRISM, CropScape, SSURGO, NAIP, NLCD, OpenET, CoCoRaHS, NWIS, LANDFIRE, Market News, QuickStats).
  They do not cover Egypt.
- **MODIS** - Landsat is better for us: longer history (1984 vs 2000) and clearer (30 m vs 250 m).
- **GEDI** - it measures tree height. Our crops are field crops, so it does not help.

---

## Extra sources - only if we have time at the end

ECOSTRESS, GRACE / GRACE-FO, ERA5, GLDAS.
All of them are also in the official Resources list.

---

## Accounts to create first

1. **NASA Earthdata Login** - for GPM, SMAP, Landsat, SRTM
2. **Copernicus Data Space** - for Sentinel-2
3. **FAO GAEZ** - open, no account needed
