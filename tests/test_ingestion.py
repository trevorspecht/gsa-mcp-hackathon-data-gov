import csv
import io

import pytest

from datagov_mcp.ingestion import COUNTIES, YEARS, population_rows, unemployment_rows


def test_population_full_grain_and_duplicate_rejected():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["SUMLEV", "STATE", "COUNTY", "CTYNAME"]
        + [f"POPESTIMATE{y}" for y in sorted(YEARS)]
    )
    for county in sorted(COUNTIES):
        writer.writerow(["050", "24", county[2:], "Synthetic county", 100, 110, 120])
    data = output.getvalue().encode()
    rows = population_rows(data)
    assert len(rows) == 72 and ("24510", 2024) in rows
    with pytest.raises(ValueError, match="Duplicate"):
        population_rows(data + b"050,24,001,Synthetic county,100,110,120\n")


def test_population_accepts_census_latin1_bytes():
    header = "SUMLEV,STATE,COUNTY,CTYNAME," + ",".join(
        f"POPESTIMATE{y}" for y in sorted(YEARS)
    )
    lines = [header, "050,35,013,Do\u00f1a Ana County,1,2,3"]
    lines += [f"050,24,{c[2:]},Synthetic county,100,110,120" for c in sorted(COUNTIES)]
    assert len(population_rows("\n".join(lines).encode("latin-1"))) == 72


def test_laus_annual_measure_and_excluded_monthly_values():
    lines = ["series_id year period value footnote_codes"]
    for county in sorted(COUNTIES):
        for year in sorted(YEARS):
            lines.append(f"LAUCN{county}0000000003 {year} M13 4.2")
            lines.append(f"LAUCN{county}0000000003 {year} M01 99.0")
    data = "\n".join(lines).encode()
    rows = unemployment_rows(data)
    assert len(rows) == 72 and set(rows.values()) == {4.2}
    with pytest.raises(ValueError, match="between"):
        unemployment_rows(data.replace(b"M13 4.2", b"M13 nan", 1))


def test_missing_sources_fail_closed():
    with pytest.raises(ValueError):
        population_rows(b"incorrect,columns\n")
    with pytest.raises(ValueError):
        unemployment_rows(b"series_id year period value\n")
