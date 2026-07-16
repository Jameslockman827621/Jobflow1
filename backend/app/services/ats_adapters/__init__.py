"""Per-ATS apply adapters with real selectors verified against live boards."""

from .base import AdapterResult, BaseATSAdapter, get_adapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .ashby import AshbyAdapter
from .workday import WorkdayAdapter
from .generic import GenericAdapter

__all__ = [
    "AdapterResult",
    "BaseATSAdapter",
    "get_adapter",
    "GreenhouseAdapter",
    "LeverAdapter",
    "AshbyAdapter",
    "WorkdayAdapter",
    "GenericAdapter",
]
