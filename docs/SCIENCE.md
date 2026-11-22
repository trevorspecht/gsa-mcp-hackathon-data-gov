---
title: "Climate and agriculture demonstration"
description: "Reviewed historical series, units, boundaries and scientific limitations"
status: draft
tier: 2
related_files: ["DATA.md", "EVALUATION.md", "../registry/science.json"]
---

# Climate and agriculture

This example supports exploration of climate observations and changing agricultural
practices, **not a claim that climate caused practice adoption**. These four series
are ordinary entries in the generic dataset registry (`registry/datasets.json`) and
are served by the same `query_dataset`, `analyze_change` and `assess_compatibility`
tools as every other registered dataset. Observations come from the small reviewed
`registry/science.json` packaged snapshot. The NOAA entries also register a fixed
publisher CSV route: `query_dataset` with `live=true` refreshes them within
25-second and 100-KB limits, with strict unit/coverage validation and source hashes.
USGS entries have no live route. No arbitrary downloads, SQL or cross-source joins
are accepted. Raw files stay in `.local/raw/climate-ag`.

## Climate observations

NOAA NCEI Climate at a Glance, Maryland statewide annual values, 1985–2012:

- [Average temperature](https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/statewide/time-series/18/tavg/12/12/1985-2012.csv): degrees Fahrenheit.
- [Precipitation](https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/statewide/time-series/18/pcp/12/12/1985-2012.csv): inches.

The publisher files identify January–December and the units; exactly 28 unique
calendar years are required. These historical observations may be revised. Two
endpoint values are not a fitted climate trend or an attribution study.
The Data.gov NClimDiv parent record is
`https://data.noaa.gov/waf/NOAA/NESDIS/ncei/aim/iso/xml/C00005.xml`.

## Agricultural-practice estimates

USGS [Implementation of conservation tillage and cover crops in the Chesapeake
Bay watershed](https://doi.org/10.5066/P9SRZS8P), ScienceBase item
`5b3bb606e4b040769c18bdc9`:

- `contill.csv`: conservation tillage, 1985/1992/2002/2012.
- `covcrop.csv`: cover crops, 2002/2012.
- `contillcovcropmeta.xml`: publisher methods and attribute dictionary.

Both tables contain 50,871 unique NHDPlus V1 catchment IDs. **Column units are
square kilometres**, despite source reporting in acres earlier in the processing
chain. The preparation script sums each year's published catchment estimates
using decimal arithmetic. Cover-crop totals: 481.5090 km² (2002) and 1770.5665 km²
(2012). Tillage totals: 8077.0353, 7057.3240, 7217.6969 and 8403.0951 km².

These are spatially allocated estimates derived from reported best-management
practices and 2001 land cover, not surveys of every catchment or farm. The study
purpose is soil-loss and water-quality modeling. Do not label these climate-driven
changes. Practice areas can overlap; do not add tillage and cover-crop totals.
Missing years are not zero and must not be interpolated. Metadata use constraints
are `none`; cite the USGS release and Chesapeake Bay Program methods.

## Verification and reproducibility

Fetched November 19, 2026. `scripts/prepare_science.py` validates units, years,
columns, numeric values and unique catchments, records original file hashes and
methodology hash, and writes a content-derived snapshot ID. Runtime checks that
identity before returning any series. Evidence records contain parameters, units,
methods, returned observations and publisher hashes.

**Geographic incompatibility:** climate is Maryland statewide; practices cover the
Chesapeake watershed across multiple states. Display separate labeled charts, not
an aligned causal plot or correlation. A future analysis needs compatible geography,
coverage and a design addressing policy, prices, water access and other drivers.
