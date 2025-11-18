"""Data models for Eurofly Traffic using Pydantic."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
import json


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
    bio: Optional[str] = None  # Pilot's bio/description
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
    """Container for traffic data with filtering and comparison capabilities."""
    pilots_on_ground: list[Pilot] = Field(default_factory=list)
    pilots_in_air: list[Pilot] = Field(default_factory=list)
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

    def __repr__(self):
        return f"<EuroflyTraffic ground={len(self.pilots_on_ground)}, air={len(self.pilots_in_air)}, timestamp={self.timestamp}>"
    
    @property
    def all_pilots(self) -> List[Pilot]:
        """Get all pilots (both on ground and in air)."""
        return self.pilots_on_ground + self.pilots_in_air
    
    def filter_by_status(self, status: str) -> List[Pilot]:
        """Filter pilots by flight status.
        
        Args:
            status: One of 'Standing', 'Rolling', 'Taking off', 'In air', 'Crashed'
            
        Returns:
            List of pilots matching the status
        """
        return [p for p in self.all_pilots if p.flight.status == status]
    
    def filter_standing(self) -> List[Pilot]:
        """Get all pilots standing at an airport."""
        return self.filter_by_status("Standing")
    
    def filter_rolling(self) -> List[Pilot]:
        """Get all pilots rolling (taxiing) at an airport."""
        return self.filter_by_status("Rolling")
    
    def filter_taking_off(self) -> List[Pilot]:
        """Get all pilots taking off."""
        return self.filter_by_status("Taking off")
    
    def filter_in_air(self) -> List[Pilot]:
        """Get all pilots in the air."""
        return self.pilots_in_air
    
    def filter_on_ground(self) -> List[Pilot]:
        """Get all pilots on the ground."""
        return self.pilots_on_ground
    
    def filter_at_departure(self) -> List[Pilot]:
        """Get pilots at their departure airport (last_position == location_from)."""
        return [
            p for p in self.all_pilots
            if p.flight.last_position and p.flight.location_from
            and p.flight.last_position == p.flight.location_from
        ]
    
    def filter_at_destination(self) -> List[Pilot]:
        """Get pilots at their destination airport (last_position == location_to)."""
        return [
            p for p in self.all_pilots
            if p.flight.last_position and p.flight.location_to
            and p.flight.last_position == p.flight.location_to
        ]
    
    def filter_en_route(self) -> List[Pilot]:
        """Get pilots en route (not at departure or destination)."""
        return [
            p for p in self.pilots_in_air
            if p.flight.last_position
            and p.flight.last_position != p.flight.location_from
            and p.flight.last_position != p.flight.location_to
        ]
    
    def filter_by_name(self, name: str) -> List[Pilot]:
        """Filter pilots by name (case-insensitive partial match)."""
        name_lower = name.lower()
        return [p for p in self.all_pilots if name_lower in p.name.lower()]
    
    def filter_by_callsign(self, callsign: str) -> List[Pilot]:
        """Filter pilots by callsign (case-insensitive partial match)."""
        callsign_lower = callsign.lower()
        return [p for p in self.all_pilots if callsign_lower in p.callsign.lower()]
    
    def filter_by_location(self, location: str) -> List[Pilot]:
        """Filter pilots by any location field (from, to, last_position)."""
        location_lower = location.lower()
        return [
            p for p in self.all_pilots
            if (p.flight.location_from and location_lower in p.flight.location_from.lower())
            or (p.flight.location_to and location_lower in p.flight.location_to.lower())
            or (p.flight.last_position and location_lower in p.flight.last_position.lower())
        ]
    
    def get_pilot_by_id(self, pilot_id: int) -> Optional[Pilot]:
        """Get a specific pilot by their ID."""
        for pilot in self.all_pilots:
            if pilot.pilot_id == pilot_id:
                return pilot
        return None
    
    def compare(self, other: "EuroflyTraffic") -> dict:
        """Compare this traffic snapshot with another and return differences.
        
        Args:
            other: Another EuroflyTraffic instance to compare with
            
        Returns:
            Dictionary containing:
            - new_pilots: Pilots present in self but not in other
            - departed_pilots: Pilots present in other but not in self
            - changed_pilots: Pilots with status/position changes
        """
        # Build pilot ID sets
        self_ids = {p.pilot_id for p in self.all_pilots if p.pilot_id}
        other_ids = {p.pilot_id for p in other.all_pilots if p.pilot_id}
        
        # Find new and departed pilots
        new_ids = self_ids - other_ids
        departed_ids = other_ids - self_ids
        common_ids = self_ids & other_ids
        
        new_pilots = [p for p in self.all_pilots if p.pilot_id in new_ids]
        departed_pilots = [p for p in other.all_pilots if p.pilot_id in departed_ids]
        
        # Find changed pilots
        changed_pilots = []
        for pilot_id in common_ids:
            self_pilot = self.get_pilot_by_id(pilot_id)
            other_pilot = other.get_pilot_by_id(pilot_id)
            
            if self_pilot and other_pilot:
                changes = {}
                
                # Check status change
                if self_pilot.flight.status != other_pilot.flight.status:
                    changes['status'] = {
                        'old': other_pilot.flight.status,
                        'new': self_pilot.flight.status
                    }
                
                # Check position change
                if self_pilot.flight.last_position != other_pilot.flight.last_position:
                    changes['last_position'] = {
                        'old': other_pilot.flight.last_position,
                        'new': self_pilot.flight.last_position
                    }
                
                # Check location_from change
                if self_pilot.flight.location_from != other_pilot.flight.location_from:
                    changes['location_from'] = {
                        'old': other_pilot.flight.location_from,
                        'new': self_pilot.flight.location_from
                    }
                
                # Check location_to change
                if self_pilot.flight.location_to != other_pilot.flight.location_to:
                    changes['location_to'] = {
                        'old': other_pilot.flight.location_to,
                        'new': self_pilot.flight.location_to
                    }
                
                if changes:
                    changed_pilots.append({
                        'pilot': self_pilot,
                        'changes': changes
                    })
        
        return {
            'new_pilots': new_pilots,
            'departed_pilots': departed_pilots,
            'changed_pilots': changed_pilots
        }
    
    def to_cache(self, filepath: str):
        """Save traffic data to a JSON cache file.
        
        Args:
            filepath: Path to save the cache file
        """
        data = self.model_dump(mode='json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    @classmethod
    def from_cache(cls, filepath: str) -> "EuroflyTraffic":
        """Load traffic data from a JSON cache file.
        
        Args:
            filepath: Path to the cache file
            
        Returns:
            EuroflyTraffic instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)


class Airplane(BaseModel):
    """Information about a private airplane in Eurofly."""
    row: int
    name: str
    category: int
    type: str
    propulsion_type: str
    engines: int
    passengers: int
    speed_kmh: int
    range_km: int
    cruising_altitude_m: int
    price: int
    qualification_price: int
    
    def __repr__(self):
        return f"<Airplane {self.name}, {self.passengers} pax, {self.speed_kmh} km/h, ${self.price}>"


class Airport(BaseModel):
    """Information about an airport in Eurofly."""
    name: str
    code: Optional[str] = None
    type: Optional[str] = None  # private, commercial, military, etc.
    country: Optional[str] = None
    region: Optional[str] = None  # e.g., "Europe", "Asia"
    category: Optional[int] = None
    difficulty: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation: Optional[int] = None
    runways: Optional[int] = None
    approach_frequency: Optional[float] = None
    runway_length: Optional[int] = None  # in meters
    
    def __repr__(self):
        return f"<Airport {self.name}, Cat:{self.category}, Runways:{self.runways}, Elevation:{self.elevation}m>"
