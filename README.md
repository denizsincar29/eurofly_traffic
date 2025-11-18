# Eurofly Traffic - Python Library and CLI

A comprehensive Python library and command-line tool for interacting with Eurofly (https://eurofly.stefankiss.sk) traffic data, pilot information, airplanes, and airports.

## Features

### Library (`eurofly` package)
- **Traffic Monitoring**: Parse and filter current traffic (pilots online)
- **Pilot Profiles**: Fetch detailed pilot information including bios, stats, and rankings
- **Pilot Search**: Search pilots by name, country, rank, or advanced criteria
- **Airplanes**: Parse and filter private airplanes by passengers, price, category
- **Airports**: Parse and filter airports by country, runways, elevation, category
- **Flight Types**: Proper classification of flight types (Free, Company, Charter, etc.)

### CLI Tool (`eurofly_cli.py`)
- **Interactive Menu**: User-friendly menu-driven interface
- **Traffic Viewing**: View all pilots online, search by term, or filter by favorites
- **Pilot Search**: Search pilot database with multiple criteria
- **Favorites Management**: Add/remove favorite pilots and track when they're online
- **Pilot Watcher**: Real-time monitoring of specific pilots (15-second refresh)
- **Detailed Profiles**: View complete pilot profiles with current flight status

### MCP Server (`mcp_server.py`)
- **LLM Integration**: Expose Eurofly data through Model Context Protocol
- **19 Tools**: Traffic, pilots, airplanes, airports, and more
- **Natural Language**: Ask questions like "What airplane requires the smallest runway?"

## Installation

```bash
# Clone the repository
git clone https://github.com/denizsincar29/eurofly_traffic.git
cd eurofly_traffic

# Install dependencies
pip install httpx beautifulsoup4 pydantic

# Or with uv
uv pip install httpx beautifulsoup4 pydantic
```

## Quick Start

### Using the CLI

```bash
python3 eurofly_cli.py
```

See [CLI_README.md](CLI_README.md) for detailed CLI documentation.

### Using the Library

```python
from eurofly import EuroflyClient

# Initialize client
client = EuroflyClient()

# Get current traffic
traffic = client.get_traffic()
print(f"Pilots online: {len(traffic.all_pilots)}")

# Search for a pilot
results = client.search_pilots("John")
for pilot_id, pilot_name in results:
    print(f"{pilot_name} (ID: {pilot_id})")

# Get pilot profile
profile = client.get_pilot_profile(510)
print(f"{profile.name} - {profile.bio}")

# Get airplanes
airplanes = client.get_airplanes()
small_planes = client.filter_airplanes_by_passengers(airplanes, max_passengers=10)

# Get airports
airports = client.get_airports(country_id=151)  # Russia
with_runways = client.filter_airports_by_runway_length(airports, min_runways=1)
```

## Documentation

- [CLI Documentation](CLI_README.md) - Complete CLI usage guide
- [MCP Server Documentation](MCP_SERVER_README.md) - MCP server setup and tools

## Library API

### EuroflyClient

Main client for interacting with Eurofly:

**Traffic**
- `get_traffic()` - Get current traffic (all pilots online)

**Pilots**
- `search_pilots(name)` - Search pilots by name
- `search_pilots_by_country(country_id)` - Search by country
- `search_pilots_by_rank(rank_id)` - Search by rank
- `search_pilots_advanced(name, country, rank)` - Advanced search
- `get_pilot_profile(pilot_id, use_cache)` - Get detailed pilot profile

**Airplanes**
- `get_airplanes(sort_by)` - Get all 121 private airplanes
- `filter_airplanes_by_passengers(airplanes, min, max)` - Filter by capacity
- `filter_airplanes_by_price(airplanes, max_price)` - Filter by budget
- `filter_airplanes_by_category(airplanes, category)` - Filter by category

**Airports**
- `get_airports(country_id, category)` - Get airports (2404 total)
- `filter_airports_by_runway_length(airports, min_runways)` - Filter by runways
- `filter_airports_by_category(airports, category)` - Filter by category
- `filter_airports_by_elevation(airports, max_elevation)` - Filter by elevation

### Models

- `Pilot` - Pilot with current flight info
- `PilotProfile` - Detailed pilot profile with stats
- `Flight` - Flight information (aircraft, status, route, etc.)
- `EuroflyTraffic` - Traffic container with filtering
- `Airplane` - Airplane specifications
- `Airport` - Airport information

### Constants

- `COUNTRIES` - Country ID to name mapping
- `RANKS` - Rank ID to name mapping
- `FLIGHT_TYPES` - Flight type codes to names (FRE, COF, CHF, BCF, BTF, MAF)

## Examples

See the `examples/` directory for complete examples:
- `debug_logging_example.py` - Debug logging for traffic parsing
- `airplanes_airports_example.py` - Airplane and airport filtering

## Development

### Debug Logging

Enable debug logging to see traffic parsing details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = EuroflyClient()
traffic = client.get_traffic()
```

When a status line isn't recognized, you'll see:
```
⚠️  Status=None for Test Pilot (SK123) | Reason: Missing status line...
    All lines: ['Boeing 737 with 200 passengers', 'Awaiting clearance', ...]
    HTML: <center><h3>...
```

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit pull requests.
