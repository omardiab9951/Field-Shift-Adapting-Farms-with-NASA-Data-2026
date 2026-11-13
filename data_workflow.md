# Field Shift - Data Workflow (Team Guide)

**Read this before you download anything or write any code.**

This file tells every person **what to do, step by step**, so we can put all the data together at the end without problems.

It covers Steps 2, 3 and 4 of `project_plan.md`: look at the data (EDA), download it, and put it together (harmonization).
The area and dates come from `pilot_area.md`.

All the code in this file was **tested** before it was written here.

---

## Contents

0. The golden rules
1. Who does what, and in what order
2. Setup (do this once)
3. The grid and the helper code
4. Time rules
5. Output files (the contract)
6. Step by step for each dataset
7. What to put in your notebook (EDA)
8. Merge
9. Checklist before every push
10. Common mistakes
11. If you get stuck

---

## 0. The golden rules

1. **Only our area.** Never download the whole world, the whole country, or full satellite scenes.
2. **Latitude starts with 31.** Longitude starts with 30. If not, you swapped them.
3. **Raw data stays on your laptop** in `data/raw/`. Never push raw data.
4. **Only small CSV results go to GitHub**, in `data/processed/`.
5. **Everyone uses the same grid** (`grid_1km.csv`) and the **same column names** from this file.
6. **Final tables: 2016-01 to 2024-12** (108 months). Landsat: 1985 to 2024.
7. **Missing value = empty.** Never write 0, -999 or -9999 for missing.
8. **Open only your own notebook.**

---

## 1. Who does what, and in what order

| Person | Data | Notebook | Output file(s) |
|---|---|---|---|
| Mostafa Sherief | The grid | `00_grid.ipynb` | `grid_1km.csv` |
| Fatma | NASA POWER | `01_nasa_power.ipynb` | `power_daily.csv`, `power_monthly.csv` |
| Omar | GPM | `02_gpm.ipynb` | `gpm_monthly.csv` |
| Mostafa Abdelhameed | SMAP | `03_smap.ipynb` | `smap_monthly.csv` |
| Mostafa Sherief | Sentinel-2 + Landsat | `04_sentinel_landsat.ipynb` | `sentinel2_monthly.csv`, `landsat_yearly.csv` |
| Omar | SRTM | `05_srtm.ipynb` | `srtm_static.csv` |
| Fatma | FAO GAEZ | `06_gaez.ipynb` | `gaez_static.csv` |
| Mostafa Sherief | Merge (at the end) | `07_merge.ipynb` | `master_monthly.csv` |

### Order

```
1. Mostafa Sherief: setup + grid_1km.csv  (first, before everyone)
2. Everyone: setup on your laptop (section 2)
3. Everyone: your notebook (section 6 + section 7)
4. Everyone: push your CSV (section 9 checklist)
5. Mostafa Sherief: merge (section 8)
```

NASA POWER, GPM and SMAP **do not need the grid**. Fatma, Omar and Mostafa Abdelhameed can start these right away.
SRTM and GAEZ need `grid_1km.csv`. Wait for it before making the output.

---

## 2. Setup (do this once)

### 2.1 Accounts

| Person | Account | Link |
|---|---|---|
| Fatma | None needed | |
| Omar | NASA Earthdata | https://urs.earthdata.nasa.gov/users/new |
| Mostafa Abdelhameed | NASA Earthdata | https://urs.earthdata.nasa.gov/users/new |
| Mostafa Sherief | None needed for the cloud catalog | |

### 2.2 Get the repo

```
git clone https://github.com/omardiab9951/Field-Shift-Adapting-Farms-with-NASA-Data-2026.git
cd Field-Shift-Adapting-Farms-with-NASA-Data-2026
git checkout eda
git pull
```

### 2.3 Make the data folders

```
mkdir data\raw
mkdir data\processed
```

```
notebooks/          <- your notebook goes here
data/
  raw/              <- your downloads. NOT on GitHub.
  processed/        <- small CSV results. ON GitHub.
```

### 2.4 Install Python packages

Everyone:

```
pip install numpy pandas matplotlib requests pyproj xarray rioxarray rasterio
```

Mostafa Sherief also:

```
pip install pystac-client planetary-computer odc-stac
```

### 2.5 First cell of EVERY notebook

Copy this as the first cell. It checks lat and lon for you.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Our area (from pilot_area.md) - do not change
W, S, E, N = 30.70, 31.05, 30.91, 31.30      # West, South, East, North
LAT_C, LON_C = 31.175, 30.805                # center point
START_YEAR, END_YEAR = 2016, 2024            # full years for the final tables

# Safety check: latitude starts with 31, longitude starts with 30
assert 31 <= S < N < 32, "Latitude is wrong. Did you swap lat and lon?"
assert 30 <= W < E < 31, "Longitude is wrong. Did you swap lat and lon?"
print("Area OK")
```

---

## 3. The grid and the helper code

### 3.1 The idea

We draw a "squared paper" over our area. Each square (cell) is **1 km x 1 km**.
Every dataset must give **one value per cell**.

| | Value |
|---|---|
| Cell size | 1 km x 1 km |
| Projection | UTM zone 36N (EPSG:32636) |
| Number of cells | **560** (tested) |
| File | `data/processed/grid_1km.csv` |
| Main columns | `cell_id` (1 to 560), `lat`, `lon` (center of the cell) |

**Nobody makes their own grid.** Everyone uses this file.

### 3.2 How to put your data on the grid

| Your data is... | Example | What to do |
|---|---|---|
| **Bigger than the whole area** | NASA POWER, GPM, SMAP | No grid. One value per month for the whole area. |
| **About 1 km** | GAEZ | Each cell takes the pixel at the **cell center** (code 3.4) |
| **Smaller than 1 km** | Sentinel-2, Landsat, SRTM | Put each small pixel in its cell, then summarize (code 3.3) |

### 3.3 Helper code A: put small pixels in cells

Use this for SRTM, Sentinel-2 and Landsat. Copy it into your notebook.

```python
from pyproj import Transformer

GRID = pd.read_csv("../data/processed/grid_1km.csv")
_TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True)

def lonlat_to_cell(lon, lat):
    """Give lon and lat of pixel centers. Returns the cell_id of each pixel (NaN if outside our area)."""
    x, y = _TO_UTM.transform(np.asarray(lon), np.asarray(lat))
    key = pd.DataFrame({"x_min_m": np.floor(x / 1000) * 1000,
                        "y_max_m": np.floor(y / 1000) * 1000 + 1000})
    out = key.merge(GRID[["x_min_m", "y_max_m", "cell_id"]], on=["x_min_m", "y_max_m"], how="left")
    return out["cell_id"].to_numpy()
```

**Note:** `lon` goes first, then `lat`.

### 3.4 Helper code B: take the pixel at the cell center

Use this for GAEZ.

```python
import xarray as xr

def value_at_cell_centers(da):
    """da = a raster with x = longitude and y = latitude. Returns one value per cell (560 values)."""
    return da.sel(x=xr.DataArray(GRID["lon"].values, dims="cell"),
                  y=xr.DataArray(GRID["lat"].values, dims="cell"),
                  method="nearest").values
```

---

## 4. Time rules

Everything becomes **monthly**: `year` (2016 to 2024) and `month` (1 to 12), whole numbers.

| Kind of value | How to make it monthly |
|---|---|
| Rain | **Sum** of the month |
| Temperature, humidity, wind, sun, soil moisture | **Mean** of the month |
| NDVI | **Max** of the clear images in the month |
| Elevation, soil, GAEZ | No time. One value always. |
| Landsat | **Yearly** (for the 40-year trend) |

Why 2016 to 2024:

- 2015 is not complete. SMAP starts on 31 March 2015. Sentinel-2 starts in July 2015.
- 2025 is not complete for GPM. The GPM Final Run (version 07) **ends on 30 September 2025**.

A yearly number with missing months is wrong. So every dataset uses the same 9 full years.

---

## 5. Output files (the contract)

| Kind | Key columns | Rows | Files |
|---|---|---|---|
| Whole area, monthly | `year, month` | **108** | `power_monthly`, `gpm_monthly`, `smap_monthly` |
| Per cell, monthly | `cell_id, year, month` | **60,480** (560 x 108) | `sentinel2_monthly` |
| Per cell, no time | `cell_id` | **560** | `srtm_static`, `gaez_static` |
| Per cell, yearly | `cell_id, year` | **22,400** (560 x 40) | `landsat_yearly` |
| Extra (daily, for Step 5) | `date` | **3,653** (2015 to 2024) | `power_daily` |

### Format rules

- CSV, comma separated
- Column names: small letters, words joined with `_`
- Put the unit in the column name (`rain_mm`, `t_max_c`, `elev_mean_m`)
- Missing value = empty
- Save with `index=False`
- If your file is bigger than 10 MB, something is wrong. Ask before you push.

---

## 6. Step by step for each dataset

### 6.1 The grid - Mostafa Sherief

**Do this first.** Notebook: `00_grid.ipynb`. After the first cell (2.5), run:

```python
from pyproj import Transformer

CELL = 1000  # 1 km in meters
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True)
to_ll  = Transformer.from_crs("EPSG:32636", "EPSG:4326", always_xy=True)

# 1. Corners of the area in meters
xs, ys = to_utm.transform([W, E, E, W], [S, S, N, N])
x0 = np.floor(min(xs) / CELL) * CELL
x1 = np.ceil(max(xs) / CELL) * CELL
y0 = np.floor(min(ys) / CELL) * CELL
y1 = np.ceil(max(ys) / CELL) * CELL
ncols = int((x1 - x0) / CELL)
nrows = int((y1 - y0) / CELL)

# 2. All cells (row 0 = north)
rows, cols = np.meshgrid(np.arange(nrows), np.arange(ncols), indexing="ij")
rows, cols = rows.ravel(), cols.ravel()
x_min = x0 + cols * CELL
y_max = y1 - rows * CELL
x_c, y_c = x_min + CELL / 2, y_max - CELL / 2
lon, lat = to_ll.transform(x_c, y_c)

grid = pd.DataFrame({
    "row": rows, "col": cols,
    "x_min_m": x_min, "x_max_m": x_min + CELL,
    "y_min_m": y_max - CELL, "y_max_m": y_max,
    "x_m": x_c, "y_m": y_c,
    "lat": np.round(lat, 6), "lon": np.round(lon, 6),
})

# 3. Keep only cells whose center is inside our area
inside = grid.lon.between(W, E) & grid.lat.between(S, N)
grid = grid[inside].reset_index(drop=True)
grid.insert(0, "cell_id", np.arange(1, len(grid) + 1))

# 4. Check and save
print("Cells:", len(grid))             # must be 560
assert len(grid) == 560
grid.to_csv("../data/processed/grid_1km.csv", index=False)
```

Then push `grid_1km.csv` and tell the team.

---

### 6.2 NASA POWER - Fatma

**What:** daily weather at **one point** (the center). No account needed.

**Step 1: download** (in your notebook, after the first cell):

```python
import requests

PARAMS = "T2M,T2M_MAX,T2M_MIN,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR"
URL = ("https://power.larc.nasa.gov/api/temporal/daily/point"
       f"?parameters={PARAMS}&community=AG"
       f"&latitude={LAT_C}&longitude={LON_C}"
       "&start=20150101&end=20241231&format=JSON")

data = requests.get(URL, timeout=300).json()

# Save the raw answer (stays on your laptop)
import json
with open("../data/raw/power_raw.json", "w") as f:
    json.dump(data, f)
```

**Step 2: check the units.** Print them and compare with the table below:

```python
print(data["parameters"])
```

| POWER name | Our column | Expected unit |
|---|---|---|
| `T2M` | `t_mean_c` | °C |
| `T2M_MAX` | `t_max_c` | °C |
| `T2M_MIN` | `t_min_c` | °C |
| `RH2M` | `rh_pct` | % |
| `WS2M` | `wind_ms` | m/s |
| `ALLSKY_SFC_SW_DWN` | `solar_mj_m2_day` | MJ/m²/day |
| `PRECTOTCORR` | `power_rain_mm` | mm/day |

If a unit is different, tell the team before you continue.

**Step 3: make the tables:**

```python
daily = pd.DataFrame(data["properties"]["parameter"])
daily.index = pd.to_datetime(daily.index, format="%Y%m%d")
daily = daily.replace(-999.0, np.nan)          # POWER uses -999 for missing
daily = daily.rename(columns={
    "T2M": "t_mean_c", "T2M_MAX": "t_max_c", "T2M_MIN": "t_min_c", "RH2M": "rh_pct",
    "WS2M": "wind_ms", "ALLSKY_SFC_SW_DWN": "solar_mj_m2_day", "PRECTOTCORR": "power_rain_mm"})

# Daily file (keep it: we need it in Step 5 for heat days, frost days and crop water need)
daily_out = daily.reset_index().rename(columns={"index": "date"})
daily_out.to_csv("../data/processed/power_daily.csv", index=False)

# Monthly file
monthly = daily.resample("MS").mean()
monthly["power_rain_mm"] = daily["power_rain_mm"].resample("MS").sum(min_count=1)   # rain = sum
monthly = monthly.loc[f"{START_YEAR}-01-01":f"{END_YEAR}-12-01"]
monthly.insert(0, "year", monthly.index.year)
monthly.insert(1, "month", monthly.index.month)
monthly.to_csv("../data/processed/power_monthly.csv", index=False)

print(len(daily_out), "daily rows (must be 3653)")
print(len(monthly), "monthly rows (must be 108)")
```

**Checks:** 3,653 daily rows, 108 monthly rows. Summer hotter than winter. Plot `t_max_c` over time.

**Do not:** download a region. One POWER cell (about 50 km) is bigger than our whole area.

---

### 6.3 GPM - Omar

**What:** `GPM_3IMERGDF` version 07 (daily rain, mm/day), **averaged over our area**.

**Why one value for the whole area:** GPM cells are about 10 km. Our area is only about 2 x 3 GPM cells, so the differences inside it are very small.

**Step 1: download with Giovanni** (NASA website, Earthdata login):

1. Open https://giovanni.gsfc.nasa.gov and log in with your NASA Earthdata account
2. **Select Plot:** `Time Series: Area-Averaged`
3. **Date range:** `2015-01-01` to `2024-12-31`
4. **Region (bounding box):** `30.70,31.05,30.91,31.30` (West, South, East, North)
5. **Variable:** search `GPM_3IMERGDF` and choose the daily **precipitation**, version **07**, **Final Run**
6. Click **Plot Data** and wait
7. Download the result as **CSV**. Save it as `data/raw/gpm_giovanni.csv`

**Step 2: open the file and look at it first.** Giovanni puts some text lines on top.

**Step 3: make the table:**

```python
PATH = "../data/raw/gpm_giovanni.csv"

# Find the line where the table starts
lines = open(PATH).read().splitlines()
start = next(i for i, l in enumerate(lines) if l.lower().startswith("time"))

gpm = pd.read_csv(PATH, skiprows=start)
gpm.columns = ["date", "rain_mm"]
gpm["date"] = pd.to_datetime(gpm["date"])
gpm = gpm.set_index("date")
gpm = gpm.replace(-9999.9, np.nan)       # check the "Fill Value" in the top lines

monthly = pd.DataFrame({
    "rain_mm":         gpm["rain_mm"].resample("MS").sum(min_count=1),
    "rain_days":       (gpm["rain_mm"] >= 1).resample("MS").sum(),
    "max_day_rain_mm": gpm["rain_mm"].resample("MS").max(),
})
monthly = monthly.loc[f"{START_YEAR}-01-01":f"{END_YEAR}-12-01"]
monthly.insert(0, "year", monthly.index.year)
monthly.insert(1, "month", monthly.index.month)
monthly.to_csv("../data/processed/gpm_monthly.csv", index=False)
print(len(monthly), "rows (must be 108)")
```

**Checks:**
- 108 rows
- Summer months (June to September) are almost 0
- Yearly total is between a few tens and about 200 mm
- Check the fill value in the top lines of the file and replace it

**If Giovanni does not work:** use Earthdata Search (https://search.earthdata.nasa.gov) with `GPM_3IMERGDF`, and choose the option to **cut to our area** before downloading. **Never download the global daily files** (there are about 4,000). If you cannot cut to our area, ask the team first.

**Why we stop at 2024:** the GPM Final Run version 07 ends on **30 September 2025**. NASA is moving to version 08.
**Never mix version 07 and version 08** in one table. NASA says mixing them can create jumps in the record.

**Note for later:** NASA also says changes in the satellites over the years can create false changes in long-term trends. So we will say "possible trend", not "proven trend".

---

### 6.4 SMAP - Mostafa Abdelhameed

**What:** `SPL4SMGP` (SMAP Level 4, every 3 hours), at **one point** (the center).

| SMAP layer | Our column | Meaning |
|---|---|---|
| `sm_surface` | `sm_surface_m3m3` | water in the top 5 cm of soil |
| `sm_rootzone` | `sm_rootzone_m3m3` | water in the top 100 cm (roots) |

**Why one point:** SMAP really sees about 36 km. Our area is smaller than that. Different SMAP pixels inside our area are **not** real differences.

**Step 1: download with AppEEARS** (NASA website, Earthdata login):

1. Open https://appeears.earthdatacloud.nasa.gov and log in with your NASA Earthdata account
2. **Extract** → **Point Sample** → **Start a new request**
3. **Sample name:** `field_shift_smap`
4. **Coordinates:** add one point: ID `center`, latitude `31.175`, longitude `30.805`
5. **Dates:** `03-31-2015` to `12-31-2024`
6. **Product:** type `SPL4SMGP` and choose the **newest version**
7. **Layers:** choose `sm_surface` and `sm_rootzone`
8. **Submit**. You get an email when it is ready (can take some time)
9. **Explore** → your request → **Download** the CSV file. Save it as `data/raw/smap_appeears.csv`

**Step 2: make the table:**

```python
raw = pd.read_csv("../data/raw/smap_appeears.csv")
print(raw.columns.tolist())      # look at the column names first

surf = [c for c in raw.columns if "sm_surface" in c][0]
root = [c for c in raw.columns if "sm_rootzone" in c][0]

sm = pd.DataFrame({"sm_surface_m3m3": raw[surf], "sm_rootzone_m3m3": raw[root]})
sm.index = pd.to_datetime(raw["Date"])
sm = sm.replace(-9999, np.nan)                 # SMAP uses -9999 for missing

monthly = sm.resample("MS").mean()
monthly["n_obs"] = sm["sm_surface_m3m3"].resample("MS").count()
monthly = monthly.loc[f"{START_YEAR}-01-01":f"{END_YEAR}-12-01"]
monthly.insert(0, "year", monthly.index.year)
monthly.insert(1, "month", monthly.index.month)
monthly.to_csv("../data/processed/smap_monthly.csv", index=False)
print(len(monthly), "rows (must be 108)")
```

**Checks:**
- 108 rows
- Values between 0 and about 0.6
- `n_obs` is about 240 per month (8 per day). If it is much smaller, tell the team.

**Do not:** download the global SMAP files. They are very big.

---

### 6.5 SRTM - Omar

**What:** `SRTMGL1` version 003 (30 m height). Our whole area is inside **one tile: `N31E030`**.

**Step 1: download with Earthdata Search:**

1. Open https://search.earthdata.nasa.gov and log in
2. Search `SRTMGL1` and choose **NASA Shuttle Radar Topography Mission Global 1 arc second V003**
3. In the file list, find **`N31E030`** (use the search box for granules if needed)
4. Download **only this one file**
5. Unzip it into `data/raw/`. You get `N31E030.hgt`

**Step 2: make the table** (needs `grid_1km.csv` and helper code A from 3.3):

```python
import rasterio
from rasterio.windows import from_bounds

with rasterio.open("../data/raw/N31E030.hgt") as src:
    win = from_bounds(W, S, E, N, src.transform)       # cut to our area
    elev = src.read(1, window=win).astype(float)
    t = src.window_transform(win)

elev[elev == -32768] = np.nan                           # SRTM missing value

# lon / lat of every pixel center
r, c = np.indices(elev.shape)
lon = t.c + (c + 0.5) * t.a
lat = t.f + (r + 0.5) * t.e

df = pd.DataFrame({"lon": lon.ravel(), "lat": lat.ravel(), "elev": elev.ravel()})
df["cell_id"] = lonlat_to_cell(df.lon, df.lat)          # helper code A
df = df.dropna(subset=["cell_id"])
df["cell_id"] = df["cell_id"].astype(int)

out = (df.groupby("cell_id")["elev"]
         .agg(elev_mean_m="mean", elev_min_m="min", elev_max_m="max")
         .reset_index())
out.to_csv("../data/processed/srtm_static.csv", index=False)
print(len(out), "rows (must be 560)")
```

**Checks:**
- 560 rows
- About 1,200 pixels per cell
- Heights are small (our land is flat). Make a map of `elev_mean_m` with the cell `lat` / `lon`.

**Important:** SRTM can be wrong by a few meters. That is bigger than the height differences in our flat area. Use it only for "lower" vs "higher" spots. **Do not use slope for decisions.**

---

### 6.6 FAO GAEZ v5 - Fatma

**What:** GAEZ **version 5** layers (about 1 km).

**Step 1: find the layers.** Open the GAEZ v5 data portal: https://gaez.fao.org
Go to the **data access / download** page. Use the filters to find each layer. Each layer has a **download link** for a GeoTIFF file.

**Use these settings (very important):**

| Setting | Choose | Why |
|---|---|---|
| Water supply | **Irrigated** | Farming in Egypt is irrigated. "Rain-fed" says "not suitable" everywhere. |
| Input level | **High** | Our farmers use fertilizer and machines |
| Climate period | **Historical** (1981-2020) | Not the future scenarios |

**Layers to get:**
- Crop **suitability** for: wheat, rice, maize, sorghum, and beans / clover if they exist
- **Soil** constraint layers (including salt, if a layer exists)

**First, check which of our 6 crops exist in GAEZ** (wheat, berseem, faba bean, rice, maize, sorghum). Write the missing ones in your notebook conclusion.

Save each GeoTIFF in `data/raw/gaez/` with a clear name, for example `suit_wheat_irrigated_high.tif`.

**Step 2: make the table** (needs `grid_1km.csv` and helper code B from 3.4):

```python
import rioxarray

LAYERS = {
    "suit_wheat":   "../data/raw/gaez/suit_wheat_irrigated_high.tif",
    "suit_rice":    "../data/raw/gaez/suit_rice_irrigated_high.tif",
    "suit_maize":   "../data/raw/gaez/suit_maize_irrigated_high.tif",
    "suit_sorghum": "../data/raw/gaez/suit_sorghum_irrigated_high.tif",
    # add soil / salt layers here with their own names
}

out = GRID[["cell_id"]].copy()
for name, path in LAYERS.items():
    da = rioxarray.open_rasterio(path).squeeze()
    print(name, "| CRS:", da.rio.crs, "| nodata:", da.rio.nodata)   # CRS should be EPSG:4326
    da = da.rio.clip_box(minx=W - 0.05, miny=S - 0.05, maxx=E + 0.05, maxy=N + 0.05)
    vals = value_at_cell_centers(da).astype(float)                  # helper code B
    if da.rio.nodata is not None:
        vals[vals == da.rio.nodata] = np.nan
    out[name] = vals

out.to_csv("../data/processed/gaez_static.csv", index=False)
print(len(out), "rows (must be 560)")
```

**Checks:**
- 560 rows
- The CRS is EPSG:4326 (lat / lon). If not, tell the team.
- **Never average class codes.** A class like "1 = very suitable, 5 = not suitable" is a label, not a number to average. The code above takes the pixel at the center, so it is safe.
- In your notebook, add a small table that explains every class code.

---

### 6.7 Sentinel-2 and Landsat - Mostafa Sherief

**Where:** Microsoft Planetary Computer cloud catalog (STAC). Collections: `sentinel-2-l2a` and `landsat-c2-l2`. No account needed. We read **only our area**. We never download full scenes.

**Sentinel-2 rules:**

| Step | Rule |
|---|---|
| Bands | `B04` (red), `B08` (near infrared), `SCL` (cloud mask) |
| Reflectance | (DN + offset) / 10000. Since 25 January 2022 the offset is **-1000**. Read it from the image information. DN = 0 is no data. |
| Clouds | Keep SCL classes **4, 5, 6, 7**. Remove all other classes. |
| NDVI | (B08 - B04) / (B08 + B04) |
| Monthly per pixel | max NDVI of the clear images |
| Farm mask (per year) | pixel's highest monthly NDVI in the year is **0.3 or less** → not farmland → remove |
| Per cell (helper A) | `ndvi_mean`, `bare_pct` (% farm pixels with NDVI **below 0.2**), `farm_pct`, `valid_pct` |

**Landsat rules:**

| Satellite | Red | Near infrared |
|---|---|---|
| Landsat 5 and 7 | `SR_B3` | `SR_B4` |
| Landsat 8 and 9 | `SR_B4` | `SR_B5` |

- Reflectance = DN x 0.0000275 - 0.2
- Clouds: use `QA_PIXEL`. Remove fill, dilated cloud, cloud and cloud shadow.
- Per pixel: max NDVI in the year. Per cell: `ndvi_max_mean` (farm pixels only), `n_clear_images`, `sensors`.

**Checks:**
- No jump in NDVI in January 2022 (if there is a jump, the offset is wrong)
- A small jump around 2013 can be the change of satellite, not the land. Write it down.
- 0.3 and 0.2 are starting values. Check them in EDA.

The full code for this part is written in `04_sentinel_landsat.ipynb`.

---

## 7. What to put in your notebook (EDA)

Every notebook has the same 7 sections. Write a short note (plan) before each part, and a short result after it.

| # | Section | What to write or show |
|---|---|---|
| 1 | What is this dataset? | Who makes it, what it measures, pixel size, how often, link |
| 2 | Download | How you got it, the date you downloaded it, file names, file size |
| 3 | Look at the data | Number of rows, columns, first rows, first and last date, units |
| 4 | Missing values | How many missing, in which months. A small plot. |
| 5 | Simple plots | A line over time. An average for each month of the year (Jan to Dec). A map if your data is per cell. |
| 6 | Problems found | Anything strange: jumps, empty months, values out of range |
| 7 | Conclusion | What we keep, what we remove, the output file name and number of rows |

---

## 8. Merge (at the end) - Mostafa Sherief

This is where everything comes together into **one table**: `master_monthly.csv`.

### 8.1 The idea

We build an empty table with **one row for every cell in every month** (560 x 108 = 60,480 rows).
Then we add the columns of each file by matching the keys:

| File kind | Matched on | Example |
|---|---|---|
| Per cell, monthly (`sentinel2`) | `cell_id + year + month` | cell 17, January 2020 gets the NDVI of cell 17 in January 2020 |
| Whole area, monthly (`power`, `gpm`, `smap`) | `year + month` | every cell in January 2020 gets the same temperature |
| Per cell, no time (`srtm`, `gaez`) | `cell_id` | cell 17 gets the same height in every month |

`landsat_yearly.csv` stays a separate file (it is yearly, not monthly).

### 8.2 The code

Notebook `07_merge.ipynb`. After the first cell (2.5), run:

```python
import os
P = "../data/processed/"
N_CELLS, N_MONTHS = 560, 108

def add_table(master, file, keys):
    """Add one output file to the master table, with safety checks."""
    t = pd.read_csv(P + file)
    name = file.replace(".csv", "")
    # 1. the key columns must exist
    missing = [k for k in keys if k not in t.columns]
    assert not missing, f"{name}: missing key columns {missing}"
    # 2. years must be 2016-2024
    if "year" in keys:
        assert t["year"].between(START_YEAR, END_YEAR).all(), f"{name}: has years outside {START_YEAR}-{END_YEAR}"
    # 3. no column name used twice
    same = (set(t.columns) - set(keys)) & set(master.columns)
    assert not same, f"{name}: these columns already exist in master: {same}"
    # 4. no fill values left
    num = t.drop(columns=keys).select_dtypes("number")
    bad = (num <= -999).sum().sum()
    assert bad == 0, f"{name}: {bad} values are -999 or lower (fill values not removed)"
    # 5. merge (each key must appear only once in the file)
    rows_before = len(master)
    master = master.merge(t, on=keys, how="left", validate="many_to_one")
    assert len(master) == rows_before, f"{name}: number of rows changed"
    print(f"OK  {name:20s} +{len(t.columns) - len(keys)} columns")
    return master

# 1. Empty table: every cell x every month
grid = pd.read_csv(P + "grid_1km.csv")[["cell_id", "lat", "lon"]]
months = pd.date_range(f"{START_YEAR}-01-01", f"{END_YEAR}-12-01", freq="MS")
time = pd.DataFrame({"year": months.year, "month": months.month})
master = grid.merge(time, how="cross")
assert len(master) == N_CELLS * N_MONTHS

# 2. Add every file
master = add_table(master, "sentinel2_monthly.csv", ["cell_id", "year", "month"])
master = add_table(master, "power_monthly.csv",     ["year", "month"])
master = add_table(master, "gpm_monthly.csv",       ["year", "month"])
master = add_table(master, "smap_monthly.csv",      ["year", "month"])
master = add_table(master, "srtm_static.csv",       ["cell_id"])
master = add_table(master, "gaez_static.csv",       ["cell_id"])

# 3. Final checks
assert len(master) == N_CELLS * N_MONTHS                                   # 60,480
assert not master.duplicated(["cell_id", "year", "month"]).any()
assert (master.groupby("cell_id").size() == N_MONTHS).all()                # every cell has 108 months
print("\nRows:", len(master), "| Columns:", master.shape[1])
print("\nMissing values (%):")
miss = (master.isna().mean() * 100).round(1)
print(miss[miss > 0].to_string() if (miss > 0).any() else "none")

# 4. Save
master.round(4).to_csv(P + "master_monthly.csv", index=False)
print("\nSaved. Size:", round(os.path.getsize(P + "master_monthly.csv") / 1e6, 1), "MB")
```

### 8.3 What the safety checks catch

The code **stops with a clear message** if a file has a problem. Tested with these mistakes:

| Mistake in a file | Message you see |
|---|---|
| -999 or -9999 not removed | `values are -999 or lower (fill values not removed)` |
| The same month written twice | `Merge keys are not unique in right dataset` |
| A year outside 2016-2024 | `has years outside 2016-2024` |
| The same column name in two files | `these columns already exist in master` |
| A key column missing (for example `cell_id`) | `missing key columns` |

If you see one of these, **send it to the owner of that file**. Do not fix other people's files.

### 8.4 What to expect

- 60,480 rows, about 29 columns
- Missing values: only in Sentinel-2 columns (cloudy months). Everything else should be 0%.
- File size: about 10 MB. This file is allowed to be bigger than the 10 MB rule.

## 9. Checklist before every `git push`

- [ ] The first cell (2.5) runs and prints "Area OK"
- [ ] My output is a CSV in `data/processed/` and smaller than 10 MB
- [ ] Column names are exactly as in this file
- [ ] Number of rows matches section 5
- [ ] No -999, -9999, -9999.9 or -32768 left
- [ ] Months are 2016-01 to 2024-12 (Landsat: 1985 to 2024)
- [ ] My notebook has the 7 sections (section 7)
- [ ] I did **not** add anything from `data/raw/`
- [ ] I ran `git pull` before `git push`

Commands:

```
git pull
git add notebooks/YOUR_NOTEBOOK.ipynb data/processed/YOUR_FILE.csv
git commit -m "EDA for YOUR DATASET"
git push origin eda
```

Add **only your own files**. Do not use `git add .` if you are not sure what it will add.

---

## 10. Common mistakes

| Mistake | What happens | How to avoid |
|---|---|---|
| Swap latitude and longitude | You work on another area and do not notice | The first cell (2.5) stops you |
| Download full files or the whole world | Hundreds of GB | Our area only |
| Push raw data | The repo breaks | Raw data only in `data/raw/` |
| Forget the Sentinel-2 offset | NDVI is wrong from 2022 | Apply the offset, check January 2022 |
| Wrong Landsat bands | NDVI is wrong for half of the years | Table in 6.7 |
| Forget the Landsat scale | Wrong values | DN x 0.0000275 - 0.2 |
| Keep -999 / -9999 | Crazy averages | Replace with empty |
| Use 2015 or 2025 in the final tables | Wrong yearly numbers | 2016 to 2024 only |
| Rain as mean instead of sum | Rain looks 30 times smaller | Rain = sum |
| GAEZ "rain-fed" | Everything "not suitable" | Choose "irrigated" |
| Average GAEZ class codes | Numbers with no meaning | Helper code B |
| Treat SMAP pixels as different places | Fake detail | One point |
| Make your own grid | Merge fails | Use `grid_1km.csv` |
| `lonlat_to_cell(lat, lon)` | Every pixel is outside the area | Longitude first: `lonlat_to_cell(lon, lat)` |

---

## 11. If you get stuck

Send this to the team group:

1. Your dataset name
2. The step number from this file (for example "6.3 Step 3")
3. A screenshot of the error or of the strange result
4. What you expected to see

Do not change the rules in this file alone. If you think a rule is wrong, tell the team first.
