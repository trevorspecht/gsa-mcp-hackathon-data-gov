"""Report configuration presence only; never print credential values."""

import json

from pydantic import ValidationError

from datagov_mcp.config import Settings, configuration_errors
from datagov_mcp.registry import Registry


def main():
    try:
        settings = Settings()
        _, blocker = Registry(settings).manifest()
        print(
            json.dumps(
                {
                    "catalog_interface": settings.catalog_interface,
                    "catalog_key_present": bool(
                        settings.data_gov_api_key.get_secret_value()
                    ),
                    "warehouse_missing": settings.missing_warehouse_settings,
                    "authentication_method": (
                        "CLI OAuth profile (login not tested)"
                        if settings.databricks_config_profile
                        else "token"
                        if settings.databricks_token.get_secret_value()
                        else "OAuth client credentials"
                        if settings.databricks_client_id
                        else "not configured"
                    ),
                    "snapshot_blocker": blocker,
                    "client": "Databricks agent via authenticated App",
                    "live_connection_tested": False,
                },
                indent=2,
            )
        )
    except ValidationError as exc:
        print(json.dumps({"configuration_errors": configuration_errors(exc)}, indent=2))
        raise SystemExit(1) from None
