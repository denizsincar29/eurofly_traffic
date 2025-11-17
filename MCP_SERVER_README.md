# Eurofly Traffic MCP Server

An MCP (Model Context Protocol) server that exposes all Eurofly Traffic library capabilities.

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

The library now includes powerful filtering methods:

```python
from eurofly import EuroflyClient

client = EuroflyClient()
traffic = client.get_traffic()

# Filter by status
standing = traffic.filter_standing()
rolling = traffic.filter_rolling()
taking_off = traffic.filter_taking_off()
in_air = traffic.filter_in_air()

# Filter by position
at_departure = traffic.filter_at_departure()
at_destination = traffic.filter_at_destination()
en_route = traffic.filter_en_route()

# Filter by name/callsign/location
pilots = traffic.filter_by_name("Deniz")
pilots = traffic.filter_by_callsign("SK903")
pilots = traffic.filter_by_location("Murmansk")
```

### Caching & Comparison

```python
# Save snapshot
traffic.to_cache("snapshot1.json")

# Load snapshot
from eurofly.models import EuroflyTraffic
old_traffic = EuroflyTraffic.from_cache("snapshot1.json")

# Compare with current
new_traffic = client.get_traffic()
diff = new_traffic.compare(old_traffic)

print(f"New pilots: {len(diff['new_pilots'])}")
print(f"Departed: {len(diff['departed_pilots'])}")
print(f"Changed: {len(diff['changed_pilots'])}")

# Example monitoring Deniz Sincar's status
for item in diff['changed_pilots']:
    if item['pilot'].name == "Deniz Sincar":
        print(f"Changes: {item['changes']}")
        # Output: {'last_position': {'old': 'Murmansk', 'new': 'Helsinki'}}
```

## MCP Server Setup

### Installation

```bash
pip install eurofly-traffic
```

### Running the Server

```bash
# Run using Python
python mcp_server.py

# Or use the entry point (after installation)
eurofly-mcp-server
```

### Available MCP Tools

1. **get_traffic()** - Get current traffic summary
2. **get_all_pilots()** - List all online pilots with details
3. **filter_pilots_by_status(status)** - Filter by flight status
4. **filter_pilots_by_name(name)** - Search pilots by name
5. **filter_pilots_by_location(location)** - Search by location
6. **get_pilot_info(pilot_name)** - Get detailed pilot information
7. **save_traffic_snapshot(filename)** - Save current traffic to cache
8. **compare_traffic_snapshots(old_filename, new_filename)** - Compare snapshots
9. **search_pilots(query)** - Search pilot database
10. **get_pilot_profile(pilot_id)** - Get profile by ID
11. **list_cache_snapshots()** - List saved snapshots

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
