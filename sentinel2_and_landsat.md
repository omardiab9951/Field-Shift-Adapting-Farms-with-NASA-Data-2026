# Sentinel-2 and Landsat - What We Use Them For

Both are satellites. Both take pictures of the land from space. Both are free.

We use both, but for two different jobs.

---

## 1. What is the difference?

| | Sentinel-2 | Landsat |
|---|---|---|
| Picture detail | 10 meters (clear) | 30 meters (less clear) |
| Oldest picture | 2015 | 1984 |
| How often it passes | every 5 days | every 8 days |

**Simple way to say it:**

- Sentinel-2 = a good camera, but only has photos from 2015.
- Landsat = an older camera, but has photos from 1984.

---

## 2. Why do we need a clear picture? (Sentinel-2)

In Egypt, one farm field is small. About 65 meters x 65 meters (one feddan).

- With Landsat (30 m): one field is only 4 pixels. Too small to see.
- With Sentinel-2 (10 m): one field is 42 pixels. We can see inside it.

So for looking at **one farm**, we need Sentinel-2.

---

## 3. Why do we need old pictures? (Landsat)

The NASA challenge asks about **long-term change**.

- Sentinel-2 has 11 years. This is not enough to show a real change.
- Landsat has 42 years. This is enough.

So for showing **how the area changed over time**, we need Landsat.

---

## 4. What we will do with each one

### Sentinel-2 - the farm today

We calculate NDVI.
NDVI is a number that tells us if the land is green or empty.

- High number = plants are growing
- Low number = the land is empty soil

From this we find:

1. **Empty months** - months when the field has no plants.
   Empty soil loses water and the wind takes the good soil away.
2. **Stress months** - months when the plants look weak.

This is the main result we show the farmer:
*"Your field is empty 4 months every year."*

### Landsat - the area over 40 years

We take one NDVI value per year, from 1984 until now.

Then we look at the line:

- Going down = the area is getting drier
- Going up = the area is getting better

This gives us the big picture, and it supports our advice with history.

---

## 5. Why both and not one?

If we use **only Sentinel-2**:
We can see the field, but we cannot say the area is changing. We only have 11 years.

If we use **only Landsat**:
We can see the change, but we cannot see one small Egyptian field. 30 meters is too big.

Using both covers the two things the challenge asks for:
**the farm now** + **the change over time**.

---

## 6. How it fits in the project

```
Sentinel-2  -->  empty months + stress months  -->  "your soil is bare, add a cover crop"

Landsat     -->  40-year trend               -->  "the area is getting drier, use less water"
```

Both results go into the scoring. They help us choose which crop rotation is better for this farm.

---

## 7. Where to get them

- Sentinel-2: Copernicus Data Space - https://dataspace.copernicus.eu
- Landsat: USGS EarthExplorer - https://earthexplorer.usgs.gov

Both need a free account.
