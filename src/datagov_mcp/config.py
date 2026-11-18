"""Operator-owned settings; validate without echoing secrets."""

import re
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    catalog_interface: Literal["direct", "gateway"] = "direct"
    data_gov_api_key: SecretStr = SecretStr("")
    catalog_requests_per_hour: int = Field(default=60, ge=1, le=1000)
    databricks_host: str = ""
    databricks_warehouse_id: str = ""
    databricks_token: SecretStr = SecretStr("")
    databricks_client_id: str = ""
    databricks_client_secret: SecretStr = SecretStr("")
    databricks_config_profile: str = Field(default="", pattern=r"^[A-Za-z0-9_-]*$")
    databricks_catalog: str = ""
    databricks_schema: str = ""
    databricks_table: str = "county_indicators"
    analytics_manifest: Path = Path(".local/data/manifest.json")
    evidence_dir: Path = Path(".local/evidence")
    mcp_transport: Literal["stdio", "http"] = "stdio"
    mcp_port: int = Field(default=8000, ge=1024, le=65535)

    @model_validator(mode="after")
    def explicit_profile(self):
        if self.databricks_config_profile and (
            self.databricks_token.get_secret_value()
            or self.databricks_client_id
            or self.databricks_client_secret.get_secret_value()
        ):
            raise ValueError("Select profile authentication or explicit credentials")
        return self

    @field_validator("databricks_host")
    @classmethod
    def workspace_origin(cls, value: str) -> str:
        if not value:
            return value
        # Databricks Apps inject DATABRICKS_HOST as a bare hostname.
        if re.fullmatch(r"(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}", value):
            value = "https://" + value
        parts = urlsplit(value)
        if (
            parts.scheme != "https"
            or not parts.hostname
            or parts.username
            or parts.password
            or parts.query
            or parts.fragment
            or parts.path not in ("", "/")
            or parts.port not in (None, 443)
        ):
            raise ValueError(
                "Use an HTTPS workspace origin without a path or credentials"
            )
        return value.rstrip("/")

    @field_validator(
        "databricks_catalog",
        "databricks_schema",
        "databricks_table",
        "databricks_warehouse_id",
    )
    @classmethod
    def identifier(cls, value: str) -> str:
        if value and not re.fullmatch(r"[A-Za-z0-9_]+", value):
            raise ValueError("Use only letters, digits and underscores")
        return value

    @property
    def catalog_origin(self) -> str:
        if self.catalog_interface == "direct":
            return "https://catalog.data.gov"
        return "https://api.gsa.gov/technology/datagov/v4"

    @property
    def missing_warehouse_settings(self) -> list[str]:
        names = [
            "databricks_host",
            "databricks_warehouse_id",
            "databricks_catalog",
            "databricks_schema",
        ]
        missing = [name.upper() for name in names if not getattr(self, name)]
        if (
            not self.databricks_config_profile
            and not self.databricks_token.get_secret_value()
            and not (
                self.databricks_client_id
                and self.databricks_client_secret.get_secret_value()
            )
        ):
            missing.append(
                "DATABRICKS_CONFIG_PROFILE, token or OAuth client credentials"
            )
        return missing

    @property
    def table_name(self) -> str:
        return ".".join(
            f"`{part}`"
            for part in (
                self.databricks_catalog,
                self.databricks_schema,
                self.databricks_table,
            )
        )


def configuration_errors(exc: ValidationError) -> list[dict[str, str]]:
    """Map validation locations to static hints; never render input/context/messages."""
    hints = {
        "databricks_host": "Use https:// plus workspace hostname; no path or query",
        "databricks_warehouse_id": "Use only the warehouse ID, not its HTTP path",
        "databricks_config_profile": "Use letters, digits, underscores or hyphens",
        "databricks_catalog": "Use an existing catalog: letters, digits or underscores",
        "databricks_schema": "Use an existing schema: letters, digits or underscores",
    }
    result = []
    for error in exc.errors(
        include_input=False, include_context=False, include_url=False
    ):
        location = error["loc"]
        field = str(location[0]) if location else "authentication_selection"
        hint = hints.get(field, "Check the field format in .env.example")
        if not location:
            hint = "For profile login, leave token, client ID and client secret blank"
        result.append({"field": field.upper(), "hint": hint})
    return result
