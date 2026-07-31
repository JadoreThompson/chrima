import threading
from prometheus_client import start_http_server
from wsgiref.simple_server import WSGIServer
from config import PROMETHEUS_METRICS_PORT

_metrics_server_started = False
_metrics_server_lock = threading.Lock()
_server: WSGIServer | None = None
_server_thread: threading.Thread | None = None


def start_metrics_server(port: int | None = None) -> None:
    global _metrics_server_started
    global _server
    global _server_thread
    
    if _metrics_server_started:
        return

    with _metrics_server_lock:
        if _metrics_server_started:
            return
        
        _server, _server_thread = start_http_server(port or PROMETHEUS_METRICS_PORT)
        _metrics_server_started = True


def reset_metrics_server(timeout: int = 5) -> None:
    global _metrics_server_started
    global _server
    global _server_thread

    if timeout < 1:
        raise ValueError("Timeout must be greater than or equal to 1")

    if _server is None or _server_thread is None:
        raise ValueError("Failed to reset metrics server. Server is not running")
    
    th = threading.Thread(target=_server.shutdown)
    th.start()

    _server_thread.join(timeout=timeout)
    th.join(timeout=timeout)

    _metrics_server_started = False
