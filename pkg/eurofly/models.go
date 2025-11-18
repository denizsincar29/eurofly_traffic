// Package eurofly provides types and functions for interacting with Eurofly traffic data.
package eurofly

import (
	"encoding/json"
	"os"
	"strings"
	"time"
)

// Flight represents flight information for a pilot.
type Flight struct {
	Aircraft     *string `json:"aircraft,omitempty"`
	Passengers   int     `json:"passengers"`
	Status       *string `json:"status,omitempty"`
	LocationFrom *string `json:"location_from,omitempty"`
	LocationTo   *string `json:"location_to,omitempty"`
	LastPosition *string `json:"last_position,omitempty"`
	Description  *string `json:"description,omitempty"`
}

// Pilot represents a pilot from traffic data.
type Pilot struct {
	Name       string  `json:"name"`
	Callsign   string  `json:"callsign"`
	FlightType string  `json:"flight_type"`
	Flight     Flight  `json:"flight"`
	PilotID    *int    `json:"pilot_id,omitempty"`
	client     *Client // Not exported, not serialized
}

// SetClient sets the client reference for this pilot.
func (p *Pilot) SetClient(client *Client) {
	p.client = client
}

// GetInfo fetches the full pilot profile information.
func (p *Pilot) GetInfo(useCache bool) (*PilotProfile, error) {
	if p.client == nil {
		return nil, ErrClientNotSet
	}
	if p.PilotID == nil {
		return nil, ErrPilotIDNotAvailable
	}
	return p.client.GetPilotProfile(*p.PilotID, useCache)
}

// GetFlightTypeName returns the full name of the flight type.
func (p *Pilot) GetFlightTypeName() string {
	if name, ok := FlightTypes[strings.ToUpper(p.FlightType)]; ok {
		return name
	}
	return p.FlightType
}

// PilotProfile represents detailed profile information for a pilot.
type PilotProfile struct {
	PilotID         int     `json:"pilot_id"`
	Name            string  `json:"name"`
	Bio             *string `json:"bio,omitempty"`
	Rank            *string `json:"rank,omitempty"`
	RankNumber      *int    `json:"rank_number,omitempty"`
	Sex             *string `json:"sex,omitempty"`
	Country         *string `json:"country,omitempty"`
	Language        *string `json:"language,omitempty"`
	Age             *int    `json:"age,omitempty"`
	OverallRank     *int    `json:"overall_rank,omitempty"`
	Registered      *string `json:"registered,omitempty"`
	LastLogin       *string `json:"last_login,omitempty"`
	LastFlight      *string `json:"last_flight,omitempty"`
	Points          *int    `json:"points,omitempty"`
	Earnings        *int    `json:"earnings,omitempty"`
	FlightsOverall  *int    `json:"flights_overall,omitempty"`
	TotalDistanceKm *int    `json:"total_distance_km,omitempty"`
	TotalFlightTime *string `json:"total_flight_time,omitempty"`
}

// Traffic represents a container for traffic data with filtering capabilities.
type Traffic struct {
	PilotsOnGround []Pilot    `json:"pilots_on_ground"`
	PilotsInAir    []Pilot    `json:"pilots_in_air"`
	Timestamp      *time.Time `json:"timestamp,omitempty"`
}

// NewTraffic creates a new Traffic instance with the current timestamp.
func NewTraffic() *Traffic {
	now := time.Now()
	return &Traffic{
		PilotsOnGround: make([]Pilot, 0),
		PilotsInAir:    make([]Pilot, 0),
		Timestamp:      &now,
	}
}

// AllPilots returns all pilots (both on ground and in air).
func (t *Traffic) AllPilots() []Pilot {
	all := make([]Pilot, 0, len(t.PilotsOnGround)+len(t.PilotsInAir))
	all = append(all, t.PilotsOnGround...)
	all = append(all, t.PilotsInAir...)
	return all
}

// FilterByStatus filters pilots by flight status.
func (t *Traffic) FilterByStatus(status string) []Pilot {
	var filtered []Pilot
	for _, p := range t.AllPilots() {
		if p.Flight.Status != nil && *p.Flight.Status == status {
			filtered = append(filtered, p)
		}
	}
	return filtered
}

// FilterByName filters pilots by name (case-insensitive partial match).
func (t *Traffic) FilterByName(name string) []Pilot {
	nameLower := strings.ToLower(name)
	var filtered []Pilot
	for _, p := range t.AllPilots() {
		if strings.Contains(strings.ToLower(p.Name), nameLower) {
			filtered = append(filtered, p)
		}
	}
	return filtered
}

// FilterByCallsign filters pilots by callsign (case-insensitive partial match).
func (t *Traffic) FilterByCallsign(callsign string) []Pilot {
	callsignLower := strings.ToLower(callsign)
	var filtered []Pilot
	for _, p := range t.AllPilots() {
		if strings.Contains(strings.ToLower(p.Callsign), callsignLower) {
			filtered = append(filtered, p)
		}
	}
	return filtered
}

// FilterByLocation filters pilots by any location field.
func (t *Traffic) FilterByLocation(location string) []Pilot {
	locationLower := strings.ToLower(location)
	var filtered []Pilot
	for _, p := range t.AllPilots() {
		if (p.Flight.LocationFrom != nil && strings.Contains(strings.ToLower(*p.Flight.LocationFrom), locationLower)) ||
			(p.Flight.LocationTo != nil && strings.Contains(strings.ToLower(*p.Flight.LocationTo), locationLower)) ||
			(p.Flight.LastPosition != nil && strings.Contains(strings.ToLower(*p.Flight.LastPosition), locationLower)) {
			filtered = append(filtered, p)
		}
	}
	return filtered
}

// GetPilotByID returns a pilot by their ID.
func (t *Traffic) GetPilotByID(pilotID int) *Pilot {
	for i := range t.AllPilots() {
		pilots := t.AllPilots()
		if pilots[i].PilotID != nil && *pilots[i].PilotID == pilotID {
			return &pilots[i]
		}
	}
	return nil
}

// ToCache saves traffic data to a JSON file.
func (t *Traffic) ToCache(filepath string) error {
	data, err := json.MarshalIndent(t, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath, data, 0644)
}

// FromCache loads traffic data from a JSON file.
func FromCache(filepath string) (*Traffic, error) {
	data, err := os.ReadFile(filepath)
	if err != nil {
		return nil, err
	}
	var traffic Traffic
	if err := json.Unmarshal(data, &traffic); err != nil {
		return nil, err
	}
	return &traffic, nil
}

// Airplane represents information about a private airplane.
type Airplane struct {
	Row                int    `json:"row"`
	Name               string `json:"name"`
	Category           int    `json:"category"`
	Type               string `json:"type"`
	PropulsionType     string `json:"propulsion_type"`
	Engines            int    `json:"engines"`
	Passengers         int    `json:"passengers"`
	SpeedKmh           int    `json:"speed_kmh"`
	RangeKm            int    `json:"range_km"`
	CruisingAltitudeM  int    `json:"cruising_altitude_m"`
	Price              int    `json:"price"`
	QualificationPrice int    `json:"qualification_price"`
}

// Airport represents information about an airport.
type Airport struct {
	Name              string   `json:"name"`
	Code              *string  `json:"code,omitempty"`
	Type              *string  `json:"type,omitempty"`
	Country           *string  `json:"country,omitempty"`
	Region            *string  `json:"region,omitempty"`
	Category          *int     `json:"category,omitempty"`
	Difficulty        *int     `json:"difficulty,omitempty"`
	Latitude          *float64 `json:"latitude,omitempty"`
	Longitude         *float64 `json:"longitude,omitempty"`
	Elevation         *int     `json:"elevation,omitempty"`
	Runways           *int     `json:"runways,omitempty"`
	ApproachFrequency *float64 `json:"approach_frequency,omitempty"`
	RunwayLength      *int     `json:"runway_length,omitempty"`
}
