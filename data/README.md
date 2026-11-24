# Data

All files are already-public U.S. government data.

- `raw/`: the exact publisher files used to build the reviewed snapshots. Census
  Vintage 2024 county population estimates (`co-est2024-alldata.csv`, layout PDF)
  and BLS LAUS Maryland files (`la.*`). `raw/climate-ag/`: NOAA Maryland annual
  temperature and precipitation CSVs and the USGS Chesapeake cover-crop and
  conservation-tillage CSVs with their metadata.
- `reviewed/`: the 72-row Maryland county snapshot (`indicators.json`) and its
  manifest, which records each source URL and SHA-256. Load it into a warehouse
  with `datagov-load` (see [docs/DATA.md](../docs/DATA.md)). The manifest's
  `loaded_table` refers to the hackathon workspace; a new workspace needs its own load.

Source hashes match `data/reviewed/manifest.json` and `registry/science.json`.
Publisher files may later be revised; these copies are the versions reviewed.
