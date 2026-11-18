from types import SimpleNamespace as NS

import pytest

from datagov_mcp.errors import ServiceError
from datagov_mcp.warehouse import Warehouse


def test_pending_query_cancels_and_reports_timeout():
    canceled = []
    client = NS(statement_execution=NS(cancel_execution=canceled.append))
    response = NS(status=NS(state=NS(value="RUNNING")), statement_id="query-1")
    with pytest.raises(ServiceError) as exc:
        Warehouse._result(client, response)
    assert exc.value.code == "QUERY_TIMEOUT" and canceled == ["query-1"]


def test_truncated_results_are_not_reported_as_complete():
    response = NS(
        status=NS(state=NS(value="SUCCEEDED")),
        manifest=NS(truncated=True, total_chunk_count=1),
    )
    with pytest.raises(ServiceError) as exc:
        Warehouse._result(None, response)
    assert exc.value.code == "QUERY_TRUNCATED"
