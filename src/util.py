from datetime import datetime, UTC
from types import ModuleType
from uuid import uuid4


def get_uuid():
    return uuid4()


def get_datetime():
    return datetime.now(UTC)


def import_modules(package: ModuleType):
    import importlib
    import pkgutil

    for module_info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        importlib.import_module(module_info.name)
