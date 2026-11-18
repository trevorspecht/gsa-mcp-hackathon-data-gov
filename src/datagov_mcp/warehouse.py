"""Execute reviewed statements with server-side wait cancellation and inline bounds."""

from databricks.sdk import WorkspaceClient
from databricks.sdk.config import Config
from databricks.sdk.service.sql import (
    Disposition,
    ExecuteStatementRequestOnWaitTimeout,
    Format,
    StatementParameterListItem,
)

from datagov_mcp.config import Settings
from datagov_mcp.errors import ServiceError


def workspace(settings: Settings):
    if settings.missing_warehouse_settings:
        raise ServiceError(
            "SETUP_REQUIRED",
            "Databricks configuration is incomplete",
            "Run datagov-setup-check and fill the named environment fields",
        )
    return authenticated_workspace(settings)


def authenticated_workspace(settings: Settings, *, require_oauth=False):
    """Explicit profile uses CLI OAuth only; never falls back to another auth type."""
    auth = {"host": settings.databricks_host}
    if settings.databricks_config_profile:
        auth.update(
            profile=settings.databricks_config_profile, auth_type="databricks-cli"
        )
    elif settings.databricks_token.get_secret_value() and require_oauth:
        raise ServiceError(
            "OAUTH_REQUIRED",
            "Databricks Apps requires OAuth",
            "Use a named CLI OAuth profile or OAuth client credentials",
        )
    elif settings.databricks_token.get_secret_value():
        auth.update(token=settings.databricks_token.get_secret_value(), auth_type="pat")
    elif (
        settings.databricks_client_id
        and settings.databricks_client_secret.get_secret_value()
    ):
        auth.update(
            client_id=settings.databricks_client_id,
            client_secret=settings.databricks_client_secret.get_secret_value(),
            auth_type="oauth-m2m",
        )
    else:
        raise ServiceError(
            "SETUP_REQUIRED",
            "Select a Databricks authentication method",
            "Set DATABRICKS_CONFIG_PROFILE after CLI OAuth login",
        )
    return WorkspaceClient(
        config=Config(
            **auth,
            http_timeout_seconds=40,
            retry_timeout_seconds=45,
            debug_headers=False,
            debug_truncate_bytes=0,
        )
    )


class Warehouse:
    def __init__(self, settings: Settings, client=None):
        self.settings = settings
        self.client = client

    def execute(self, sql: str, parameters: dict, row_limit=100):
        try:
            client = self.client or workspace(self.settings)
            response = client.statement_execution.execute_statement(
                statement=sql,
                warehouse_id=self.settings.databricks_warehouse_id,
                parameters=[
                    StatementParameterListItem(
                        name=k,
                        value=str(v),
                        type=(
                            "INT"
                            if isinstance(v, int)
                            else "DOUBLE"
                            if isinstance(v, float)
                            else "STRING"
                        ),
                    )
                    for k, v in parameters.items()
                ],
                disposition=Disposition.INLINE,
                format=Format.JSON_ARRAY,
                byte_limit=64_000,
                row_limit=row_limit,
                wait_timeout="30s",
                on_wait_timeout=ExecuteStatementRequestOnWaitTimeout.CANCEL,
            )
            return self._result(client, response)
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                "WAREHOUSE_ERROR",
                "Warehouse operation failed",
                "Check warehouse access, table grants and query history",
            ) from exc

    @staticmethod
    def _result(client, response):
        state = (
            response.status.state.value
            if response.status and response.status.state
            else "UNKNOWN"
        )
        if state in ("PENDING", "RUNNING"):
            if response.statement_id:
                client.statement_execution.cancel_execution(response.statement_id)
            raise ServiceError(
                "QUERY_TIMEOUT",
                "Query exceeded its synchronous budget",
                "Inspect warehouse query history; cancellation was requested",
            )
        if state != "SUCCEEDED":
            raise ServiceError(
                "QUERY_FAILED",
                f"Warehouse query state: {state}",
                "Inspect warehouse query history; no automatic retry is made",
            )
        manifest = response.manifest
        if manifest and (manifest.truncated or (manifest.total_chunk_count or 0) > 1):
            raise ServiceError(
                "QUERY_TRUNCATED",
                "Warehouse result exceeded inline bounds",
                "Reduce the approved query scope",
            )
        columns = (
            [c.name for c in manifest.schema.columns]
            if manifest and manifest.schema
            else []
        )
        rows = (
            response.result.data_array
            if response.result and response.result.data_array
            else []
        )
        if any(len(row) != len(columns) for row in rows):
            raise ServiceError(
                "INVALID_RESPONSE",
                "Warehouse columns do not match rows",
                "Inspect the query schema",
            )
        return {
            "query_id": response.statement_id,
            "rows": [dict(zip(columns, row, strict=True)) for row in rows],
        }
