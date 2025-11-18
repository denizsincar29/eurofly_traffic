package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/denizsincar29/eurofly_traffic/pkg/eurofly"
)

const (
	favoritesFileName = ".eurofly_favorites.json"
)

// FavoritesManager manages favorite pilots.
type FavoritesManager struct {
	Favorites map[int]bool `json:"favorites"`
	filepath  string
}

// NewFavoritesManager creates a new favorites manager.
func NewFavoritesManager() *FavoritesManager {
	homeDir, _ := os.UserHomeDir()
	filepath := filepath.Join(homeDir, favoritesFileName)

	mgr := &FavoritesManager{
		Favorites: make(map[int]bool),
		filepath:  filepath,
	}
	mgr.Load()
	return mgr
}

// Load loads favorites from file.
func (fm *FavoritesManager) Load() {
	data, err := os.ReadFile(fm.filepath)
	if err != nil {
		return
	}

	var temp struct {
		Favorites []int `json:"favorites"`
	}
	if err := json.Unmarshal(data, &temp); err != nil {
		return
	}

	fm.Favorites = make(map[int]bool)
	for _, id := range temp.Favorites {
		fm.Favorites[id] = true
	}
}

// Save saves favorites to file.
func (fm *FavoritesManager) Save() error {
	var ids []int
	for id := range fm.Favorites {
		ids = append(ids, id)
	}

	data := struct {
		Favorites []int `json:"favorites"`
	}{
		Favorites: ids,
	}

	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(fm.filepath, jsonData, 0644)
}

// Add adds a pilot to favorites.
func (fm *FavoritesManager) Add(pilotID int, pilotName string) {
	fm.Favorites[pilotID] = true
	fm.Save()
	nameStr := ""
	if pilotName != "" {
		nameStr = fmt.Sprintf(" (%s)", pilotName)
	}
	fmt.Printf("✓ Added pilot ID %d%s to favorites\n", pilotID, nameStr)
}

// Remove removes a pilot from favorites.
func (fm *FavoritesManager) Remove(pilotID int) {
	if _, exists := fm.Favorites[pilotID]; exists {
		delete(fm.Favorites, pilotID)
		fm.Save()
		fmt.Printf("✓ Removed pilot ID %d from favorites\n", pilotID)
	} else {
		fmt.Printf("Pilot ID %d is not in favorites\n", pilotID)
	}
}

// IsFavorite checks if a pilot is in favorites.
func (fm *FavoritesManager) IsFavorite(pilotID int) bool {
	return fm.Favorites[pilotID]
}

// List returns all favorite pilot IDs.
func (fm *FavoritesManager) List() []int {
	var ids []int
	for id := range fm.Favorites {
		ids = append(ids, id)
	}
	return ids
}

func main() {
	client := eurofly.NewClient("")
	favMgr := NewFavoritesManager()
	scanner := bufio.NewScanner(os.Stdin)

	for {
		displayMainMenu()
		choice := readInput(scanner, "Select option: ")

		switch choice {
		case "1":
			viewTraffic(client, favMgr, scanner, false, "")
		case "2":
			search := readInput(scanner, "Enter search term: ")
			if search != "" {
				viewTraffic(client, favMgr, scanner, false, search)
			}
		case "3":
			viewTraffic(client, favMgr, scanner, true, "")
		case "4":
			searchPilotsMenu(client, favMgr, scanner)
		case "5":
			manageFavorites(client, favMgr, scanner)
		case "6":
			watchPilot(client, favMgr, scanner)
		case "7":
			browseAirplanes(client, scanner)
		case "8":
			browseAirports(client, scanner)
		case "9":
			fmt.Println("Goodbye!")
			return
		default:
			fmt.Println("Invalid option")
		}
	}
}

func displayMainMenu() {
	fmt.Println("\n" + strings.Repeat("=", 80))
	fmt.Println("EUROFLY TRAFFIC CLI")
	fmt.Println(strings.Repeat("=", 80))
	fmt.Println("\n1. View all traffic")
	fmt.Println("2. Search traffic")
	fmt.Println("3. View favorites online")
	fmt.Println("4. Search pilots")
	fmt.Println("5. Manage favorites")
	fmt.Println("6. Watch specific pilot")
	fmt.Println("7. Browse airplanes")
	fmt.Println("8. Browse airports")
	fmt.Println("9. Exit")
}

func readInput(scanner *bufio.Scanner, prompt string) string {
	fmt.Print("\n" + prompt)
	if scanner.Scan() {
		return strings.TrimSpace(scanner.Text())
	}
	return ""
}

func displayPilotDetails(pilot *eurofly.Pilot, showFavorite bool, favMgr *FavoritesManager) {
	favMarker := ""
	if showFavorite && pilot.PilotID != nil && favMgr.IsFavorite(*pilot.PilotID) {
		favMarker = " ⭐"
	}

	fmt.Printf("\n%s (%s) - %s (%s)%s\n", pilot.Name, pilot.Callsign,
		pilot.GetFlightTypeName(), pilot.FlightType, favMarker)

	if pilot.PilotID != nil {
		fmt.Printf("  Pilot ID: %d\n", *pilot.PilotID)
	}

	if pilot.Flight.Description != nil {
		fmt.Printf("  Description: %s\n", *pilot.Flight.Description)
	}

	status := "Unknown"
	if pilot.Flight.Status != nil {
		status = *pilot.Flight.Status
	}
	fmt.Printf("  Status: %s\n", status)

	if pilot.Flight.Aircraft != nil {
		fmt.Printf("  Aircraft: %s\n", *pilot.Flight.Aircraft)
	}

	if pilot.Flight.Passengers > 0 {
		fmt.Printf("  Passengers: %d\n", pilot.Flight.Passengers)
	}

	if pilot.Flight.LocationFrom != nil {
		fmt.Printf("  From: %s\n", *pilot.Flight.LocationFrom)
	}

	if pilot.Flight.LocationTo != nil {
		fmt.Printf("  To: %s\n", *pilot.Flight.LocationTo)
	}

	if pilot.Flight.LastPosition != nil {
		fmt.Printf("  Position: %s\n", *pilot.Flight.LastPosition)
	}
}

func viewTraffic(client *eurofly.Client, favMgr *FavoritesManager, scanner *bufio.Scanner, favoritesOnly bool, search string) {
	fmt.Println("\nFetching traffic...")
	traffic, err := client.GetTraffic(context.Background())
	if err != nil {
		fmt.Printf("Error fetching traffic: %v\n", err)
		return
	}

	pilotsOnGround := traffic.PilotsOnGround
	pilotsInAir := traffic.PilotsInAir

	// Filter by search term
	if search != "" {
		searchLower := strings.ToLower(search)
		pilotsOnGround = filterPilotsBySearch(pilotsOnGround, searchLower)
		pilotsInAir = filterPilotsBySearch(pilotsInAir, searchLower)
	}

	// Filter by favorites
	if favoritesOnly {
		pilotsOnGround = filterPilotsByFavorites(pilotsOnGround, favMgr)
		pilotsInAir = filterPilotsByFavorites(pilotsInAir, favMgr)
	}

	// Display header
	fmt.Println("\n" + strings.Repeat("=", 80))
	if favoritesOnly {
		fmt.Println("FAVORITE PILOTS ONLINE")
	} else if search != "" {
		fmt.Printf("TRAFFIC SEARCH: '%s'\n", search)
	} else {
		fmt.Println("ALL TRAFFIC")
	}
	fmt.Println(strings.Repeat("=", 80))

	// Display pilots on ground
	fmt.Printf("\n--- Pilots on ground (%d) ---\n", len(pilotsOnGround))
	if len(pilotsOnGround) > 0 {
		for i := range pilotsOnGround {
			displayPilotDetails(&pilotsOnGround[i], !favoritesOnly, favMgr)
		}
	} else {
		fmt.Println("None")
	}

	// Display pilots in air
	fmt.Printf("\n--- Pilots in air (%d) ---\n", len(pilotsInAir))
	if len(pilotsInAir) > 0 {
		for i := range pilotsInAir {
			displayPilotDetails(&pilotsInAir[i], !favoritesOnly, favMgr)
		}
	} else {
		fmt.Println("None")
	}

	fmt.Println("\n" + strings.Repeat("=", 80))
	fmt.Printf("Total: %d pilot(s)\n", len(pilotsOnGround)+len(pilotsInAir))
	fmt.Println(strings.Repeat("=", 80))
}

func filterPilotsBySearch(pilots []eurofly.Pilot, searchLower string) []eurofly.Pilot {
	var filtered []eurofly.Pilot
	for _, p := range pilots {
		if strings.Contains(strings.ToLower(p.Name), searchLower) ||
			strings.Contains(strings.ToLower(p.Callsign), searchLower) ||
			strings.Contains(strings.ToLower(p.FlightType), searchLower) ||
			(p.Flight.Description != nil && strings.Contains(strings.ToLower(*p.Flight.Description), searchLower)) ||
			(p.Flight.LocationFrom != nil && strings.Contains(strings.ToLower(*p.Flight.LocationFrom), searchLower)) ||
			(p.Flight.LocationTo != nil && strings.Contains(strings.ToLower(*p.Flight.LocationTo), searchLower)) ||
			(p.Flight.Aircraft != nil && strings.Contains(strings.ToLower(*p.Flight.Aircraft), searchLower)) {
			filtered = append(filtered, p)
		}
	}
	return filtered
}

func filterPilotsByFavorites(pilots []eurofly.Pilot, favMgr *FavoritesManager) []eurofly.Pilot {
	var filtered []eurofly.Pilot
	for _, p := range pilots {
		if p.PilotID != nil && favMgr.IsFavorite(*p.PilotID) {
			filtered = append(filtered, p)
		}
	}
	return filtered
}

func searchPilotsMenu(client *eurofly.Client, favMgr *FavoritesManager, scanner *bufio.Scanner) {
	fmt.Println("\n" + strings.Repeat("=", 80))
	fmt.Println("PILOT SEARCH")
	fmt.Println(strings.Repeat("=", 80))
	fmt.Println("\n1. Search by name")
	fmt.Println("2. Search by country")
	fmt.Println("3. Search by rank")
	fmt.Println("4. Advanced search")
	fmt.Println("5. Back to main menu")

	choice := readInput(scanner, "Select option: ")

	switch choice {
	case "1":
		name := readInput(scanner, "Enter pilot name to search: ")
		if name != "" {
			results, err := client.SearchPilots(context.Background(), name)
			if err != nil {
				fmt.Printf("Error: %v\n", err)
				return
			}
			displaySearchResults(client, favMgr, scanner, results, fmt.Sprintf("Search: %s", name))
		}
	case "2":
		fmt.Println("\nAvailable countries (showing first 20):")
		count := 0
		for id, name := range eurofly.Countries {
			if count >= 20 {
				break
			}
			fmt.Printf("%d. %s (ID: %d)\n", count+1, name, id)
			count++
		}
		fmt.Println("... and more")

		countryIDStr := readInput(scanner, "Enter country ID: ")
		if countryID, err := strconv.Atoi(countryIDStr); err == nil {
			countryName := eurofly.Countries[countryID]
			if countryName == "" {
				countryName = fmt.Sprintf("Country %d", countryID)
			}
			results, err := client.SearchPilotsByCountry(context.Background(), countryID)
			if err != nil {
				fmt.Printf("Error: %v\n", err)
				return
			}
			displaySearchResults(client, favMgr, scanner, results, fmt.Sprintf("Country: %s", countryName))
		}
	case "3":
		fmt.Println("\nAvailable ranks:")
		for id, name := range eurofly.Ranks {
			fmt.Printf("%d. %s\n", id, name)
		}

		rankIDStr := readInput(scanner, "Enter rank ID: ")
		if rankID, err := strconv.Atoi(rankIDStr); err == nil {
			rankName := eurofly.Ranks[rankID]
			if rankName == "" {
				rankName = fmt.Sprintf("Rank %d", rankID)
			}
			results, err := client.SearchPilotsByRank(context.Background(), rankID)
			if err != nil {
				fmt.Printf("Error: %v\n", err)
				return
			}
			displaySearchResults(client, favMgr, scanner, results, fmt.Sprintf("Rank: %s", rankName))
		}
	case "4":
		fmt.Println("\nAdvanced Search")
		name := readInput(scanner, "Name (or Enter to skip): ")
		var namePtr *string
		if name != "" {
			namePtr = &name
		}

		countryIDStr := readInput(scanner, "Country ID (or Enter to skip): ")
		var countryPtr *int
		if countryID, err := strconv.Atoi(countryIDStr); err == nil {
			countryPtr = &countryID
		}

		rankIDStr := readInput(scanner, "Rank ID (or Enter to skip): ")
		var rankPtr *int
		if rankID, err := strconv.Atoi(rankIDStr); err == nil {
			rankPtr = &rankID
		}

		results, err := client.SearchPilotsAdvanced(context.Background(), namePtr, countryPtr, rankPtr)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			return
		}
		displaySearchResults(client, favMgr, scanner, results, "Advanced search")
	}
}

func displaySearchResults(client *eurofly.Client, favMgr *FavoritesManager, scanner *bufio.Scanner,
	results []struct {
		ID   int
		Name string
	}, title string) {

	if len(results) == 0 {
		fmt.Println("\nNo pilots found")
		return
	}

	fmt.Printf("\n%s - Found %d pilot(s):\n\n", title, len(results))
	displayResults := results
	if len(results) > 50 {
		displayResults = results[:50]
	}

	for i, r := range displayResults {
		favMarker := ""
		if favMgr.IsFavorite(r.ID) {
			favMarker = " ⭐"
		}
		fmt.Printf("%d. %s (ID: %d)%s\n", i+1, r.Name, r.ID, favMarker)
	}

	if len(results) > 50 {
		fmt.Printf("\n... and %d more pilots\n", len(results)-50)
	}

	fmt.Println("\nOptions:")
	fmt.Println("  <number>     - View pilot profile")
	fmt.Println("  f <number>   - Add pilot to favorites")
	fmt.Println("  u <number>   - Remove pilot from favorites")
	fmt.Println("  Enter        - Back to menu")

	choice := readInput(scanner, "Select option: ")
	if choice == "" {
		return
	}

	parts := strings.Fields(choice)

	// Add to favorites
	if len(parts) == 2 && strings.ToLower(parts[0]) == "f" {
		if index, err := strconv.Atoi(parts[1]); err == nil && index >= 1 && index <= len(displayResults) {
			r := displayResults[index-1]
			favMgr.Add(r.ID, r.Name)
		} else {
			fmt.Println("Invalid input")
		}
		return
	}

	// Remove from favorites
	if len(parts) == 2 && strings.ToLower(parts[0]) == "u" {
		if index, err := strconv.Atoi(parts[1]); err == nil && index >= 1 && index <= len(displayResults) {
			r := displayResults[index-1]
			favMgr.Remove(r.ID)
		} else {
			fmt.Println("Invalid input")
		}
		return
	}

	// View profile
	if index, err := strconv.Atoi(choice); err == nil && index >= 1 && index <= len(displayResults) {
		r := displayResults[index-1]
		viewPilotProfile(client, favMgr, scanner, r.ID, r.Name)
	} else {
		fmt.Println("Invalid input")
	}
}

func viewPilotProfile(client *eurofly.Client, favMgr *FavoritesManager, scanner *bufio.Scanner, pilotID int, pilotName string) {
	fmt.Printf("\nFetching profile for %s...\n", pilotName)
	profile, err := client.GetPilotProfile(pilotID, false)
	if err != nil {
		fmt.Printf("Error fetching profile: %v\n", err)
		return
	}

	// Check if currently flying
	traffic, _ := client.GetTraffic(context.Background())
	var flyingPilot *eurofly.Pilot
	if traffic != nil {
		for i := range traffic.AllPilots() {
			p := &traffic.AllPilots()[i]
			if p.PilotID != nil && *p.PilotID == pilotID {
				flyingPilot = p
				break
			}
		}
	}

	// Display profile
	fmt.Println("\n" + strings.Repeat("=", 80))
	fmt.Printf("PILOT PROFILE: %s\n", profile.Name)
	isFav := favMgr.IsFavorite(pilotID)
	if isFav {
		fmt.Println("Favorite: Yes ⭐")
	} else {
		fmt.Println("Favorite: No")
	}
	fmt.Println(strings.Repeat("=", 80))

	if profile.Bio != nil {
		fmt.Printf("\n📝 Bio: %s\n", *profile.Bio)
	}

	// Show current flight if flying
	if flyingPilot != nil {
		fmt.Println("\n" + strings.Repeat("=", 80))
		fmt.Println("🛫 CURRENTLY FLYING")
		fmt.Println(strings.Repeat("=", 80))
		displayPilotDetails(flyingPilot, false, favMgr)
		fmt.Println(strings.Repeat("=", 80))
	}

	// Show profile details
	fmt.Printf("\nPilot ID: %d\n", pilotID)

	if profile.Rank != nil {
		fmt.Printf("Rank: %s", *profile.Rank)
		if profile.RankNumber != nil {
			fmt.Printf(" (#%d)", *profile.RankNumber)
		}
		fmt.Println()
	}

	if profile.OverallRank != nil {
		fmt.Printf("Overall Rank: #%d\n", *profile.OverallRank)
	}

	if profile.Sex != nil {
		fmt.Printf("Sex: %s\n", *profile.Sex)
	}

	if profile.Country != nil {
		fmt.Printf("Country: %s\n", *profile.Country)
	}

	if profile.Language != nil {
		fmt.Printf("Language: %s\n", *profile.Language)
	}

	if profile.Age != nil {
		fmt.Printf("Age: %d years old\n", *profile.Age)
	}

	if profile.Registered != nil {
		fmt.Printf("\nRegistered: %s\n", *profile.Registered)
	}

	if profile.LastLogin != nil {
		fmt.Printf("Last Login: %s\n", *profile.LastLogin)
	}

	if profile.LastFlight != nil {
		fmt.Printf("Last Flight: %s\n", *profile.LastFlight)
	}

	if profile.FlightsOverall != nil {
		fmt.Printf("\nFlights Overall: %d\n", *profile.FlightsOverall)
	}

	if profile.TotalDistanceKm != nil {
		fmt.Printf("Total Distance: %d km\n", *profile.TotalDistanceKm)
	}

	if profile.TotalFlightTime != nil {
		fmt.Printf("Total Flight Time: %s\n", *profile.TotalFlightTime)
	}

	if profile.Points != nil {
		fmt.Printf("\nPoints: %d\n", *profile.Points)
	}

	if profile.Earnings != nil {
		fmt.Printf("Earnings: $%d\n", *profile.Earnings)
	}

	fmt.Println(strings.Repeat("=", 80))

	// Options
	fmt.Println("\nOptions:")
	if isFav {
		fmt.Println("  u - Remove from favorites")
	} else {
		fmt.Println("  f - Add to favorites")
	}
	fmt.Println("  Enter - Back")

	choice := readInput(scanner, "Select option: ")

	if choice == "f" && !isFav {
		favMgr.Add(pilotID, profile.Name)
	} else if choice == "u" && isFav {
		favMgr.Remove(pilotID)
	}
}

func manageFavorites(client *eurofly.Client, favMgr *FavoritesManager, scanner *bufio.Scanner) {
	fmt.Println("\n" + strings.Repeat("=", 80))
	fmt.Println("MANAGE FAVORITES")
	fmt.Println(strings.Repeat("=", 80))

	favIDs := favMgr.List()
	if len(favIDs) == 0 {
		fmt.Println("\nNo favorites saved")
		return
	}

	fmt.Printf("\nFavorite Pilots (%d):\n", len(favIDs))
	fmt.Println(strings.Repeat("=", 80))

	// Fetch profiles for favorites
	fmt.Println("\nFetching profiles...")
	type profileInfo struct {
		ID   int
		Name string
	}
	var profiles []profileInfo
	for _, pilotID := range favIDs {
		profile, err := client.GetPilotProfile(pilotID, true)
		if err != nil {
			profiles = append(profiles, profileInfo{ID: pilotID, Name: fmt.Sprintf("Pilot %d", pilotID)})
		} else {
			profiles = append(profiles, profileInfo{ID: pilotID, Name: profile.Name})
		}
	}

	for i, p := range profiles {
		fmt.Printf("%d. %s (ID: %d)\n", i+1, p.Name, p.ID)
	}

	fmt.Println("\nOptions:")
	fmt.Println("  <number> - View pilot profile")
	fmt.Println("  u <number> - Remove from favorites")
	fmt.Println("  Enter - Back")

	choice := readInput(scanner, "Select option: ")
	if choice == "" {
		return
	}

	parts := strings.Fields(choice)

	// Remove from favorites
	if len(parts) == 2 && strings.ToLower(parts[0]) == "u" {
		if index, err := strconv.Atoi(parts[1]); err == nil && index >= 1 && index <= len(profiles) {
			p := profiles[index-1]
			favMgr.Remove(p.ID)
		} else {
			fmt.Println("Invalid input")
		}
		return
	}

	// View profile
	if index, err := strconv.Atoi(choice); err == nil && index >= 1 && index <= len(profiles) {
		p := profiles[index-1]
		viewPilotProfile(client, favMgr, scanner, p.ID, p.Name)
	} else {
		fmt.Println("Invalid input")
	}
}

func watchPilot(client *eurofly.Client, favMgr *FavoritesManager, scanner *bufio.Scanner) {
	pilotInput := readInput(scanner, "Enter pilot name or ID to watch: ")
	if pilotInput == "" {
		fmt.Println("No input provided")
		return
	}

	var pilotID int
	var pilotName string

	// Check if input is a digit (ID)
	if id, err := strconv.Atoi(pilotInput); err == nil {
		pilotID = id
		// Get pilot name from profile
		profile, err := client.GetPilotProfile(pilotID, true)
		if err != nil {
			pilotName = fmt.Sprintf("Pilot %d", pilotID)
		} else {
			pilotName = profile.Name
		}
	} else {
		// Input is a name
		pilotName = pilotInput
		fmt.Printf("\nSearching for pilot: %s...\n", pilotName)

		// Search in current traffic first
		traffic, err := client.GetTraffic(context.Background())
		if err != nil {
			fmt.Printf("Error fetching traffic: %v\n", err)
			return
		}

		matches := traffic.FilterByName(pilotName)
		if len(matches) == 0 {
			fmt.Printf("Pilot '%s' not found in current traffic.\n", pilotName)
			fmt.Println("Searching in pilot database...")

			// Search in database
			results, err := client.SearchPilots(context.Background(), pilotName)
			if err != nil {
				fmt.Printf("Error searching: %v\n", err)
				return
			}

			if len(results) > 0 {
				fmt.Printf("\nFound %d pilot(s) in database:\n", len(results))
				displayCount := 5
				if len(results) < displayCount {
					displayCount = len(results)
				}
				for i := 0; i < displayCount; i++ {
					fmt.Printf("%d. %s (ID: %d)\n", i+1, results[i].Name, results[i].ID)
				}

				selection := readInput(scanner, "Enter number to watch, or press Enter to cancel: ")
				if idx, err := strconv.Atoi(selection); err == nil && idx >= 1 && idx <= displayCount {
					selected := results[idx-1]
					pilotID = selected.ID
					pilotName = selected.Name
				} else {
					fmt.Println("Cancelled")
					return
				}
			} else {
				fmt.Printf("No pilots found matching '%s'\n", pilotName)
				return
			}
		} else {
			if len(matches) > 1 {
				fmt.Printf("\nFound %d pilots matching '%s':\n", len(matches), pilotName)
				for i, p := range matches {
					if i >= 5 {
						break
					}
					fmt.Printf("%d. %s (%s)\n", i+1, p.Name, p.Callsign)
				}

				selection := readInput(scanner, "Enter number to watch, or press Enter to cancel: ")
				if idx, err := strconv.Atoi(selection); err == nil && idx >= 1 && idx <= len(matches) {
					selected := matches[idx-1]
					if selected.PilotID != nil {
						pilotID = *selected.PilotID
					}
					pilotName = selected.Name
				} else {
					fmt.Println("Cancelled")
					return
				}
			} else {
				if matches[0].PilotID != nil {
					pilotID = *matches[0].PilotID
				}
				pilotName = matches[0].Name
			}
		}
	}

	fmt.Printf("\n🔍 Watching pilot: %s (ID: %d)\n", pilotName, pilotID)
	fmt.Println("Press Ctrl+C to stop")
	fmt.Println(strings.Repeat("=", 80))

	// Watch loop - refresh every 15 seconds
	for {
		traffic, err := client.GetTraffic(context.Background())
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			time.Sleep(15 * time.Second)
			continue
		}

		found := false
		for i := range traffic.AllPilots() {
			p := &traffic.AllPilots()[i]
			if p.PilotID != nil && *p.PilotID == pilotID {
				found = true
				fmt.Printf("\n[%s] %s is ONLINE\n", time.Now().Format("15:04:05"), pilotName)
				displayPilotDetails(p, false, favMgr)
				break
			}
		}

		if !found {
			fmt.Printf("\n[%s] %s is OFFLINE\n", time.Now().Format("15:04:05"), pilotName)
		}

		time.Sleep(15 * time.Second)
	}
}

func browseAirplanes(client *eurofly.Client, scanner *bufio.Scanner) {
	fmt.Println("\n" + strings.Repeat("=", 80))
	fmt.Println("BROWSE AIRPLANES")
	fmt.Println(strings.Repeat("=", 80))

	fmt.Println("\nFetching airplanes...")
	airplanes, err := client.GetAirplanes(context.Background(), nil)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Printf("\nTotal Airplanes: %d\n", len(airplanes))
	fmt.Println("\n1. View all")
	fmt.Println("2. Filter by passengers")
	fmt.Println("3. Filter by price")
	fmt.Println("4. Filter by category")
	fmt.Println("5. Back")

	choice := readInput(scanner, "Select option: ")

	switch choice {
	case "1":
		displayAirplanes(airplanes)
	case "2":
		minStr := readInput(scanner, "Minimum passengers: ")
		if min, err := strconv.Atoi(minStr); err == nil {
			maxStr := readInput(scanner, "Maximum passengers (or Enter for no limit): ")
			var maxPtr *int
			if max, err := strconv.Atoi(maxStr); err == nil {
				maxPtr = &max
			}
			filtered := eurofly.FilterAirplanesByPassengers(airplanes, min, maxPtr)
			displayAirplanes(filtered)
		}
	case "3":
		maxStr := readInput(scanner, "Maximum price: ")
		if max, err := strconv.Atoi(maxStr); err == nil {
			filtered := eurofly.FilterAirplanesByPrice(airplanes, max)
			displayAirplanes(filtered)
		}
	case "4":
		catStr := readInput(scanner, "Category (1-7): ")
		if cat, err := strconv.Atoi(catStr); err == nil {
			filtered := eurofly.FilterAirplanesByCategory(airplanes, cat)
			displayAirplanes(filtered)
		}
	}
}

func displayAirplanes(airplanes []eurofly.Airplane) {
	fmt.Printf("\nShowing %d airplane(s):\n\n", len(airplanes))
	for _, a := range airplanes {
		fmt.Printf("%d. %s - Cat:%d, Pax:%d, Speed:%d km/h, Range:%d km, Price:$%d\n",
			a.Row, a.Name, a.Category, a.Passengers, a.SpeedKmh, a.RangeKm, a.Price)
	}
}

func browseAirports(client *eurofly.Client, scanner *bufio.Scanner) {
	fmt.Println("\n" + strings.Repeat("=", 80))
	fmt.Println("BROWSE AIRPORTS")
	fmt.Println(strings.Repeat("=", 80))

	fmt.Println("\nFetching airports...")
	airports, err := client.GetAirports(context.Background(), nil, nil)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Printf("\nTotal Airports: %d\n", len(airports))
	fmt.Println("\n1. View all (first 50)")
	fmt.Println("2. Filter by country")
	fmt.Println("3. Filter by category")
	fmt.Println("4. Filter by elevation")
	fmt.Println("5. Back")

	choice := readInput(scanner, "Select option: ")

	switch choice {
	case "1":
		displayAirports(airports[:min(50, len(airports))])
	case "2":
		fmt.Println("\nAvailable countries (showing first 20):")
		count := 0
		for id, name := range eurofly.Countries {
			if count >= 20 {
				break
			}
			fmt.Printf("%d. %s (ID: %d)\n", count+1, name, id)
			count++
		}

		countryIDStr := readInput(scanner, "Enter country ID: ")
		if countryID, err := strconv.Atoi(countryIDStr); err == nil {
			filtered, err := client.GetAirports(context.Background(), &countryID, nil)
			if err != nil {
				fmt.Printf("Error: %v\n", err)
				return
			}
			displayAirports(filtered)
		}
	case "3":
		catStr := readInput(scanner, "Category (1-7): ")
		if cat, err := strconv.Atoi(catStr); err == nil {
			filtered := eurofly.FilterAirportsByCategory(airports, cat)
			displayAirports(filtered)
		}
	case "4":
		maxStr := readInput(scanner, "Maximum elevation (meters): ")
		if max, err := strconv.Atoi(maxStr); err == nil {
			filtered := eurofly.FilterAirportsByElevation(airports, max)
			displayAirports(filtered)
		}
	}
}

func displayAirports(airports []eurofly.Airport) {
	fmt.Printf("\nShowing %d airport(s):\n\n", len(airports))
	for _, a := range airports {
		fmt.Printf("%s", a.Name)
		if a.Code != nil {
			fmt.Printf(" - %s", *a.Code)
		}
		if a.Country != nil {
			fmt.Printf(" (%s)", *a.Country)
		}
		if a.Category != nil {
			fmt.Printf(" - Cat:%d", *a.Category)
		}
		if a.Runways != nil {
			fmt.Printf(", Runways:%d", *a.Runways)
		}
		if a.Elevation != nil {
			fmt.Printf(", Elev:%dm", *a.Elevation)
		}
		fmt.Println()
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
