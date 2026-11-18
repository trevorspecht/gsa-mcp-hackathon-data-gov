import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from datagov_mcp.agent import AgentSettings, agent_workspace
from datagov_mcp.config import Settings, configuration_errors
from datagov_mcp.errors import ServiceError
from datagov_mcp.warehouse import authenticated_workspace, workspace


@pytest.fixture
def capture_auth(monkeypatch):
    import datagov_mcp.warehouse as module

    captured = {}

    def config(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(module, "Config", config)
    monkeypatch.setattr(
        module, "WorkspaceClient", lambda config: SimpleNamespace(config=config)
    )
    return captured


def profile_settings(**kwargs):
    return Settings(
        _env_file=None,
        databricks_host="https://workspace.example.com",
        databricks_config_profile="hackathon",
        **kwargs,
    )


def test_profile_warehouse_auth_does_not_require_service_principal(capture_auth):
    settings = profile_settings(
        databricks_catalog="curated",
        databricks_schema="demo",
        databricks_warehouse_id="warehouse",
    )
    assert settings.missing_warehouse_settings == []
    workspace(settings)
    assert capture_auth["auth_type"] == "databricks-cli"
    assert capture_auth["profile"] == "hackathon"
    assert "token" not in capture_auth and "client_secret" not in capture_auth


def test_agent_uses_same_explicit_oauth_profile(capture_auth):
    settings = AgentSettings(
        **profile_settings().model_dump(),
        _env_file=None,
        databricks_mcp_url="https://app.example.com/mcp",
        databricks_model_endpoint="model",
    )
    agent_workspace(settings)
    assert capture_auth["auth_type"] == "databricks-cli"


@pytest.mark.parametrize(
    "field",
    [
        "databricks_token",
        "databricks_client_id",
        "databricks_client_secret",
    ],
)
def test_profile_cannot_silently_mix_credentials(field):
    with pytest.raises(ValidationError):
        profile_settings(**{field: "synthetic"})


def test_profile_login_failure_does_not_fall_back(monkeypatch):
    import datagov_mcp.warehouse as module

    calls = []

    def fail(**kwargs):
        calls.append(kwargs)
        raise ValueError("login required")

    monkeypatch.setattr(module, "Config", fail)
    with pytest.raises(ValueError, match="login required"):
        authenticated_workspace(profile_settings())
    assert len(calls) == 1 and calls[0]["auth_type"] == "databricks-cli"


def test_pat_is_warehouse_only(capture_auth):
    settings = Settings(_env_file=None, databricks_token="synthetic")
    authenticated_workspace(settings)
    assert capture_auth["auth_type"] == "pat"
    with pytest.raises(ServiceError) as exc:
        authenticated_workspace(settings, require_oauth=True)
    assert exc.value.code == "OAUTH_REQUIRED"


def test_m2m_remains_available_for_app(capture_auth):
    settings = Settings(
        _env_file=None,
        databricks_client_id="synthetic",
        databricks_client_secret="synthetic",  # pragma: allowlist secret
    )
    authenticated_workspace(settings, require_oauth=True)
    assert capture_auth["auth_type"] == "oauth-m2m"


def test_validation_diagnostics_never_echo_input():
    marker = "SENSITIVE_EXAMPLE_VALUE"
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None, databricks_host=marker)
    output = json.dumps(configuration_errors(exc.value))
    assert marker not in output
    assert "DATABRICKS_HOST" in output and "https://" in output
