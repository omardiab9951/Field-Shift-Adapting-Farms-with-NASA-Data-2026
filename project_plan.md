# Field Shift - Full Project Plan

This file explains every step, from today until we submit.
Read it before you start your part.

---

## The idea in one line

We take satellite data about a farm, and we tell the farmer which crop rotation is better for his land, and why.

## The order of work

```
Pick the area -> Look at the data -> Download it -> Make one table
-> Calculate signals -> Score 3 rotations -> Explain them -> Build the website -> Submit
```

---

# PART 1 - THE DATA

## Step 0 - Choose the data sources ✅ DONE

We chose 7 sources. All of them come from the official NASA Resources list.
See the file `data_sources.md`.

---

## Step 1 - Choose the pilot area 🔜 NEXT

**What we do:**
Pick one small area in the Nile Delta, about 20 km x 20 km.
Write down its 4 corner coordinates.

**Why:**
Satellite data for the whole world is huge. Hundreds of gigabytes.
For one small area it is small and fast.

**Output:** 4 numbers (north, south, east, west).

**Important:** Nobody downloads anything before this step is finished.
If we change the area later, all downloads are wasted.

**Time:** 30 minutes.

---

## Step 2 - EDA (look at the data) 🔄 IN PROGRESS

**What we do:**
Each person opens their own dataset and learns what is inside it.

**Why:**
Every dataset has problems: missing days, clouds, strange numbers.
It is better to find them now than later.

**Who:** everyone, on their own notebook.

**Each notebook has the same 7 sections:**

1. What is this dataset?
2. Download a small sample
3. Look at it - shape, dates, columns
4. Missing values - how many and where
5. Simple plots
6. Problems found
7. Conclusion

**Output:** 6 notebooks in the `notebooks` folder.

---

## Step 3 - Download the real data

**What we do:**
Each person downloads their full dataset, for the pilot area only, for about 10 years.
Save it in the `data` folder.

**Why:**
We need it saved on our computers before the event.

**Important:**
Never download during the presentation. The internet can be slow or fail.
Download early. Keep a note of what you downloaded and from where.

**Output:** data files saved on disk.

---

# PART 2 - MAKE THE DATA USABLE

## Step 4 - Harmonization

**The problem:**
Our 6 datasets do not match each other.

- Sentinel-2 sees 10 meters. SMAP sees 9 kilometers.
- GPM gives data every 30 minutes. Landsat gives it every 8 days.

We cannot compare them like this.

**What we do:**
Put everything on the same map grid and the same time step (one month).

- Detailed data (like NDVI) -> take the average inside each square
- Rough data (like SMAP) -> stretch it over the smaller squares
- Rain -> add it up for the month
- Temperature and NDVI -> take the average for the month

**Output:** ONE table. One row for each square, for each month.

| square | month | rain | temp | soil moisture | ndvi | slope | soil type |
|---|---|---|---|---|---|---|---|

**This is the hardest technical part of the project.**

---

## Step 5 - Calculate the signals

**What we do:**
Raw numbers do not help a farmer. We turn them into useful signals.

| Signal | What it means | From |
|---|---|---|
| Soil moisture anomaly | This month is drier than normal | SMAP |
| Bare-field months | Months with no plants on the field | Sentinel-2 |
| Stress months | Months when plants look weak | Sentinel-2 |
| Heat days | Days too hot for the crop | NASA POWER |
| Frost days | Days too cold | NASA POWER |
| Rain trend | Is rain going down over the years? | GPM |
| 40-year trend | Is the area getting drier? | Landsat |
| Erosion risk | Slope + heavy rain | SRTM + GPM |
| Water balance | Rain minus water the crop needs | GPM + POWER |

**Output:** new columns in the same table.

---

## Step 6 - Build the crop table

**What we do:**
A small table. One row per crop. About 6 rows.
This is not a download. We write it by hand.

| Crop | Water need | Fixes nitrogen? | Covers the soil? | Planted | Harvested |
|---|---|---|---|---|---|
| Wheat | 1.15 | No | Medium | November | May |
| Berseem | 0.90 | Yes | Very good | October | April |
| Faba bean | 1.15 | Yes | Medium | November | April |
| Rice | 1.20 | No | Flooded | May | October |
| Maize | 1.20 | No | Medium | May | October |
| Sorghum | 1.05 | No | Deep roots | May | September |

**Why we need it:**
The satellite tells us about the land. It never tells us how much water wheat drinks.
That comes from agriculture books.

**Note:** This step does not wait for any data. It can start today.

**Output:** `crops.csv`

---

# PART 3 - THE BRAIN

## Step 7 - Build and score the rotations

**What we do:**
Build 3 rotation options and give each one a score.

- **Option A:** what the farmer grows now (the baseline)
- **Option B:** add a crop that fixes nitrogen (better soil)
- **Option C:** use less water (drought crop + cover crop)

**How we score:**

1. Choose the criteria: water use, soil health, erosion, pests, income, climate fit
2. Give each option a score from 0 to 1 on each criterion
3. The farmer moves sliders to say what matters to him -> this becomes the weights
4. Final score = weighted average
5. Show the ranking, AND show every single score, so the farmer sees why

**Why not machine learning?**
The challenge asks us to explain why each option is suggested.
A black box cannot explain itself. A clear scoring system can.
We can still use ML for small things, like grouping fields with similar conditions.

**Output:** code that takes a location + priorities and returns 3 ranked options.

---

## Step 8 - Confidence and explanation

**This step is required by the challenge. Do not skip it.**

**What we do:**
Every option comes with a short text:

1. **Why** we suggested it
2. **Evidence** - which signals support it
3. **Benefits** - for soil, water, pests, income
4. **Gaps** - what we do not know
5. **Risks** - what a local expert must check

And a confidence level: high, medium, or low.

**Confidence goes down when:**
- many satellite values were missing (clouds)
- we stretched rough data onto a fine grid
- we used a default value instead of real local data
- two datasets disagree

**Always show this line:** this tool supports the farmer, it does not replace him.

---

# PART 4 - THE PRODUCT

## Step 9 - Build the website

**5 screens:**

| Screen | The farmer does |
|---|---|
| 1. Location | Clicks his farm on the map |
| 2. Current rotation | Picks his crops and their order |
| 3. Soil and limits | Water, equipment, market (optional) |
| 4. Priorities | Moves sliders - save water, income, soil |
| 5. Results | Sees 3 options with scores, charts, and explanations |

**Design rules:**
- Few inputs. Sliders and dropdowns, not typing.
- Simple words. The farmer is not a scientist.
- Arabic and English if we have time.

---

## Step 10 - Submit

**What we need:**
- A short video
- The project page filled in
- A link to the public repo
- A list of every dataset we used, with its name and source

**Submit hours early.**
Many good teams lose because they submit in the last 15 minutes.

---

# HOW THE JUDGES SCORE US

Five criteria: Impact, Creativity, Validity, Relevance, Presentation.

| Criterion | Where we win it |
|---|---|
| Relevance | Steps 7 and 8 - the challenge asked for 3 rotations plus explanation, we did exactly that |
| Validity | Steps 4 and 5 - a clear scientific method, not a black box |
| Impact | We chose Egypt - a real water problem for millions of farmers |
| Creativity | Salinity and rotation logic - most teams will not do this |
| Presentation | Step 10 |

---

# THE 3 BIGGEST MISTAKES

1. **Downloading data too late** - no data on demo day
2. **Skipping the explanation and confidence part** - we lose Relevance directly
3. **A nice website with no real data behind it** - judges find this with one question

---

# WHAT CAN START RIGHT NOW

These do not wait for anything:

- Step 1 (pick the area) - 30 minutes
- Step 2 (EDA) - everyone
- Step 6 (crop table) - one person
