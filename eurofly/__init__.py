"""Eurofly Traffic - Library for interacting with Eurofly traffic data."""

from .client import EuroflyClient
from .models import Flight, Pilot, PilotProfile, EuroflyTraffic
from .constants import COUNTRIES, COUNTRY_NAME_TO_ID, RANKS, FLIGHT_TYPES, FLIGHT_TYPE_TO_CODE

__version__ = "0.2.0"

__all__ = [
    "EuroflyClient",
    "Flight",
    "Pilot",
    "PilotProfile",
    "EuroflyTraffic",
    "COUNTRIES",
    "COUNTRY_NAME_TO_ID",
    "RANKS",
    "FLIGHT_TYPES",
    "FLIGHT_TYPE_TO_CODE",
]
