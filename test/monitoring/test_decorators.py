import pytest
from prometheus_client import REGISTRY

from chrima.monitoring import trace_method, trace_class


@pytest.mark.asyncio(loop_scope="session")
class TestTraceMethod:
    async def test_records_success_count(self):
        class FakeService:
            @trace_method("TestService")
            async def do_work(self):
                return 42

        before = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "TestService", "method": "do_work", "status": "success"},
        ) or 0

        svc = FakeService()
        result = await svc.do_work()

        assert result == 42
        after = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "TestService", "method": "do_work", "status": "success"},
        )
        assert after == before + 1

    async def test_records_error_count(self):
        class FakeService:
            @trace_method("TestService")
            async def fail_work(self):
                raise ValueError("boom")

        before = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "TestService", "method": "fail_work", "status": "error"},
        ) or 0

        svc = FakeService()
        with pytest.raises(ValueError):
            await svc.fail_work()

        after = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "TestService", "method": "fail_work", "status": "error"},
        )
        assert after == before + 1

    async def test_records_success_on_sync_method(self):
        class FakeService:
            @trace_method("TestService")
            def sync_work(self):
                return "done"

        before = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "TestService", "method": "sync_work", "status": "success"},
        ) or 0

        svc = FakeService()
        result = svc.sync_work()

        assert result == "done"
        after = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "TestService", "method": "sync_work", "status": "success"},
        )
        assert after == before + 1

    async def test_records_error_on_sync_method(self):
        class FakeService:
            @trace_method("TestService")
            def sync_fail(self):
                raise RuntimeError("fail")

        before = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "TestService", "method": "sync_fail", "status": "error"},
        ) or 0

        svc = FakeService()
        with pytest.raises(RuntimeError):
            svc.sync_fail()

        after = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "TestService", "method": "sync_fail", "status": "error"},
        )
        assert after == before + 1

    async def test_records_duration_histogram(self):
        class FakeService:
            @trace_method("TestService")
            async def slow_work(self):
                return "ok"

        svc = FakeService()
        await svc.slow_work()

        count = REGISTRY.get_sample_value(
            "service_method_duration_seconds_count",
            {"service": "TestService", "method": "slow_work"},
        )
        assert count is not None
        assert count >= 1

    async def test_uses_method_name_as_label(self):
        class FakeService:
            @trace_method("TestService")
            async def custom_name(self):
                return "ok"

        svc = FakeService()
        await svc.custom_name()

        counter = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "TestService", "method": "custom_name", "status": "success"},
        )
        assert counter is not None
        assert counter >= 1


@pytest.mark.asyncio(loop_scope="session")
class TestTraceClass:
    async def test_wraps_public_methods(self):
        @trace_class()
        class MyService:
            async def run(self):
                return "running"

            async def handle_event(self):
                return "handled"

            def stop(self):
                pass

        svc = MyService()
        await svc.run()
        await svc.handle_event()
        svc.stop()

        run_count = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "MyService", "method": "run", "status": "success"},
        )
        handle_count = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "MyService", "method": "handle_event", "status": "success"},
        )
        stop_count = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "MyService", "method": "stop", "status": "success"},
        )

        assert run_count is not None and run_count >= 1
        assert handle_count is not None and handle_count >= 1
        assert stop_count is not None and stop_count >= 1

    async def test_skips_private_methods(self):
        @trace_class()
        class MyService:
            async def run(self):
                return "running"

            async def _internal(self):
                return "internal"

            def __private(self):
                return "private"

        svc = MyService()

        run_before = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "MyService", "method": "run", "status": "success"},
        ) or 0

        await svc._internal()
        svc._MyService__private()

        run_after = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "MyService", "method": "run", "status": "success"},
        )

        assert run_after == run_before

    async def test_uses_custom_service_name(self):
        custom_before = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "CustomName", "method": "run", "status": "success"},
        ) or 0

        @trace_class("CustomName")
        class MyService:
            async def run(self):
                return "running"

        svc = MyService()
        await svc.run()

        custom_after = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "CustomName", "method": "run", "status": "success"},
        )
        assert custom_after == custom_before + 1

    async def test_records_error_on_public_method(self):
        @trace_class()
        class MyService:
            async def run(self):
                raise ConnectionError("fail")

        before = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "MyService", "method": "run", "status": "error"},
        ) or 0

        svc = MyService()
        with pytest.raises(ConnectionError):
            await svc.run()

        after = REGISTRY.get_sample_value(
            "service_method_calls_total",
            {"service": "MyService", "method": "run", "status": "error"},
        )
        assert after == before + 1
