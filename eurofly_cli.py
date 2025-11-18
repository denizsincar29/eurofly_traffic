#!/usr/bin/env python3
"""
Eurofly CLI - Comprehensive command-line tool for Eurofly traffic monitoring.

This tool consolidates all functionality:
- View current traffic
- Search for pilots
- Manage favorites
- Watch specific pilots
- Filter by language/country
- View airplanes and airports
"""

import sys
import json
import os
import time
from typing import List, Optional, Set
from pathlib import Path

from eurofly import EuroflyClient, COUNTRIES, RANKS, FLIGHT_TYPES


# Favorites file location
FAVORITES_FILE = Path.home() / ".eurofly_favorites.json"


class FavoritesManager:
    """Manage favorite pilots."""
    
    def __init__(self):
        self.favorites: Set[int] = set()
        self.load()
    
    def load(self):
        """Load favorites from file."""
        if FAVORITES_FILE.exists():
            try:
                with open(FAVORITES_FILE, 'r') as f:
                    data = json.load(f)
                    self.favorites = set(data.get('favorites', []))
            except Exception as e:
                print(f"Warning: Could not load favorites: {e}")
                self.favorites = set()
    
    def save(self):
        """Save favorites to file."""
        try:
            with open(FAVORITES_FILE, 'w') as f:
                json.dump({'favorites': list(self.favorites)}, f, indent=2)
        except Exception as e:
            print(f"Error saving favorites: {e}")
    
    def add(self, pilot_id: int, pilot_name: str = None):
        """Add a pilot to favorites."""
        self.favorites.add(pilot_id)
        self.save()
        name_str = f" ({pilot_name})" if pilot_name else ""
        print(f"✓ Added pilot ID {pilot_id}{name_str} to favorites")
    
    def remove(self, pilot_id: int):
        """Remove a pilot from favorites."""
        if pilot_id in self.favorites:
            self.favorites.discard(pilot_id)
            self.save()
            print(f"✓ Removed pilot ID {pilot_id} from favorites")
        else:
            print(f"Pilot ID {pilot_id} is not in favorites")
    
    def list_all(self):
        """List all favorite pilot IDs."""
        if not self.favorites:
            print("No favorites saved")
            return []
        
        print(f"\nFavorite Pilots ({len(self.favorites)}):")
        print("=" * 80)
        return sorted(self.favorites)
    
    def is_favorite(self, pilot_id: int) -> bool:
        """Check if a pilot is in favorites."""
        return pilot_id in self.favorites


def display_pilot_details(pilot, show_favorite_status=False, favorites_mgr=None):
    """Display detailed information about a pilot."""
    fav_marker = ""
    if show_favorite_status and favorites_mgr and pilot.pilot_id:
        fav_marker = " ⭐" if favorites_mgr.is_favorite(pilot.pilot_id) else ""
    
    print(f"\n{pilot.name} ({pilot.callsign}) - {pilot.get_flight_type_name()} ({pilot.flight_type}){fav_marker}")
    
    if pilot.pilot_id:
        print(f"  Pilot ID: {pilot.pilot_id}")
    
    if pilot.flight.description:
        print(f"  Description: {pilot.flight.description}")
    
    print(f"  Status: {pilot.flight.status}")
    
    if pilot.flight.aircraft:
        print(f"  Aircraft: {pilot.flight.aircraft}")
    
    if pilot.flight.passengers:
        print(f"  Passengers: {pilot.flight.passengers}")
    
    if pilot.flight.location_from:
        print(f"  From: {pilot.flight.location_from}")
    
    if pilot.flight.location_to:
        print(f"  To: {pilot.flight.location_to}")
    
    if pilot.flight.last_position:
        print(f"  Position: {pilot.flight.last_position}")


def view_traffic(client: EuroflyClient, favorites_mgr: FavoritesManager, search: str = None, favorites_only: bool = False):
    """View current traffic, optionally filtered."""
    print("\nFetching traffic...")
    traffic = client.get_traffic()
    
    pilots_on_ground = traffic.pilots_on_ground
    pilots_in_air = traffic.pilots_in_air
    
    # Filter by search term
    if search:
        search_lower = search.lower()
        
        def matches_search(pilot):
            return (search_lower in pilot.name.lower() or
                    search_lower in pilot.callsign.lower() or
                    search_lower in pilot.flight_type.lower() or
                    (pilot.flight.description and search_lower in pilot.flight.description.lower()) or
                    (pilot.flight.location_from and search_lower in pilot.flight.location_from.lower()) or
                    (pilot.flight.location_to and search_lower in pilot.flight.location_to.lower()) or
                    (pilot.flight.aircraft and search_lower in pilot.flight.aircraft.lower()))
        
        pilots_on_ground = [p for p in pilots_on_ground if matches_search(p)]
        pilots_in_air = [p for p in pilots_in_air if matches_search(p)]
    
    # Filter by favorites
    if favorites_only:
        pilots_on_ground = [p for p in pilots_on_ground if p.pilot_id and favorites_mgr.is_favorite(p.pilot_id)]
        pilots_in_air = [p for p in pilots_in_air if p.pilot_id and favorites_mgr.is_favorite(p.pilot_id)]
    
    # Display header
    print(f"\n{'=' * 80}")
    if favorites_only:
        print("FAVORITE PILOTS ONLINE")
    elif search:
        print(f"TRAFFIC SEARCH: '{search}'")
    else:
        print("ALL TRAFFIC")
    print(f"{'=' * 80}")
    
    # Display pilots on ground
    print(f"\n--- Pilots on ground ({len(pilots_on_ground)}) ---")
    if pilots_on_ground:
        for pilot in pilots_on_ground:
            display_pilot_details(pilot, show_favorite_status=not favorites_only, favorites_mgr=favorites_mgr)
    else:
        print("None")
    
    # Display pilots in air
    print(f"\n--- Pilots in air ({len(pilots_in_air)}) ---")
    if pilots_in_air:
        for pilot in pilots_in_air:
            display_pilot_details(pilot, show_favorite_status=not favorites_only, favorites_mgr=favorites_mgr)
    else:
        print("None")
    
    print(f"\n{'=' * 80}")
    print(f"Total: {len(pilots_on_ground) + len(pilots_in_air)} pilot(s)")
    print(f"{'=' * 80}")


def search_pilots_menu(client: EuroflyClient, favorites_mgr: FavoritesManager):
    """Search for pilots in the database."""
    print("\n" + "=" * 80)
    print("PILOT SEARCH")
    print("=" * 80)
    print("\n1. Search by name")
    print("2. Search by country")
    print("3. Search by rank")
    print("4. Advanced search")
    print("5. Back to main menu")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        name = input("Enter pilot name to search: ").strip()
        if name:
            results = client.search_pilots(name)
            display_search_results(client, favorites_mgr, results, f"Search: {name}")
    
    elif choice == "2":
        print("\nAvailable countries (showing first 20):")
        for i, (cid, cname) in enumerate(list(COUNTRIES.items())[:20], 1):
            print(f"{i}. {cname} (ID: {cid})")
        print("... and more")
        
        country_id = input("\nEnter country ID: ").strip()
        if country_id.isdigit():
            country_id = int(country_id)
            country_name = COUNTRIES.get(country_id, f"Country {country_id}")
            results = client.search_pilots_by_country(country_id)
            display_search_results(client, favorites_mgr, results, f"Country: {country_name}")
    
    elif choice == "3":
        print("\nAvailable ranks:")
        for rid, rname in RANKS.items():
            print(f"{rid}. {rname}")
        
        rank_id = input("\nEnter rank ID: ").strip()
        if rank_id.isdigit():
            rank_id = int(rank_id)
            rank_name = RANKS.get(rank_id, f"Rank {rank_id}")
            results = client.search_pilots_by_rank(rank_id)
            display_search_results(client, favorites_mgr, results, f"Rank: {rank_name}")
    
    elif choice == "4":
        print("\nAdvanced Search")
        name = input("Name (or Enter to skip): ").strip() or None
        country_id = input("Country ID (or Enter to skip): ").strip()
        country_id = int(country_id) if country_id.isdigit() else None
        rank = input("Rank ID (or Enter to skip): ").strip()
        rank = int(rank) if rank.isdigit() else None
        
        results = client.search_pilots_advanced(name=name, country=country_id, rank=rank)
        display_search_results(client, favorites_mgr, results, "Advanced search")


def display_search_results(client: EuroflyClient, favorites_mgr: FavoritesManager, results: List, title: str):
    """Display search results and allow viewing profiles or adding to favorites."""
    if not results:
        print("\nNo pilots found")
        return
    
    print(f"\n{title} - Found {len(results)} pilot(s):\n")
    display_results = results[:50]
    
    for i, (pilot_id, pilot_name) in enumerate(display_results, 1):
        fav_marker = " ⭐" if favorites_mgr.is_favorite(pilot_id) else ""
        print(f"{i}. {pilot_name} (ID: {pilot_id}){fav_marker}")
    
    if len(results) > 50:
        print(f"\n... and {len(results) - 50} more pilots")
    
    # Options
    print("\nOptions:")
    print("  <number>     - View pilot profile")
    print("  f <number>   - Add pilot to favorites")
    print("  u <number>   - Remove pilot from favorites")
    print("  Enter        - Back to menu")
    
    choice = input("\nSelect option: ").strip()
    
    if not choice:
        return
    
    parts = choice.split()
    
    # Add to favorites
    if len(parts) == 2 and parts[0].lower() == 'f':
        try:
            index = int(parts[1]) - 1
            if 0 <= index < len(display_results):
                pilot_id, pilot_name = display_results[index]
                favorites_mgr.add(pilot_id, pilot_name)
        except ValueError:
            print("Invalid input")
        return
    
    # Remove from favorites
    if len(parts) == 2 and parts[0].lower() == 'u':
        try:
            index = int(parts[1]) - 1
            if 0 <= index < len(display_results):
                pilot_id, pilot_name = display_results[index]
                favorites_mgr.remove(pilot_id)
        except ValueError:
            print("Invalid input")
        return
    
    # View profile
    try:
        index = int(choice) - 1
        if 0 <= index < len(display_results):
            pilot_id, pilot_name = display_results[index]
            view_pilot_profile(client, favorites_mgr, pilot_id, pilot_name)
    except ValueError:
        print("Invalid input")


def view_pilot_profile(client: EuroflyClient, favorites_mgr: FavoritesManager, pilot_id: int, pilot_name: str):
    """View detailed pilot profile."""
    print(f"\nFetching profile for {pilot_name}...")
    profile = client.get_pilot_profile(pilot_id, use_cache=False)
    
    # Check if currently flying
    traffic = client.get_traffic()
    flying_pilot = None
    for pilot in traffic.all_pilots:
        if pilot.pilot_id == pilot_id:
            flying_pilot = pilot
            break
    
    # Display profile
    print("\n" + "=" * 80)
    print(f"PILOT PROFILE: {profile.name}")
    is_fav = favorites_mgr.is_favorite(pilot_id)
    print(f"Favorite: {'Yes ⭐' if is_fav else 'No'}")
    print("=" * 80)
    
    if profile.bio:
        print(f"\n📝 Bio: {profile.bio}")
    
    # Show current flight if flying
    if flying_pilot:
        print(f"\n{'=' * 80}")
        print("🛫 CURRENTLY FLYING")
        print("=" * 80)
        display_pilot_details(flying_pilot)
        print("=" * 80)
    
    # Show profile details
    print(f"\nPilot ID: {pilot_id}")
    
    if profile.rank:
        print(f"Rank: {profile.rank}", end="")
        if profile.rank_number:
            print(f" (#{profile.rank_number})", end="")
        print()
    
    if profile.overall_rank:
        print(f"Overall Rank: #{profile.overall_rank}")
    
    if profile.sex:
        print(f"Sex: {profile.sex}")
    
    if profile.country:
        print(f"Country: {profile.country}")
    
    if profile.language:
        print(f"Language: {profile.language}")
    
    if profile.age:
        print(f"Age: {profile.age} years old")
    
    if profile.registered:
        print(f"\nRegistered: {profile.registered}")
    
    if profile.last_login:
        print(f"Last Login: {profile.last_login}")
    
    if profile.last_flight:
        print(f"Last Flight: {profile.last_flight}")
    
    if profile.flights_overall:
        print(f"\nFlights Overall: {profile.flights_overall}")
    
    if profile.total_distance_km:
        print(f"Total Distance: {profile.total_distance_km} km")
    
    if profile.total_flight_time:
        print(f"Total Flight Time: {profile.total_flight_time}")
    
    if profile.points:
        print(f"\nPoints: {profile.points}")
    
    if profile.earnings:
        print(f"Earnings: ${profile.earnings:,.2f}")
    
    print("=" * 80)
    
    # Options
    print("\nOptions:")
    if is_fav:
        print("  u - Remove from favorites")
    else:
        print("  f - Add to favorites")
    print("  Enter - Back")
    
    choice = input("\nSelect option: ").strip().lower()
    
    if choice == 'f' and not is_fav:
        favorites_mgr.add(pilot_id, profile.name)
    elif choice == 'u' and is_fav:
        favorites_mgr.remove(pilot_id)


def manage_favorites(client: EuroflyClient, favorites_mgr: FavoritesManager):
    """Manage favorites."""
    print("\n" + "=" * 80)
    print("MANAGE FAVORITES")
    print("=" * 80)
    
    fav_ids = favorites_mgr.list_all()
    
    if not fav_ids:
        return
    
    # Fetch profiles for favorites
    print("\nFetching profiles...")
    profiles = []
    for pilot_id in fav_ids:
        try:
            profile = client.get_pilot_profile(pilot_id)
            profiles.append((pilot_id, profile.name))
        except:
            profiles.append((pilot_id, f"Pilot {pilot_id}"))
    
    for i, (pilot_id, name) in enumerate(profiles, 1):
        print(f"{i}. {name} (ID: {pilot_id})")
    
    print("\nOptions:")
    print("  <number> - View pilot profile")
    print("  u <number> - Remove from favorites")
    print("  Enter - Back")
    
    choice = input("\nSelect option: ").strip()
    
    if not choice:
        return
    
    parts = choice.split()
    
    # Remove from favorites
    if len(parts) == 2 and parts[0].lower() == 'u':
        try:
            index = int(parts[1]) - 1
            if 0 <= index < len(profiles):
                pilot_id, name = profiles[index]
                favorites_mgr.remove(pilot_id)
        except ValueError:
            print("Invalid input")
        return
    
    # View profile
    try:
        index = int(choice) - 1
        if 0 <= index < len(profiles):
            pilot_id, name = profiles[index]
            view_pilot_profile(client, favorites_mgr, pilot_id, name)
    except ValueError:
        print("Invalid input")


def watch_pilot(client: EuroflyClient, favorites_mgr: FavoritesManager):
    """Watch a specific pilot."""
    pilot_input = input("\nEnter pilot name or ID to watch: ").strip()
    
    if not pilot_input:
        print("No input provided")
        return
    
    pilot_id = None
    pilot_name = None
    
    # Check if input is a digit (ID)
    if pilot_input.isdigit():
        pilot_id = int(pilot_input)
        # Get pilot name from profile
        try:
            profile = client.get_pilot_profile(pilot_id)
            pilot_name = profile.name
        except:
            pilot_name = f"Pilot {pilot_id}"
    else:
        # Input is a name, search for the pilot
        pilot_name = pilot_input
        print(f"\nSearching for pilot: {pilot_name}...")
        
        # Search in current traffic first
        traffic = client.get_traffic()
        matches = [p for p in traffic.all_pilots if pilot_name.lower() in p.name.lower()]
        
        if not matches:
            print(f"Pilot '{pilot_name}' not found in current traffic.")
            print("Searching in pilot database...")
            
            # Search in database
            try:
                results = client.search_pilots_by_name(pilot_name)
                if results:
                    print(f"\nFound {len(results)} pilot(s) in database:")
                    for i, profile in enumerate(results[:5], 1):
                        print(f"{i}. {profile.name} (ID: {profile.pilot_id})")
                    
                    selection = input("\nEnter number to watch, or press Enter to cancel: ").strip()
                    if selection.isdigit() and 1 <= int(selection) <= len(results[:5]):
                        selected_profile = results[int(selection) - 1]
                        pilot_id = selected_profile.pilot_id
                        pilot_name = selected_profile.name
                    else:
                        print("Cancelled")
                        return
                else:
                    print(f"No pilots found matching '{pilot_name}'")
                    return
            except Exception as e:
                print(f"Error searching for pilot: {e}")
                return
        elif len(matches) == 1:
            pilot_id = matches[0].pilot_id
            pilot_name = matches[0].name
            print(f"Found: {pilot_name} (ID: {pilot_id})")
        else:
            print(f"\nFound {len(matches)} pilots currently flying:")
            for i, p in enumerate(matches[:10], 1):
                print(f"{i}. {p.name} (ID: {p.pilot_id}) - {p.callsign}")
            
            selection = input("\nEnter number to watch, or press Enter to cancel: ").strip()
            if selection.isdigit() and 1 <= int(selection) <= len(matches[:10]):
                selected_pilot = matches[int(selection) - 1]
                pilot_id = selected_pilot.pilot_id
                pilot_name = selected_pilot.name
            else:
                print("Cancelled")
                return
    
    if not pilot_id:
        print("Could not determine pilot ID")
        return
    
    print(f"\nWatching {pilot_name} (ID: {pilot_id})")
    print("Refreshing every 15 seconds. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            traffic = client.get_traffic()
            
            # Find pilot in traffic
            found_pilot = None
            for pilot in traffic.all_pilots:
                if pilot.pilot_id == pilot_id:
                    found_pilot = pilot
                    break
            
            print(f"\n{'=' * 80}")
            print(f"Status at {time.strftime('%H:%M:%S')}")
            print(f"{'=' * 80}")
            
            if found_pilot:
                display_pilot_details(found_pilot, show_favorite_status=True, favorites_mgr=favorites_mgr)
            else:
                print(f"\n{pilot_name} is currently offline")
                print("\nStopping watch - pilot offline for 15 seconds")
                break
            
            time.sleep(15)
    
    except KeyboardInterrupt:
        print("\n\nStopped watching")


def main_menu():
    """Main menu."""
    client = EuroflyClient()
    favorites_mgr = FavoritesManager()
    
    while True:
        print("\n" + "=" * 80)
        print("EUROFLY CLI - Main Menu")
        print("=" * 80)
        print("\n1. View all traffic")
        print("2. Search traffic")
        print("3. View favorites flying")
        print("4. Search pilots")
        print("5. Manage favorites")
        print("6. Watch pilot")
        print("7. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            view_traffic(client, favorites_mgr)
        
        elif choice == "2":
            search_term = input("Enter search term: ").strip()
            if search_term:
                view_traffic(client, favorites_mgr, search=search_term)
        
        elif choice == "3":
            view_traffic(client, favorites_mgr, favorites_only=True)
        
        elif choice == "4":
            search_pilots_menu(client, favorites_mgr)
        
        elif choice == "5":
            manage_favorites(client, favorites_mgr)
        
        elif choice == "6":
            watch_pilot(client, favorites_mgr)
        
        elif choice == "7":
            print("\nGoodbye!")
            break
        
        else:
            print("\nInvalid option")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
