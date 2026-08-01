import asyncio
import functools

from opentelemetry import trace

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config import TEMPO_BASE_URL

provider = TracerProvider()
exporter = OTLPSpanExporter(endpoint=TEMPO_BASE_URL)
processor = BatchSpanProcessor(exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


def trace_method(service_name: str):
    def decorator(func):
        global tracer

        name = service_name
        method_name = func.__name__
        labels = {"service": name, "method": method_name}

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                with tracer.start_as_current_span(f"{name}.{method_name}"):
                    return await func(self, *args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                with tracer.start_as_current_span(f"{name}.{method_name}"):
                    return func(self, *args, **kwargs)

            return sync_wrapper

    return decorator


def trace_class(service_name: str | None = None):
    def decorator(cls):
        name = service_name or cls.__name__

        for attr_name, attr_value in list(cls.__dict__.items()):
            if not callable(attr_value):
                continue

            setattr(cls, attr_name, trace_method(name)(attr_value))

        return cls

    return decorator
