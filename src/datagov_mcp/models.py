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


class SearchEnvelope(BaseModel):
    results: list[dict]
    after: str | None = Field(default=None, max_length=8000)
    sort: str | None = None


RegistryId = Annotated[str, Field(pattern=r"^[a-z0-9_]{1,64}$")]
GeographyId = Annotated[str, Field(pattern=r"^[A-Za-z0-9_]{1,64}$")]
Period = Annotated[int, Field(ge=1800, le=2100)]


class ObservationRequest(Input):
    dataset_id: RegistryId
    measure_ids: list[RegistryId] = Field(default_factory=list, max_length=8)
    geography_ids: list[GeographyId] = Field(default_factory=list, max_length=50)
    start_period: Period | None = None
    end_period: Period | None = None

    @model_validator(mode="after")
    def bounds(self):
        if (
            self.start_period is not None
            and self.end_period is not None
            and self.end_period < self.start_period
        ):
            raise ValueError("end_period must not precede start_period")
        if len(set(self.geography_ids)) != len(self.geography_ids):
            raise ValueError("Geography IDs must be unique")
        return self


class ChangeRequest(Input):
    dataset_id: RegistryId
    measure_ids: list[RegistryId] = Field(default_factory=list, max_length=4)
    start_period: Period
    end_period: Period
    geography_ids: list[GeographyId] = Field(default_factory=list, max_length=50)
    direction_filters: dict[RegistryId, Literal["increase", "decrease"]] = Field(
        default_factory=dict, max_length=4
    )
    sort_by: RegistryId | None = None
    limit: int = Field(default=50, ge=1, le=50)

    @model_validator(mode="after")
    def periods(self):
        if self.end_period <= self.start_period:
            raise ValueError("end_period must be later than start_period")
        if len(set(self.geography_ids)) != len(self.geography_ids):
            raise ValueError("Geography IDs must be unique")
        if self.measure_ids and not set(self.direction_filters) <= set(
            self.measure_ids
        ):
            raise ValueError("Direction filters must use selected measures")
        return self


class Selection(Input):
    dataset_id: RegistryId
    measure_ids: list[RegistryId] = Field(default_factory=list, max_length=8)


class CompatibilityRequest(Input):
    datasets: list[Selection] = Field(min_length=2, max_length=4)
