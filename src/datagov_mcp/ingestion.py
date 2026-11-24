"""Operator-only preparation from explicit local publisher files."""

import argparse
import csv
import hashlib
import io
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from datagov_mcp.registry import warehouse_dataset

# Maryland has 23 counties (odd codes 001..047, excluding 007) and Baltimore city.
COUNTIES = ({f"24{code:03d}" for code in range(1, 48, 2)} - {"24007"}) | {"24510"}
YEARS = {2022, 2023, 2024}


def source_bytes(path: Path):
    if path.stat().st_size > 25_000_000:
        raise ValueError("Source exceeds 25 MB preparation limit")
    return path.read_bytes()


def population_rows(content: bytes):
    result = {}
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Census popest CSVs are published in Latin-1 (e.g. "Doña Ana County").
        text = content.decode("latin-1")
    reader = csv.DictReader(io.StringIO(text))
    needed = {"SUMLEV", "STATE", "COUNTY", "CTYNAME"} | {
        f"POPESTIMATE{y}" for y in YEARS
    }
    if not needed <= set(reader.fieldnames or []):
        raise ValueError("Expected Census Vintage 2024 county all-data CSV columns")
    for row in reader:
        if row["SUMLEV"].strip() != "050" or row["STATE"].zfill(2) != "24":
            continue
        county = row["STATE"].zfill(2) + row["COUNTY"].zfill(3)
        if county not in COUNTIES:
            raise ValueError("Unexpected Maryland county geography")
        for year in sorted(YEARS):
            key = (county, year)
            if key in result:
                raise ValueError("Duplicate Census county/year")
            value = int(row[f"POPESTIMATE{year}"])
            if value <= 0:
                raise ValueError("Population must be positive")
            result[key] = {
                "county_fips": county,
                "county_name": row["CTYNAME"],
                "state_fips": "24",
                "year": year,
                "population": value,
            }
    expected = {(county, year) for county in COUNTIES for year in YEARS}
    if set(result) != expected:
        raise ValueError(
            "Census must cover all 24 Maryland county equivalents for 2022–2024"
        )
    return result


def unemployment_rows(content: bytes):
    result = {}
    lines = content.decode("utf-8-sig").splitlines()
    if not lines or not {"series_id", "year", "period", "value"} <= set(
        lines[0].split()
    ):
        raise ValueError("Expected BLS la.data.27.Maryland tabular series file")
    for line in lines[1:]:
        fields = line.split()
        if len(fields) < 4:
            if line.strip():
                raise ValueError("Malformed BLS row")
            continue
        series, year_text, period, value_text = fields[:4]
        match = re.fullmatch(r"LAUCN(24\d{3})0000000003", series)
        if not match or period != "M13" or int(year_text) not in YEARS:
            continue
        county, year = match.group(1), int(year_text)
        if county not in COUNTIES:
            raise ValueError("Unexpected BLS county geography")
        key = (county, year)
        if key in result:
            raise ValueError("Duplicate BLS annual county/year")
        rate = float(value_text)
        if not math.isfinite(rate) or not 0 <= rate <= 100:
            raise ValueError("BLS annual unemployment rate must be between 0 and 100")
        result[key] = rate
    expected = {(county, year) for county in COUNTIES for year in YEARS}
    if set(result) != expected:
        raise ValueError(
            "BLS must cover all 24 Maryland county equivalents for 2022–2024"
        )
    return result


def prepare(population: Path, laus: Path, output: Path, reviewed: bool):
    pop_bytes, laus_bytes = source_bytes(population), source_bytes(laus)
    pop, rates = population_rows(pop_bytes), unemployment_rows(laus_bytes)
    hashes = [hashlib.sha256(b).hexdigest() for b in (pop_bytes, laus_bytes)]
    snapshot = hashlib.sha256("".join(hashes).encode()).hexdigest()[:24]
    rows = [
        {**pop[key], "unemployment_rate": rates[key], "snapshot_id": snapshot}
        for key in sorted(pop)
    ]
    serialized = json.dumps(rows, indent=2, allow_nan=False) + "\n"
    sources = [dict(s) for s in warehouse_dataset()["sources"]]
    for source, digest in zip(sources, hashes, strict=True):
        source["sha256"] = digest
        source["verification"] = (
            "operator-supplied publisher file; schema and coverage checked"
        )
    manifest = {
        "snapshot_id": snapshot,
        "state_fips": "24",
        "years": sorted(YEARS),
        "county_fips": sorted(COUNTIES),
        "row_count": len(rows),
        "sources": sources,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "data_sha256": hashlib.sha256(serialized.encode()).hexdigest(),
        "domain_reviewed": reviewed,
        "loaded_table": None,
        "review_note": "Verify publisher provenance, M13 annual averages, "
        "measure 03, Vintage 2024 and geographic comparability",
    }
    output.mkdir(parents=True, exist_ok=True)
    if (output / "manifest.json").exists() or (output / "indicators.json").exists():
        raise ValueError("Output snapshot already exists; use a new output directory")
    (output / "indicators.json").write_text(serialized)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population", type=Path, required=True)
    parser.add_argument("--laus", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/reviewed"))
    parser.add_argument(
        "--domain-reviewed",
        action="store_true",
        help="Confirm publisher provenance and metric methodology review",
    )
    args = parser.parse_args()
    try:
        result = prepare(args.population, args.laus, args.output, args.domain_reviewed)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, UnicodeError) as exc:
        raise SystemExit(
            f"Preparation failed: {type(exc).__name__}; check input/output files"
        ) from None
