# Eurofly Traffic MCP Server (Go)

An MCP (Model Context Protocol) server that exposes all Eurofly Traffic library capabilities. Written in idiomatic Go.

## Features

### Traffic Monitoring
- Real-time traffic data fetching
- Pilot filtering by name, status, and location
- Detailed pilot profiles
- Flight status tracking

### Traffic Comparison
- Save traffic snapshots for later analysis
- Compare snapshots to detect changes
- Monitor pilot status changes over time
- Track position updates

### Filtering Capabilities

The library includes powerful filtering methods:

```go
import (
    "context"
    "github.com/denizsincar29/eurofly_traffic/pkg/eurofly"
)

client := eurofly.NewClient("")
traffic, _ := client.GetTraffic(context.Background())

// Filter by status
standing := traffic.FilterByStatus("Standing")
inAir := traffic.FilterByStatus("In air")

// Filter by name/callsign/location
pilots := traffic.FilterByName("Deniz")
pilots = traffic.FilterByCallsign("SK903")
pilots = traffic.FilterByLocation("Murmansk")
```

### Caching & Comparison

```go
// Save snapshot
traffic.ToCache("snapshot1.json")

// Load snapshot
oldTraffic, _ := eurofly.FromCache("snapshot1.json")

// Get current traffic for comparison
newTraffic, _ := client.GetTraffic(context.Background())

// Compare snapshots (implement compare method if needed)
```

## MCP Server Setup

### Installation

```bash
# Build from source
go build -o eurofly-mcp-server ./cmd/eurofly-mcp-server

# Or install to $GOPATH/bin
go install ./cmd/eurofly-mcp-server
```

### Running the Server

```bash
# Run the server
./eurofly-mcp-server

# Or if installed to $GOPATH/bin
eurofly-mcp-server
```

### Available MCP Tools

#### Traffic & Pilots
1. **get_traffic()** - Get current traffic summary
2. **get_all_pilots()** - List all online pilots with details
3. **filter_pilots_by_status(status)** - Filter by flight status
4. **filter_pilots_by_name(name)** - Search pilots by name
5. **filter_pilots_by_location(location)** - Search by location
6. **get_pilot_info(pilot_name)** - Get detailed pilot information
7. **search_pilots(query)** - Search pilot database
8. **get_pilot_profile(pilot_id)** - Get profile by ID

#### Airplanes
9. **get_all_airplanes(sort_by)** - List all 121 private airplanes
10. **find_airplanes_by_passengers(min, max)** - Filter by passenger capacity
11. **find_airplanes_by_price(max_price)** - Find affordable airplanes
12. **find_airplanes_by_category(category)** - Filter by category (1-7)
13. **find_smallest_runway_airplane()** - Find planes for small runways

#### Airports
14. **get_airports(country_id, category)** - List airports (2404 total)
15. **find_airports_with_runways(min_runways, country_id, category)** - Filter by runway count
16. **find_airports_by_elevation(max_elevation, country_id, category)** - Filter by elevation

#### Snapshots
17. **save_traffic_snapshot(filename)** - Save current traffic to cache
18. **compare_traffic_snapshots(old_filename, new_filename)** - Compare snapshots
19. **list_cache_snapshots()** - List saved snapshots

### Example Queries for LLMs

With the MCP server running, you can now ask LLM models (Gemini, Claude, etc.) natural language questions:

**Airplane Queries:**
- "What airplane requires the smallest runway?"
- "Find me affordable airplanes under $500,000"
- "Show me large airplanes with 200+ passengers"
- "What are the fastest airplanes?"
- "Find small planes for 5 passengers"

**Airport Queries:**
- "Show me airports in Russia with runways"
- "Find low-elevation airports below 200 meters"
- "List airports in category 1"
- "Which airports are suitable for small planes?"

**Traffic Queries:**
- "Who is currently flying?"
- "Show me all pilots taking off right now"
- "Find pilots at Murmansk airport"
- "Is Deniz Sincar online?"

### Example Usage with MCP Client

```python
# Example: Monitor a specific pilot every minute
import time
from mcp import Client

client = Client()

# Initial snapshot
client.save_traffic_snapshot("initial.json")

while True:
    time.sleep(60)  # Wait 1 minute
    
    # Compare with current
    diff = client.compare_traffic_snapshots("initial.json")
    
    # Check if Deniz Sincar changed position
    # ... process diff ...
    
    # Update snapshot
    client.save_traffic_snapshot("initial.json")
```

## Use Cases

### 1. Monitor Specific Pilot
```python
# Track Deniz Sincar's flight progress
traffic1 = client.get_traffic()
deniz1 = traffic1.filter_by_name("Deniz Sincar")[0]

# Wait some time
time.sleep(60)

traffic2 = client.get_traffic()
deniz2 = traffic2.filter_by_name("Deniz Sincar")[0]

if deniz1.flight.last_position != deniz2.flight.last_position:
    print(f"Position changed: {deniz1.flight.last_position} → {deniz2.flight.last_position}")
```

### 2. Track Airport Activity
```python
# Monitor all pilots at a specific airport
pilots = traffic.filter_by_location("Murmansk")
print(f"{len(pilots)} pilots at Murmansk")

for pilot in pilots:
    print(f"  {pilot.name}: {pilot.flight.status}")
```

### 3. Flight Status Monitoring
```python
# Get all pilots currently taking off
taking_off = traffic.filter_taking_off()

for pilot in taking_off:
    print(f"{pilot.name} taking off from {pilot.flight.location_from}")
```

### 4. En Route Tracking
```python
# Find pilots currently en route (between departure and destination)
en_route = traffic.filter_en_route()

for pilot in en_route:
    print(f"{pilot.name}: {pilot.flight.location_from} → {pilot.flight.location_to}")
    print(f"  Currently at: {pilot.flight.last_position}")
```

## Cache Directory

Traffic snapshots are saved to `~/.eurofly_cache/` by default.

## API Changes (v0.3.0)

### New Model Fields
- `EuroflyTraffic.timestamp` - Timestamp when traffic was fetched

### New Methods on EuroflyTraffic
- `all_pilots` - Property returning all pilots
- `filter_by_status(status)` - Filter by flight status
- `filter_standing()` - Get standing pilots
- `filter_rolling()` - Get rolling pilots
- `filter_taking_off()` - Get pilots taking off
- `filter_in_air()` - Get pilots in air
- `filter_on_ground()` - Get pilots on ground
- `filter_at_departure()` - Get pilots at departure airport
- `filter_at_destination()` - Get pilots at destination
- `filter_en_route()` - Get pilots between airports
- `filter_by_name(name)` - Filter by pilot name
- `filter_by_callsign(callsign)` - Filter by callsign
- `filter_by_location(location)` - Filter by any location
- `get_pilot_by_id(pilot_id)` - Get specific pilot
- `compare(other)` - Compare with another traffic snapshot
- `to_cache(filepath)` - Save to JSON file
- `from_cache(filepath)` - Load from JSON file (class method)

## License

Same as eurofly-traffic library.
