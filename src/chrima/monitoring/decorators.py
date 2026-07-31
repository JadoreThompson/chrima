import asyncio
import functools

from .metrics import service_method_calls_total, service_method_duration_seconds
from .server import start_metrics_server

_metrics_server_ensured = False


def _ensure_metrics_server() -> None:
    global _metrics_server_ensured
    
    if _metrics_server_ensured:
        return
    _metrics_server_ensured = True
    start_metrics_server()


def trace_method(service_name: str):
    def decorator(func):
        name = service_name
        method_name = func.__name__
        labels = {"service": name, "method": method_name}

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                _ensure_metrics_server()
                with service_method_duration_seconds.labels(**labels).time():
                    try:
                        result = await func(self, *args, **kwargs)
                        service_method_calls_total.labels(
                            **labels, status="success"
                        ).inc()
                        return result
                    except Exception:
                        service_method_calls_total.labels(
                            **labels, status="error"
                        ).inc()
                        raise

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                _ensure_metrics_server()
                with service_method_duration_seconds.labels(**labels).time():
                    try:
                        result = func(self, *args, **kwargs)
                        service_method_calls_total.labels(
                            **labels, status="success"
                        ).inc()
                        return result
                    except Exception:
                        service_method_calls_total.labels(
                            **labels, status="error"
                        ).inc()
                        raise

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
