import pytest
from prometheus_client import REGISTRY


@pytest.mark.asyncio(loop_scope="session")
class TestHttpMetrics:
    async def test_records_request_count(self, client):
        before = REGISTRY.get_sample_value(
            "http_requests_total",
            {"method": "GET", "path": "/monitoring/health", "status": "200"},
        ) or 0

        rsp = await client.get("/monitoring/health")

        assert rsp.status_code == 200
        after = REGISTRY.get_sample_value(
            "http_requests_total",
            {"method": "GET", "path": "/monitoring/health", "status": "200"},
        )
        assert after == before + 1

    async def test_records_status_code(self, client):
        path = "/monitoring/health"
        before = REGISTRY.get_sample_value(
            "http_requests_total",
            {"method": "GET", "path": path, "status": "200"},
        ) or 0

        rsp = await client.get(path)
        assert rsp.status_code == 200

        after = REGISTRY.get_sample_value(
            "http_requests_total",
            {"method": "GET", "path": path, "status": "200"},
        )
        assert after == before + 1

    async def test_records_duration_histogram(self, client):
        await client.get("/monitoring/health")

        count = REGISTRY.get_sample_value(
            "http_request_duration_seconds_count",
            {"method": "GET", "path": "/monitoring/health", "status": "200"},
        )
        assert count is not None
        assert count >= 1

    async def test_records_method_label(self, client):
        await client.get("/monitoring/health")

        get_count = REGISTRY.get_sample_value(
            "http_requests_total",
            {"method": "GET", "path": "/monitoring/health", "status": "200"},
        )
        assert get_count is not None
        assert get_count >= 1
