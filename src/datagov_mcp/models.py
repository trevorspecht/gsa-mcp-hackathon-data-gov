"""Bounded public tool contracts. Metadata remains untrusted source data."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1, max_length=300)]
Slug = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,200}$")]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class SearchRequest(Input):
    query: str = Field(default="", max_length=500)
    organization: Slug | None = None
    organization_type: (
        Literal[
            "Federal Government",
            "State Government",
            "City Government",
            "County Government",
            "University",
            "Tribal",
            "Non-Profit",
        ]
        | None
    ) = None
    keywords: list[Text] = Field(default_factory=list, max_length=5)
    location_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,100}$")
    spatial_within: bool = False
    sort: Literal["relevance", "popularity", "last_harvested_date"] = "relevance"
    limit: int = Field(default=5, ge=1, le=10)
    cursor: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")

    @model_validator(mode="after")
    def bounded_intent(self):
        if not any(
            (
                self.query.strip(),
                self.organization,
                self.keywords,
                self.location_id,
                self.organization_type,
            )
        ):
            raise ValueError("Supply a query or filter instead of walking the catalog")
        if self.spatial_within and not self.location_id:
            raise ValueError("spatial_within requires a location_id")
        return self


class CompareRequest(Input):
    metric_ids: list[Text] = Field(
        default_factory=lambda: ["population", "unemployment_rate"],
        min_length=2,
        max_length=2,
    )
    state_fips: str = Field(default="24", pattern=r"^\d{2}$")
    start_year: int = Field(default=2022, ge=1900, le=2100)
    end_year: int = Field(default=2024, ge=1900, le=2100)
    county_fips: list[str] = Field(default_factory=list, max_length=24)
    population_direction: Literal["any", "increase", "decrease"] = "any"
    unemployment_direction: Literal["any", "increase", "decrease"] = "any"
    sort_by: Literal["county", "population_change", "unemployment_change"] = "county"
    limit: int = Field(default=24, ge=1, le=24)

    @model_validator(mode="after")
    def periods_and_counties(self):
        if self.start_year >= self.end_year:
            raise ValueError("end_year must be later than start_year")
        if len(set(self.metric_ids)) != 2:
            raise ValueError("Select two distinct metrics")
        if len(set(self.county_fips)) != len(self.county_fips):
            raise ValueError("County FIPS must be unique")
        if any(
            len(c) != 5
            or not c.isascii()
            or not c.isdigit()
            or not c.startswith(self.state_fips)
            for c in self.county_fips
        ):
            raise ValueError(
                "County FIPS must be five digits within the selected state"
            )
        return self


class SearchEnvelope(BaseModel):
    results: list[dict]
    after: str | None = Field(default=None, max_length=8000)
    sort: str | None = None
