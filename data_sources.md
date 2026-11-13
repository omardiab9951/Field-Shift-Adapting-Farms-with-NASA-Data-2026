# Field Shift - Data Sources We Will Use

We need to know 7 things about the land. Each thing has one source.

| What we want to know | Source | What it gives us |
|---|---|---|
| 1. Is it hot or cold? | **NASA POWER** | Daily temperature, sun, humidity, wind |
| 2. How much rain fell? | **GPM (IMERG)** | Rain amount, every day |
| 3. Is the soil wet or dry? | **SMAP** | Soil moisture |
| 4. Is the field green or empty? | **Sentinel-2** | NDVI (plant greenness), 10 m detail |
| 5. What type is the soil? | **SoilGrids** | Clay, sand, organic carbon, pH |
| 6. Is there salt in the soil? | **FAO Salt-Affected Soils Map** | Salinity level |
| 7. How much water does a crop need, and when is it planted? | **FAO + Egypt Ministry of Agriculture** | Crop water need, planting calendar |

## In one line

We take **weather + rain + soil water + plant image from space + soil type + salt**, put them together, and tell the farmer what to plant after what.

## Not used

- **USA-only sources** (USDA, PRISM, CropScape, SSURGO, NAIP, OpenET, and others) - they do not cover Egypt. We use global sources instead.
- **Extra sources** (ECOSTRESS, GRACE, MODIS, ERA5) - only if we have time at the end.

## Accounts to create first

1. **NASA Earthdata Login** - for GPM and SMAP
2. **Copernicus Data Space** - for Sentinel-2
