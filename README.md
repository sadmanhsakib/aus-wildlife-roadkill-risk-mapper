# 🦘 aus-wildlife-roadkill-risk

> **⚠️ This project is currently a work in progress.** Active development is paused and will resume in a few weeks. The current codebase represents the early-stage foundation of the project.

## Overview

A Python-based tool for analysing **wildlife-vehicle collision risk** in Australia. The project fetches wildlife sighting data from biodiversity databases and overlays it with road network data to identify high-risk zones where animals are most likely to encounter traffic.

Currently focused on **kangaroos** (*Macropus giganteus*) and **wombats** (*Vombatus ursinus*).

## How It Works

1. **Data Fetching** — Pulls wildlife occurrence records from:
   - [GBIF](https://www.gbif.org/) (Global Biodiversity Information Facility)
   - [ALA](https://www.ala.org.au/) (Atlas of Living Australia)

2. **Data Cleaning** — Standardises and filters the raw sighting data (removes duplicates, missing coordinates, etc.)

3. **Spatial Risk Analysis** — Uses GeoPandas and OSMnx to:
   - Overlay sighting locations on Australian road networks
   - Buffer roads by 500m to define a risk zone
   - Classify each sighting as **high-risk** (within 500m of a road) or **low-risk**

4. **Visualisation** — Plots the road network, buffer zones, and colour-coded sightings on a map

## Project Structure

```
├── fetcher.py          # Fetches & cleans data from GBIF and ALA APIs
├── risk-analyzer.py    # Spatial analysis & visualisation
├── sightings/          # Cached sighting data (JSON & CSV)
├── roads/              # Australian SA1 boundary shapefiles
├── .env                # API keys and config (not committed)
├── requirements.txt    # Python dependencies
└── test.py             # Scratch/testing file
```

## Tech Stack

- **Python 3**
- **Pandas / GeoPandas** — Data manipulation & spatial operations
- **OSMnx** — Road network retrieval from OpenStreetMap
- **Matplotlib** — Visualisation
- **Shapely** — Geometric operations
- **Requests** — API calls

## Current Status

This is an **early-stage prototype**. The core data pipeline and basic risk analysis are functional, but there is still significant work planned, including but not limited to:

- [ ] Expanding species coverage beyond kangaroos and wombats
- [ ] Analysing multiple regions beyond the ACT
- [ ] Improving risk classification methodology
- [ ] Adding density-based hotspot detection
- [ ] Building a more polished output/reporting system

## Setup

1. Clone the repo
2. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the required API URLs (see `.env.example` if available)
4. Run the fetcher to pull sighting data:
   ```bash
   python fetcher.py
   ```
5. Run the risk analyser:
   ```bash
   python risk-analyzer.py
   ```

## License

See [LICENSE](LICENSE) for details.