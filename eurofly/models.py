"""Data models for Eurofly Traffic using Pydantic."""
from typing import Optional
from pydantic import BaseModel, Field


class Flight(BaseModel):
    """Flight information for a pilot."""
    aircraft: Optional[str] = None
    passengers: int = 0
    status: Optional[str] = None
    location_from: Optional[str] = None
    location_to: Optional[str] = None
    last_position: Optional[str] = None
    description: Optional[str] = None

    def __repr__(self):
        return (f"<Flight {self.aircraft}, {self.passengers} pax, status={self.status}, "
                f"from={self.location_from}, to={self.location_to}, last={self.last_position}>")


class PilotProfile(BaseModel):
    """Detailed profile information for a pilot."""
    pilot_id: int
    name: str
    rank: Optional[str] = None
    rank_number: Optional[int] = None
    sex: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    age: Optional[int] = None
    overall_rank: Optional[int] = None
    registered: Optional[str] = None
    last_login: Optional[str] = None
    last_flight: Optional[str] = None
    points: Optional[int] = None
    earnings: Optional[int] = None
    flights_overall: Optional[int] = None
    total_distance_km: Optional[int] = None
    total_flight_time: Optional[str] = None

    def __repr__(self):
        return f"<PilotProfile {self.name} (ID:{self.pilot_id}), Rank:{self.overall_rank}, Flights:{self.flights_overall}>"


class Pilot(BaseModel):
    """Pilot information from traffic data."""
    name: str
    callsign: str
    airline: str
    flight: Flight
    pilot_id: Optional[int] = None
    
    # Non-serializable field - will be set after creation
    model_config = {"arbitrary_types_allowed": True}
    _client: Optional[object] = None

    def set_client(self, client):
        """Set the client reference after creation."""
        self._client = client

    def get_info(self, use_cache: bool = True) -> Optional[PilotProfile]:
        """Fetch full pilot profile information using the client.
        
        Args:
            use_cache: If True, try to load from cache first. Default True.
        """
        if not self._client:
            raise ValueError("Client reference not set for this Pilot object")
        if not self.pilot_id:
            raise ValueError("Pilot ID not available for this Pilot object")
        return self._client.get_pilot_profile(self.pilot_id, use_cache=use_cache)

    def __repr__(self):
        return f"<Pilot {self.name} ({self.callsign}) - {self.airline}>"


class EuroflyTraffic(BaseModel):
    """Container for traffic data."""
    pilots_on_ground: list[Pilot] = Field(default_factory=list)
    pilots_in_air: list[Pilot] = Field(default_factory=list)

    def __repr__(self):
        return f"<EuroflyTraffic ground={len(self.pilots_on_ground)}, air={len(self.pilots_in_air)}>"
