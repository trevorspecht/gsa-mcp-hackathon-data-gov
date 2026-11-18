"""Strict schemas for operator-produced analytic artifacts."""

import math
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
County = Annotated[str, Field(pattern=r"^24\d{3}$")]


class Source(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    url: str
    sha256: Digest


class Manifest(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)
    snapshot_id: Annotated[str, Field(pattern=r"^[a-f0-9]{24}$")]
    state_fips: Literal["24"]
    years: list[int] = Field(min_length=3, max_length=3)
    county_fips: list[County] = Field(min_length=24, max_length=24)
    sources: list[Source] = Field(min_length=2, max_length=2)
    data_sha256: Digest
    row_count: Literal[72]
    domain_reviewed: bool
    loaded_table: str | None = None

    @model_validator(mode="after")
    def coverage(self):
        if set(self.years) != {2022, 2023, 2024}:
            raise ValueError("Snapshot requires 2022–2024")
        expected = ({f"24{c:03d}" for c in range(1, 48, 2)} - {"24007"}) | {"24510"}
        if set(self.county_fips) != expected:
            raise ValueError("Snapshot requires all Maryland county equivalents")
        if {s.id for s in self.sources} != {"census_population", "bls_laus"}:
            raise ValueError("Snapshot requires both reviewed publishers")
        return self


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    county_fips: County
    county_name: str = Field(min_length=1, max_length=150)
    state_fips: Literal["24"]
    year: int = Field(ge=2022, le=2024)
    population: int = Field(gt=0, le=10_000_000)
    unemployment_rate: float = Field(ge=0, le=100)
    snapshot_id: Annotated[str, Field(pattern=r"^[a-f0-9]{24}$")]

    @field_validator("unemployment_rate")
    @classmethod
    def finite(cls, value):
        if not math.isfinite(value):
            raise ValueError("Expected finite rate")
        return value
