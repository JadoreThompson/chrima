import asyncio
import functools
import logging

from opentelemetry import trace

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config import TEMPO_BASE_URL

logger = logging.getLogger("Tracer")


class Tracer:
    def __init__(self) -> None:
        self._enabled = TEMPO_BASE_URL is not None

        if not self._enabled:
            logger.warning(
                "TEMPO_BASE_URL is not configured. Distributed tracing is disabled."
            )
            self._tracer = None
            return

        provider = TracerProvider()
        exporter = OTLPSpanExporter(endpoint=TEMPO_BASE_URL)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(__name__)

    def trace_method(self, service_name: str):
        def decorator(func):
            if not self._enabled:
                return func

            name = service_name
            method_name = func.__name__

            if asyncio.iscoroutinefunction(func):

                @functools.wraps(func)
                async def async_wrapper(_self, *args, **kwargs):
                    with self._tracer.start_as_current_span(f"{name}.{method_name}"):
                        return await func(_self, *args, **kwargs)

                return async_wrapper
            else:

                @functools.wraps(func)
                def sync_wrapper(_self, *args, **kwargs):
                    with self._tracer.start_as_current_span(f"{name}.{method_name}"):
                        return func(_self, *args, **kwargs)

                return sync_wrapper

        return decorator

    def trace_class(self, service_name: str | None = None):
        def decorator(cls):
            name = service_name or cls.__name__

            for attr_name, attr_value in list(cls.__dict__.items()):
                if not callable(attr_value):
                    continue

                setattr(cls, attr_name, self.trace_method(name)(attr_value))

            return cls

        return decorator


tracer = Tracer()
trace_class = tracer.trace_class
trace_method = tracer.trace_method
