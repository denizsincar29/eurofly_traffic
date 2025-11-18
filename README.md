# Eurofly Traffic - Go Library and CLI

A comprehensive Go library with command-line interface for interacting with Eurofly (https://eurofly.stefankiss.sk) traffic data, pilot information, airplanes, and airports.

## Features

### Library (`pkg/eurofly`)
- **Traffic Monitoring**: Parse and filter current traffic (pilots online)
- **Pilot Profiles**: Fetch detailed pilot information including bios, stats, and rankings
- **Pilot Search**: Search pilots by name, country, rank, or advanced criteria
- **Airplanes**: Parse and filter private airplanes (121 total) by passengers, price, category
- **Airports**: Parse and filter airports (2404 total) by country, runways, elevation, category
- **Flight Types**: Proper classification of flight types (Free, Company, Charter, etc.)
- **Context Support**: All HTTP operations support context for cancellation and timeout
- **Type Safety**: Strongly typed models with proper JSON serialization

### CLI Tool (`eurofly-cli`)
- **Interactive Menu**: User-friendly menu-driven interface
- **Traffic Viewing**: View all pilots online, search by term, or filter by favorites
- **Pilot Search**: Search pilot database with multiple criteria
- **Favorites Management**: Add/remove favorite pilots and track when they're online
- **Pilot Watcher**: Real-time monitoring of specific pilots (15-second refresh), accepts name or ID
- **Detailed Profiles**: View complete pilot profiles with current flight status
- **Airplane Search**: Browse and filter 121 airplanes by passengers, price, category
- **Airport Search**: Browse and filter 2404 airports by country, runways, elevation, category

### MCP Server (`eurofly-mcp-server`)
- **LLM Integration**: Expose Eurofly data through Model Context Protocol
- **17 Tools**: Traffic, pilots, airplanes, airports, and more
- **Natural Language**: Ask questions like "What airplane requires the smallest runway?"

## Installation

```bash
# Clone the repository
git clone https://github.com/denizsincar29/eurofly_traffic.git
cd eurofly_traffic

# Build the binaries
go build -o eurofly-cli ./cmd/eurofly-cli
go build -o eurofly-mcp-server ./cmd/eurofly-mcp-server

# Or install to $GOPATH/bin
go install ./cmd/eurofly-cli
go install ./cmd/eurofly-mcp-server
```

## Quick Start

### Using the CLI

```bash
./eurofly-cli
```

See [CLI_README.md](CLI_README.md) for detailed CLI documentation.

### Using the Library

```go
package main

import (
    "context"
    "fmt"
    "github.com/denizsincar29/eurofly_traffic/pkg/eurofly"
)

func main() {
    // Initialize client
    client := eurofly.NewClient("")
    ctx := context.Background()
    
    // Get current traffic
    traffic, err := client.GetTraffic(ctx)
    if err != nil {
        panic(err)
    }
    fmt.Printf("Pilots online: %d\n", len(traffic.AllPilots()))
    
    // Search for a pilot
    results, err := client.SearchPilots(ctx, "John")
    if err != nil {
        panic(err)
    }
    for _, result := range results {
        fmt.Printf("%s (ID: %d)\n", result.Name, result.ID)
    }
    
    // Get pilot profile
    profile, err := client.GetPilotProfile(510, true)
    if err != nil {
        panic(err)
    }
    fmt.Printf("%s - %s\n", profile.Name, *profile.Bio)
    
    // Get airplanes
    airplanes, err := client.GetAirplanes(ctx, nil)
    if err != nil {
        panic(err)
    }
    maxPax := 10
    smallPlanes := eurofly.FilterAirplanesByPassengers(airplanes, 1, &maxPax)
    
    // Get airports
    countryID := 151 // Russia
    airports, err := client.GetAirports(ctx, &countryID, nil)
    if err != nil {
        panic(err)
    }
    withRunways := eurofly.FilterAirportsByRunwayLength(airports, 1)
    fmt.Printf("Airports with runways: %d\n", len(withRunways))
}
```

## Documentation

- [CLI Documentation](CLI_README.md) - Complete CLI usage guide
- [MCP Server Documentation](MCP_SERVER_README.md) - MCP server setup and tools

## Library API

### Client

Main client for interacting with Eurofly:

**Traffic**
- `GetTraffic(ctx)` - Get current traffic (all pilots online)

**Pilots**
- `SearchPilots(ctx, name)` - Search pilots by name
- `SearchPilotsByCountry(ctx, country_id)` - Search by country
- `SearchPilotsByRank(ctx, rank_id)` - Search by rank
- `SearchPilotsAdvanced(ctx, name, country, rank)` - Advanced search
- `GetPilotProfile(pilot_id, use_cache)` - Get detailed pilot profile

**Airplanes**
- `GetAirplanes(ctx, sort_by)` - Get all 121 private airplanes
- `FilterAirplanesByPassengers(airplanes, min, max)` - Filter by capacity
- `FilterAirplanesByPrice(airplanes, max_price)` - Filter by budget
- `FilterAirplanesByCategory(airplanes, category)` - Filter by category

**Airports**
- `GetAirports(ctx, country_id, category)` - Get airports (2404 total)
- `FilterAirportsByRunwayLength(airports, min_runways)` - Filter by runways
- `FilterAirportsByCategory(airports, category)` - Filter by category
- `FilterAirportsByElevation(airports, max_elevation)` - Filter by elevation

### Models

- `Pilot` - Pilot with current flight info
- `PilotProfile` - Detailed pilot profile with stats
- `Flight` - Flight information (aircraft, status, route, etc.)
- `Traffic` - Traffic container with filtering methods
- `Airplane` - Airplane specifications
- `Airport` - Airport information

### Constants

- `Countries` - Country ID to name mapping
- `Ranks` - Rank ID to name mapping
- `FlightTypes` - Flight type codes to names (FRE, COF, CHF, BCF, BTF, MAF)

## Development

### Building from Source

```bash
# Build both binaries
go build -o eurofly-cli ./cmd/eurofly-cli
go build -o eurofly-mcp-server ./cmd/eurofly-mcp-server

# Run tests
go test ./pkg/eurofly/...

# Format code
go fmt ./...
```

### Debug Logging

The library logs warnings when parsing issues occur. You'll see messages like:
```
⚠️  Status=nil for Test Pilot (SK123) | Flight lines: [...]
```

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit pull requests.
