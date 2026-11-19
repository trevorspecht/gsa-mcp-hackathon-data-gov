"""Prepare the fixed climate/agriculture demonstration from reviewed local files.

Download URLs and methodology are in docs/SCIENCE.md. No runtime tool downloads
these files or accepts arbitrary URLs. Rebuilds create a reviewable asset diff.
"""

import csv
import hashlib
import io
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".local/raw/climate-ag"


def climate(content, units):
    text = content.decode("utf-8-sig")
    if f"# Units: {units}" not in text:
        raise ValueError("Unexpected NOAA units")
    rows = list(
        csv.DictReader(
            io.StringIO(
                "\n".join(
                    line for line in text.splitlines() if not line.startswith("#")
                )
            )
        )
    )
    values = {}
    for row in rows:
        year = int(row["Date"][:4])
        if row["Date"] != f"{year}12" or year in values:
            raise ValueError("Expected unique calendar-year observations")
        value = Decimal(row["Value"])
        if not value.is_finite() or value <= -90:
            raise ValueError("Missing or invalid climate value")
        values[year] = float(value)
    if set(values) != set(range(1985, 2013)):
        raise ValueError("Expected exactly 1985–2012")
    return [{"year": y, "value": values[y]} for y in sorted(values)]


def practices(content, columns):
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    if reader.fieldnames != ["comid", *columns]:
        raise ValueError("Unexpected USGS columns")
    seen, totals = set(), dict.fromkeys(columns, Decimal(0))
    for row in reader:
        key = row["comid"]
        if not key.isdigit() or key in seen:
            raise ValueError("Duplicate or invalid catchment")
        seen.add(key)
        for col in columns:
            value = Decimal(row[col])
            if not value.is_finite() or value < 0:
                raise ValueError("Invalid implementation area")
            totals[col] += value
    if len(seen) != 50871:
        raise ValueError("Expected 50,871 unique NHDPlus V1 catchments")
    return [{"year": int(col[-4:]), "value": float(totals[col])} for col in columns]


def main():
    metadata = (RAW / "metadata.xml").read_bytes()
    specs = [
        (
            "md_temperature",
            "Maryland annual average temperature",
            "md-tavg.csv",
            "degrees Fahrenheit",
            "Maryland statewide",
            climate,
            "Degrees Fahrenheit",
        ),
        (
            "md_precipitation",
            "Maryland annual precipitation",
            "md-pcp.csv",
            "inches",
            "Maryland statewide",
            climate,
            "Inches",
        ),
        (
            "chesapeake_cover_crops",
            "Chesapeake estimated cover-crop implementation",
            "covcrop.csv",
            "square kilometres",
            "Chesapeake Bay watershed",
            practices,
            ["covc2002", "covc2012"],
        ),
        (
            "chesapeake_conservation_tillage",
            "Chesapeake estimated conservation-tillage implementation",
            "contill.csv",
            "square kilometres",
            "Chesapeake Bay watershed",
            practices,
            ["cont1985", "cont1992", "cont2002", "cont2012"],
        ),
    ]
    datasets = []
    for id, title, filename, unit, geography, parse, parameter in specs:
        content = (RAW / filename).read_bytes()
        noaa = id.startswith("md_")
        metric = "tavg" if id == "md_temperature" else "pcp"
        source = {
            "publisher": "NOAA NCEI"
            if noaa
            else "U.S. Geological Survey / Chesapeake Bay Program",
            "url": f"https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/statewide/time-series/18/{metric}/12/12/1985-2012.csv"
            if noaa
            else "https://doi.org/10.5066/P9SRZS8P",
            "file": filename,
            "sha256": hashlib.sha256(content).hexdigest(),
            "catalog_identifier": "https://data.noaa.gov/waf/NOAA/NESDIS/ncei/aim/iso/xml/C00005.xml"
            if noaa
            else (
                "http://datainventory.doi.gov/id/dataset/USGS_5b3bb606e4b040769c18bdc9"
            ),
        }
        datasets.append(
            {
                "id": id,
                "title": title,
                "unit": unit,
                "geography": geography,
                "source": source,
                "observations": parse(content, parameter),
                "method": (
                    "Publisher calendar-year statewide observations, January–December."
                )
                if noaa
                else (
                    "Sum published square-kilometre estimates across 50,871 unique "
                    "NHDPlus V1 catchments; Decimal arithmetic before serialization."
                ),
                "caveats": [
                    (
                        "Frozen historical demonstration, not current conditions or "
                        "climate attribution."
                    ),
                    (
                        "Maryland statewide climate and Chesapeake watershed practices "
                        "have different geography; no direct join or causal "
                        "inference is "
                        "supported."
                    ),
                    (
                        "Annual weather variability is not itself evidence of "
                        "a long-term "
                        "climate trend; two endpoints are not a trend estimate."
                    )
                    if noaa
                    else (
                        "Spatially allocated estimates from reported "
                        "practices, not direct "
                        "measurements at every catchment. Practices were reported for "
                        "soil/water-quality management, not proven climate-driven "
                        "adoption."
                    ),
                    (
                        "Published climate values may be revised; this "
                        "snapshot records "
                        "exact source hashes."
                    )
                    if noaa
                    else (
                        "Only listed observation years exist. Do not "
                        "interpolate missing "
                        "years or add cover-crop and tillage areas: practices "
                        "can overlap."
                    ),
                ],
            }
        )
    body = {
        "version": 1,
        "retrieved_date": "2026-11-19",
        "domain_reviewed": True,
        "methodology_sha256": hashlib.sha256(metadata).hexdigest(),
        "datasets": datasets,
    }
    serialized = json.dumps(body, sort_keys=True)
    body["snapshot_id"] = hashlib.sha256(serialized.encode()).hexdigest()[:24]
    (ROOT / "registry/science.json").write_text(json.dumps(body, indent=2) + "\n")
    print("Prepared", body["snapshot_id"], "reviewed science asset")


if __name__ == "__main__":
    main()
