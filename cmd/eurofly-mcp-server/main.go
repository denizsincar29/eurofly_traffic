package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/denizsincar29/eurofly_traffic/pkg/eurofly"
)

var (
	client   *eurofly.Client
	cacheDir string
)

func init() {
	client = eurofly.NewClient("")
	homeDir, _ := os.UserHomeDir()
	cacheDir = filepath.Join(homeDir, ".eurofly_cache")
	os.MkdirAll(cacheDir, 0755)
}

// Tool represents an MCP tool
type Tool struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	InputSchema map[string]interface{} `json:"inputSchema"`
}

// ToolResult represents the result of a tool execution
type ToolResult struct {
	Content []interface{} `json:"content"`
	IsError bool          `json:"isError,omitempty"`
}

// TextContent represents text content in a tool result
type TextContent struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

func main() {
	// For now, just implement a simple stdio-based MCP server
	// In a real implementation, you'd use the MCP protocol properly

	fmt.Println("Eurofly MCP Server - Go Edition")
	fmt.Println("Available tools:")
	tools := getTools()
	for _, tool := range tools {
		fmt.Printf("  - %s: %s\n", tool.Name, tool.Description)
	}

	// Example: Run a test command
	if len(os.Args) > 1 {
		toolName := os.Args[1]
		result, err := executeTool(toolName, map[string]interface{}{})
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			os.Exit(1)
		}
		output, _ := json.MarshalIndent(result, "", "  ")
		fmt.Println(string(output))
	}
}

func getTools() []Tool {
	return []Tool{
		{
			Name:        "get_traffic",
			Description: "Fetch current traffic from Eurofly and return summary",
			InputSchema: map[string]interface{}{
				"type":       "object",
				"properties": map[string]interface{}{},
			},
		},
		{
			Name:        "get_all_pilots",
			Description: "Get list of all currently online pilots with their status",
			InputSchema: map[string]interface{}{
				"type":       "object",
				"properties": map[string]interface{}{},
			},
		},
		{
			Name:        "filter_pilots_by_status",
			Description: "Filter pilots by their flight status",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"status": map[string]interface{}{
						"type":        "string",
						"description": "Flight status (Standing, Rolling, Taking off, In air, Crashed)",
					},
				},
				"required": []string{"status"},
			},
		},
		{
			Name:        "filter_pilots_by_name",
			Description: "Search for pilots by name (case-insensitive partial match)",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"name": map[string]interface{}{
						"type":        "string",
						"description": "Name or partial name to search for",
					},
				},
				"required": []string{"name"},
			},
		},
		{
			Name:        "filter_pilots_by_location",
			Description: "Search for pilots by location",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"location": map[string]interface{}{
						"type":        "string",
						"description": "Location name or partial name",
					},
				},
				"required": []string{"location"},
			},
		},
		{
			Name:        "get_pilot_info",
			Description: "Get detailed information about a specific pilot",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"pilot_name": map[string]interface{}{
						"type":        "string",
						"description": "Name of the pilot to look up",
					},
				},
				"required": []string{"pilot_name"},
			},
		},
		{
			Name:        "search_pilots",
			Description: "Search for pilots in the Eurofly database by name",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"query": map[string]interface{}{
						"type":        "string",
						"description": "Search query",
					},
				},
				"required": []string{"query"},
			},
		},
		{
			Name:        "get_pilot_profile",
			Description: "Get full profile for a pilot by ID",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"pilot_id": map[string]interface{}{
						"type":        "integer",
						"description": "Pilot ID",
					},
				},
				"required": []string{"pilot_id"},
			},
		},
		{
			Name:        "get_all_airplanes",
			Description: "Get all private airplanes",
			InputSchema: map[string]interface{}{
				"type":       "object",
				"properties": map[string]interface{}{},
			},
		},
		{
			Name:        "find_airplanes_by_passengers",
			Description: "Find airplanes by passenger capacity",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"min_passengers": map[string]interface{}{
						"type":        "integer",
						"description": "Minimum passengers",
					},
					"max_passengers": map[string]interface{}{
						"type":        "integer",
						"description": "Maximum passengers (optional)",
					},
				},
				"required": []string{"min_passengers"},
			},
		},
		{
			Name:        "find_airplanes_by_price",
			Description: "Find airplanes by maximum price",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"max_price": map[string]interface{}{
						"type":        "integer",
						"description": "Maximum price",
					},
				},
				"required": []string{"max_price"},
			},
		},
		{
			Name:        "find_airplanes_by_category",
			Description: "Find airplanes by category",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"category": map[string]interface{}{
						"type":        "integer",
						"description": "Category (1-7)",
					},
				},
				"required": []string{"category"},
			},
		},
		{
			Name:        "get_airports",
			Description: "Get airports, optionally filtered by country or category",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"country_id": map[string]interface{}{
						"type":        "integer",
						"description": "Country ID (optional)",
					},
					"category": map[string]interface{}{
						"type":        "integer",
						"description": "Category (optional)",
					},
				},
			},
		},
		{
			Name:        "find_airports_with_runways",
			Description: "Find airports with minimum number of runways",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"min_runways": map[string]interface{}{
						"type":        "integer",
						"description": "Minimum runways",
					},
				},
				"required": []string{"min_runways"},
			},
		},
		{
			Name:        "find_airports_by_elevation",
			Description: "Find airports by maximum elevation",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"max_elevation": map[string]interface{}{
						"type":        "integer",
						"description": "Maximum elevation in meters",
					},
				},
				"required": []string{"max_elevation"},
			},
		},
		{
			Name:        "save_traffic_snapshot",
			Description: "Save current traffic to a cache file",
			InputSchema: map[string]interface{}{
				"type": "object",
				"properties": map[string]interface{}{
					"filename": map[string]interface{}{
						"type":        "string",
						"description": "Filename (optional)",
					},
				},
			},
		},
		{
			Name:        "list_cache_snapshots",
			Description: "List all saved traffic snapshots",
			InputSchema: map[string]interface{}{
				"type":       "object",
				"properties": map[string]interface{}{},
			},
		},
	}
}

func executeTool(name string, params map[string]interface{}) (*ToolResult, error) {
	ctx := context.Background()

	switch name {
	case "get_traffic":
		return getTrafficTool(ctx)
	case "get_all_pilots":
		return getAllPilotsTool(ctx)
	case "filter_pilots_by_status":
		status, _ := params["status"].(string)
		return filterPilotsByStatusTool(ctx, status)
	case "filter_pilots_by_name":
		name, _ := params["name"].(string)
		return filterPilotsByNameTool(ctx, name)
	case "filter_pilots_by_location":
		location, _ := params["location"].(string)
		return filterPilotsByLocationTool(ctx, location)
	case "get_pilot_info":
		pilotName, _ := params["pilot_name"].(string)
		return getPilotInfoTool(ctx, pilotName)
	case "search_pilots":
		query, _ := params["query"].(string)
		return searchPilotsTool(ctx, query)
	case "get_pilot_profile":
		pilotID, _ := params["pilot_id"].(float64)
		return getPilotProfileTool(ctx, int(pilotID))
	case "get_all_airplanes":
		return getAllAirplanesTool(ctx)
	case "find_airplanes_by_passengers":
		minPax, _ := params["min_passengers"].(float64)
		maxPax, hasMax := params["max_passengers"].(float64)
		var maxPtr *int
		if hasMax {
			maxInt := int(maxPax)
			maxPtr = &maxInt
		}
		return findAirplanesByPassengersTool(ctx, int(minPax), maxPtr)
	case "find_airplanes_by_price":
		maxPrice, _ := params["max_price"].(float64)
		return findAirplanesByPriceTool(ctx, int(maxPrice))
	case "find_airplanes_by_category":
		category, _ := params["category"].(float64)
		return findAirplanesByCategoryTool(ctx, int(category))
	case "get_airports":
		countryID, hasCountry := params["country_id"].(float64)
		category, hasCat := params["category"].(float64)
		var countryPtr *int
		var catPtr *int
		if hasCountry {
			cid := int(countryID)
			countryPtr = &cid
		}
		if hasCat {
			cat := int(category)
			catPtr = &cat
		}
		return getAirportsTool(ctx, countryPtr, catPtr)
	case "find_airports_with_runways":
		minRunways, _ := params["min_runways"].(float64)
		return findAirportsWithRunwaysTool(ctx, int(minRunways))
	case "find_airports_by_elevation":
		maxElev, _ := params["max_elevation"].(float64)
		return findAirportsByElevationTool(ctx, int(maxElev))
	case "save_traffic_snapshot":
		filename, _ := params["filename"].(string)
		return saveTrafficSnapshotTool(ctx, filename)
	case "list_cache_snapshots":
		return listCacheSnapshotsTool()
	default:
		return nil, fmt.Errorf("unknown tool: %s", name)
	}
}

func getTrafficTool(ctx context.Context) (*ToolResult, error) {
	traffic, err := client.GetTraffic(ctx)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	text := fmt.Sprintf("Traffic at %s\n", traffic.Timestamp.Format(time.RFC3339))
	text += fmt.Sprintf("Total pilots: %d\n", len(traffic.AllPilots()))
	text += fmt.Sprintf("  - On ground: %d\n", len(traffic.PilotsOnGround))
	text += fmt.Sprintf("  - In air: %d\n", len(traffic.PilotsInAir))

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: text}}}, nil
}

func getAllPilotsTool(ctx context.Context) (*ToolResult, error) {
	traffic, err := client.GetTraffic(ctx)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	var result strings.Builder
	result.WriteString(fmt.Sprintf("All Pilots (%d online)\n", len(traffic.AllPilots())))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, pilot := range traffic.AllPilots() {
		result.WriteString(fmt.Sprintf("%s (%s) - %s (%s)\n", pilot.Name, pilot.Callsign,
			pilot.GetFlightTypeName(), pilot.FlightType))
		if pilot.Flight.Description != nil {
			result.WriteString(fmt.Sprintf("  Description: %s\n", *pilot.Flight.Description))
		}
		status := "Unknown"
		if pilot.Flight.Status != nil {
			status = *pilot.Flight.Status
		}
		result.WriteString(fmt.Sprintf("  Status: %s\n", status))
		if pilot.Flight.Aircraft != nil {
			result.WriteString(fmt.Sprintf("  Aircraft: %s\n", *pilot.Flight.Aircraft))
		}
		if pilot.Flight.LocationFrom != nil {
			result.WriteString(fmt.Sprintf("  From: %s\n", *pilot.Flight.LocationFrom))
		}
		if pilot.Flight.LocationTo != nil {
			result.WriteString(fmt.Sprintf("  To: %s\n", *pilot.Flight.LocationTo))
		}
		if pilot.Flight.LastPosition != nil {
			result.WriteString(fmt.Sprintf("  Last Position: %s\n", *pilot.Flight.LastPosition))
		}
		result.WriteString("\n")
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func filterPilotsByStatusTool(ctx context.Context, status string) (*ToolResult, error) {
	traffic, err := client.GetTraffic(ctx)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	pilots := traffic.FilterByStatus(status)
	var result strings.Builder
	result.WriteString(fmt.Sprintf("Pilots with status '%s' (%d found)\n", status, len(pilots)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, pilot := range pilots {
		result.WriteString(fmt.Sprintf("%s (%s)\n", pilot.Name, pilot.Callsign))
		if pilot.Flight.LocationFrom != nil {
			result.WriteString(fmt.Sprintf("  At: %s\n", *pilot.Flight.LocationFrom))
		}
		result.WriteString("\n")
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func filterPilotsByNameTool(ctx context.Context, name string) (*ToolResult, error) {
	traffic, err := client.GetTraffic(ctx)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	pilots := traffic.FilterByName(name)
	var result strings.Builder
	result.WriteString(fmt.Sprintf("Pilots matching '%s' (%d found)\n", name, len(pilots)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, pilot := range pilots {
		result.WriteString(fmt.Sprintf("%s (%s) - %s\n", pilot.Name, pilot.Callsign, pilot.GetFlightTypeName()))
		if pilot.Flight.Status != nil {
			result.WriteString(fmt.Sprintf("  Status: %s\n", *pilot.Flight.Status))
		}
		result.WriteString("\n")
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func filterPilotsByLocationTool(ctx context.Context, location string) (*ToolResult, error) {
	traffic, err := client.GetTraffic(ctx)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	pilots := traffic.FilterByLocation(location)
	var result strings.Builder
	result.WriteString(fmt.Sprintf("Pilots related to '%s' (%d found)\n", location, len(pilots)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, pilot := range pilots {
		result.WriteString(fmt.Sprintf("%s (%s)\n", pilot.Name, pilot.Callsign))
		if pilot.Flight.LocationFrom != nil {
			result.WriteString(fmt.Sprintf("  From: %s\n", *pilot.Flight.LocationFrom))
		}
		if pilot.Flight.LocationTo != nil {
			result.WriteString(fmt.Sprintf("  To: %s\n", *pilot.Flight.LocationTo))
		}
		result.WriteString("\n")
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func getPilotInfoTool(ctx context.Context, pilotName string) (*ToolResult, error) {
	traffic, err := client.GetTraffic(ctx)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	pilots := traffic.FilterByName(pilotName)
	if len(pilots) == 0 {
		return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: fmt.Sprintf("No pilot found with name '%s'", pilotName)}}}, nil
	}

	pilot := pilots[0]
	var result strings.Builder
	result.WriteString(fmt.Sprintf("Pilot Information: %s\n", pilot.Name))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")
	result.WriteString(fmt.Sprintf("Callsign: %s\n", pilot.Callsign))
	result.WriteString(fmt.Sprintf("Flight Type: %s (%s)\n", pilot.GetFlightTypeName(), pilot.FlightType))

	// Try to get full profile
	if pilot.PilotID != nil {
		profile, err := client.GetPilotProfile(*pilot.PilotID, true)
		if err == nil {
			result.WriteString("\nProfile Statistics:\n")
			if profile.Rank != nil {
				result.WriteString(fmt.Sprintf("  Rank: %s\n", *profile.Rank))
			}
			if profile.OverallRank != nil {
				result.WriteString(fmt.Sprintf("  Overall Rank: %d\n", *profile.OverallRank))
			}
			if profile.FlightsOverall != nil {
				result.WriteString(fmt.Sprintf("  Total Flights: %d\n", *profile.FlightsOverall))
			}
			if profile.TotalDistanceKm != nil {
				result.WriteString(fmt.Sprintf("  Total Distance: %d km\n", *profile.TotalDistanceKm))
			}
		}
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func searchPilotsTool(ctx context.Context, query string) (*ToolResult, error) {
	results, err := client.SearchPilots(ctx, query)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	var result strings.Builder
	result.WriteString(fmt.Sprintf("Search results for '%s' (%d found)\n", query, len(results)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for i, r := range results {
		if i >= 50 {
			result.WriteString(fmt.Sprintf("\n... and %d more pilots\n", len(results)-50))
			break
		}
		result.WriteString(fmt.Sprintf("%d. %s (ID: %d)\n", i+1, r.Name, r.ID))
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func getPilotProfileTool(ctx context.Context, pilotID int) (*ToolResult, error) {
	profile, err := client.GetPilotProfile(pilotID, true)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	var result strings.Builder
	result.WriteString(fmt.Sprintf("Pilot Profile: %s (ID: %d)\n", profile.Name, profile.PilotID))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	if profile.Bio != nil {
		result.WriteString(fmt.Sprintf("Bio: %s\n\n", *profile.Bio))
	}

	if profile.Rank != nil {
		result.WriteString(fmt.Sprintf("Rank: %s\n", *profile.Rank))
	}
	if profile.Country != nil {
		result.WriteString(fmt.Sprintf("Country: %s\n", *profile.Country))
	}
	if profile.FlightsOverall != nil {
		result.WriteString(fmt.Sprintf("Flights: %d\n", *profile.FlightsOverall))
	}
	if profile.TotalDistanceKm != nil {
		result.WriteString(fmt.Sprintf("Distance: %d km\n", *profile.TotalDistanceKm))
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func getAllAirplanesTool(ctx context.Context) (*ToolResult, error) {
	airplanes, err := client.GetAirplanes(ctx, nil)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	var result strings.Builder
	result.WriteString(fmt.Sprintf("All Airplanes (%d total)\n", len(airplanes)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, a := range airplanes {
		result.WriteString(fmt.Sprintf("%d. %s - Passengers: %d, Price: $%d\n",
			a.Row, a.Name, a.Passengers, a.Price))
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func findAirplanesByPassengersTool(ctx context.Context, minPax int, maxPax *int) (*ToolResult, error) {
	airplanes, err := client.GetAirplanes(ctx, nil)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	filtered := eurofly.FilterAirplanesByPassengers(airplanes, minPax, maxPax)

	var result strings.Builder
	result.WriteString(fmt.Sprintf("Airplanes with %d", minPax))
	if maxPax != nil {
		result.WriteString(fmt.Sprintf("-%d", *maxPax))
	} else {
		result.WriteString("+")
	}
	result.WriteString(fmt.Sprintf(" passengers (%d found)\n", len(filtered)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, a := range filtered {
		result.WriteString(fmt.Sprintf("%s - %d passengers, $%d\n", a.Name, a.Passengers, a.Price))
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func findAirplanesByPriceTool(ctx context.Context, maxPrice int) (*ToolResult, error) {
	airplanes, err := client.GetAirplanes(ctx, nil)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	filtered := eurofly.FilterAirplanesByPrice(airplanes, maxPrice)

	var result strings.Builder
	result.WriteString(fmt.Sprintf("Airplanes under $%d (%d found)\n", maxPrice, len(filtered)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, a := range filtered {
		result.WriteString(fmt.Sprintf("%s - $%d\n", a.Name, a.Price))
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func findAirplanesByCategoryTool(ctx context.Context, category int) (*ToolResult, error) {
	airplanes, err := client.GetAirplanes(ctx, nil)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	filtered := eurofly.FilterAirplanesByCategory(airplanes, category)

	var result strings.Builder
	result.WriteString(fmt.Sprintf("Airplanes in category %d (%d found)\n", category, len(filtered)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, a := range filtered {
		result.WriteString(fmt.Sprintf("%s - %d passengers\n", a.Name, a.Passengers))
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func getAirportsTool(ctx context.Context, countryID *int, category *int) (*ToolResult, error) {
	airports, err := client.GetAirports(ctx, countryID, category)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	var result strings.Builder
	result.WriteString(fmt.Sprintf("Airports (%d found)\n", len(airports)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	limit := 50
	if len(airports) < limit {
		limit = len(airports)
	}

	for i := 0; i < limit; i++ {
		a := airports[i]
		result.WriteString(a.Name)
		if a.Code != nil {
			result.WriteString(fmt.Sprintf(" - %s", *a.Code))
		}
		if a.Country != nil {
			result.WriteString(fmt.Sprintf(" (%s)", *a.Country))
		}
		result.WriteString("\n")
	}

	if len(airports) > limit {
		result.WriteString(fmt.Sprintf("\n... and %d more airports\n", len(airports)-limit))
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func findAirportsWithRunwaysTool(ctx context.Context, minRunways int) (*ToolResult, error) {
	airports, err := client.GetAirports(ctx, nil, nil)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	filtered := eurofly.FilterAirportsByRunwayLength(airports, minRunways)

	var result strings.Builder
	result.WriteString(fmt.Sprintf("Airports with %d+ runways (%d found)\n", minRunways, len(filtered)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, a := range filtered {
		result.WriteString(fmt.Sprintf("%s - %d runways\n", a.Name, *a.Runways))
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func findAirportsByElevationTool(ctx context.Context, maxElev int) (*ToolResult, error) {
	airports, err := client.GetAirports(ctx, nil, nil)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	filtered := eurofly.FilterAirportsByElevation(airports, maxElev)

	var result strings.Builder
	result.WriteString(fmt.Sprintf("Airports under %dm elevation (%d found)\n", maxElev, len(filtered)))
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	for _, a := range filtered {
		result.WriteString(fmt.Sprintf("%s - %dm\n", a.Name, *a.Elevation))
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}

func saveTrafficSnapshotTool(ctx context.Context, filename string) (*ToolResult, error) {
	traffic, err := client.GetTraffic(ctx)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	if filename == "" {
		filename = fmt.Sprintf("traffic_%s.json", traffic.Timestamp.Format("20060102_150405"))
	}

	filepath := filepath.Join(cacheDir, filename)
	if err := traffic.ToCache(filepath); err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	text := fmt.Sprintf("Traffic snapshot saved to %s\n%d pilots saved.", filepath, len(traffic.AllPilots()))
	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: text}}}, nil
}

func listCacheSnapshotsTool() (*ToolResult, error) {
	files, err := os.ReadDir(cacheDir)
	if err != nil {
		return &ToolResult{IsError: true, Content: []interface{}{TextContent{Type: "text", Text: err.Error()}}}, err
	}

	var result strings.Builder
	result.WriteString("Saved Traffic Snapshots\n")
	result.WriteString(strings.Repeat("=", 80) + "\n\n")

	jsonFiles := 0
	for _, file := range files {
		if !file.IsDir() && strings.HasSuffix(file.Name(), ".json") && strings.HasPrefix(file.Name(), "traffic_") {
			info, _ := file.Info()
			result.WriteString(fmt.Sprintf("%s - %s\n", file.Name(), info.ModTime().Format(time.RFC3339)))
			jsonFiles++
		}
	}

	if jsonFiles == 0 {
		result.WriteString("No snapshots found\n")
	}

	return &ToolResult{Content: []interface{}{TextContent{Type: "text", Text: result.String()}}}, nil
}
