"""Per-ATS apply adapters with real selectors verified against live boards."""

from .base import AdapterResult, BaseATSAdapter, get_adapter
from .greenhouse import GreenhouseAdapter
from .lever import LeverAdapter
from .ashby import AshbyAdapter
from .workday import WorkdayAdapter
from .workable import WorkableAdapter
from .smartrecruiters import SmartRecruitersAdapter
from .icims import IcimsAdapter
from .linkedin import LinkedInAdapter
from .indeed import IndeedAdapter
from .generic import GenericAdapter

__all__ = [
    "AdapterResult",
    "BaseATSAdapter",
    "get_adapter",
    "GreenhouseAdapter",
    "LeverAdapter",
    "AshbyAdapter",
    "WorkdayAdapter",
    "WorkableAdapter",
    "SmartRecruitersAdapter",
    "IcimsAdapter",
    "LinkedInAdapter",
    "IndeedAdapter",
    "GenericAdapter",
]
