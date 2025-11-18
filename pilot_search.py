#!/usr/bin/env python3
"""
Pilot Search Tool - Search for pilots using various criteria
"""
from eurofly import EuroflyClient, COUNTRIES, COUNTRY_NAME_TO_ID, RANKS


def _check_if_flying(client, pilot_id, pilot_name):
    """Check if a pilot is currently flying and return their flight info.
    
    Args:
        client: EuroflyClient instance
        pilot_id: Pilot's ID for exact matching
        pilot_name: Pilot's name for fallback matching
        
    Returns:
        Pilot object if flying, None otherwise
    """
    try:
        traffic = client.get_traffic()
        
        # Try to find by pilot_id first (most reliable)
        if pilot_id:
            for pilot in traffic.all_pilots:
                if pilot.pilot_id == pilot_id:
                    return pilot
        
        # Fallback to name matching (partial match)
        pilots = traffic.filter_by_name(pilot_name)
        if pilots:
            return pilots[0]  # Return the first match
        
        return None
    except Exception as e:
        print(f"Error checking flight status: {e}")
        return None


def _display_current_flight(pilot):
    """Display current flight information for a pilot."""
    print("\n" + "=" * 80)
    print("🛫 CURRENTLY FLYING")
    print("=" * 80)
    
    print(f"\nPilot: {pilot.name} ({pilot.callsign})")
    if pilot.airline:
        print(f"Airline: {pilot.airline}")
    
    if pilot.flight.description:
        print(f"Description: {pilot.flight.description}")
    
    print(f"\nFlight Status: {pilot.flight.status}")
    
    if pilot.flight.aircraft:
        print(f"Aircraft: {pilot.flight.aircraft}")
    
    if pilot.flight.passengers:
        print(f"Passengers: {pilot.flight.passengers}")
    
    if pilot.flight.location_from:
        print(f"From: {pilot.flight.location_from}")
    
    if pilot.flight.location_to:
        print(f"To: {pilot.flight.location_to}")
    
    if pilot.flight.last_position:
        print(f"Current Position: {pilot.flight.last_position}")
    
    print("=" * 80)


def _display_full_profile(profile, client=None, pilot_name=None):
    """Display full pilot profile information."""
    print("\n" + "=" * 80)
    print(f"PILOT PROFILE: {profile.name}")
    print("=" * 80)
    
    # Show bio first, right after the header for maximum visibility
    if profile.bio:
        print(f"\n📝 Bio: {profile.bio}")
    
    # Check if pilot is currently flying
    if client:
        flying_pilot = _check_if_flying(client, profile.pilot_id, pilot_name or profile.name)
        if flying_pilot:
            _display_current_flight(flying_pilot)
    
    print(f"\nPilot ID: {profile.pilot_id}")
    
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
        print(f"Total Distance: {profile.total_distance_km:,} km")
    
    if profile.total_flight_time:
        print(f"Total Flight Time: {profile.total_flight_time}")
    
    if profile.points:
        print(f"\nPoints: {profile.points:,}")
    
    if profile.earnings:
        print(f"Earnings: ${profile.earnings:,.2f}")
    
    print("=" * 80)


def search_by_name():
    """Search pilots by name."""
    print("\n" + "=" * 80)
    print("SEARCH PILOTS BY NAME")
    print("=" * 80)
    
    name = input("\nEnter pilot name (or part of name): ").strip()
    if not name:
        print("No name entered.")
        return
    
    client = EuroflyClient()
    print(f"\nSearching for pilots matching '{name}'...")
    results = client.search_pilots(name)
    
    if results:
        print(f"\nFound {len(results)} pilot(s):\n")
        for i, (pilot_id, pilot_name) in enumerate(results, 1):
            print(f"{i}. {pilot_name} (ID: {pilot_id})")
        
        # Ask if user wants to see details
        if len(results) > 0:
            choice = input("\nEnter pilot number to see full details (or press Enter to skip): ").strip()
            if choice:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(results):
                        pilot_id, pilot_name = results[index]
                        print(f"\nFetching full profile for {pilot_name}...")
                        profile = client.get_pilot_profile(pilot_id)
                        _display_full_profile(profile, client, pilot_name)
                    else:
                        print("Invalid pilot number.")
                except ValueError:
                    print("Invalid input.")
    else:
        print("\nNo pilots found.")


def search_by_country():
    """Search pilots by country."""
    print("\n" + "=" * 80)
    print("SEARCH PILOTS BY COUNTRY")
    print("=" * 80)
    
    print("\nYou can search by:")
    print("  1. Country name (e.g., 'Russia', 'France', 'USA')")
    print("  2. Country ID (e.g., 151, 124, etc.)")
    print("\nAvailable countries (showing first 20):")
    
    # Display first 20 countries
    country_list = list(COUNTRIES.items())[:20]
    for i in range(0, len(country_list), 3):
        row = country_list[i:i+3]
        print("  ".join([f"{cid:3d}. {name:20s}" for cid, name in row]))
    print(f"\n... and {len(COUNTRIES) - 20} more countries")
    
    user_input = input("\nEnter country name or ID: ").strip()
    if not user_input:
        print("No input provided.")
        return
    
    # Try to parse as ID first
    country_id = None
    try:
        country_id = int(user_input)
        if country_id not in COUNTRIES:
            print(f"Country ID {country_id} not found.")
            return
    except ValueError:
        # Not a number, try as country name
        country_id = COUNTRY_NAME_TO_ID.get(user_input.lower())
        if country_id is None:
            print(f"Country '{user_input}' not found.")
            print("Please check spelling or use country ID.")
            return
    
    client = EuroflyClient()
    country_name = COUNTRIES.get(country_id, f"Country {country_id}")
    print(f"\nSearching for pilots from {country_name}...")
    results = client.search_pilots_by_country(country_id)
    
    if results:
        display_results = results[:50]  # Limit to 50 for display
        print(f"\nFound {len(results)} pilot(s):\n")
        for i, (pilot_id, pilot_name) in enumerate(display_results, 1):
            print(f"{i}. {pilot_name} (ID: {pilot_id})")
        if len(results) > 50:
            print(f"\n... and {len(results) - 50} more pilots")
        
        # Ask if user wants to see details
        if len(display_results) > 0:
            choice = input("\nEnter pilot number to see full details (or press Enter to skip): ").strip()
            if choice:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(display_results):
                        pilot_id, pilot_name = display_results[index]
                        print(f"\nFetching full profile for {pilot_name}...")
                        profile = client.get_pilot_profile(pilot_id)
                        _display_full_profile(profile, client, pilot_name)
                    else:
                        print("Invalid pilot number.")
                except ValueError:
                    print("Invalid input.")
    else:
        print("\nNo pilots found.")


def search_by_rank():
    """Search pilots by rank level."""
    print("\n" + "=" * 80)
    print("SEARCH PILOTS BY RANK")
    print("=" * 80)
    
    print("\nAvailable ranks:")
    for rank_id, rank_name in RANKS.items():
        print(f"  {rank_id}. {rank_name}")
    
    try:
        rank_level = int(input("\nEnter rank level (1-7): ").strip())
        if rank_level not in RANKS:
            print("Invalid rank level.")
            return
    except ValueError:
        print("Invalid rank level.")
        return
    
    client = EuroflyClient()
    rank_name = RANKS[rank_level]
    print(f"\nSearching for pilots with rank '{rank_name}' or higher...")
    results = client.search_pilots_by_rank(rank_level)
    
    if results:
        display_results = results[:50]  # Limit to 50 for display
        print(f"\nFound {len(results)} pilot(s):\n")
        for i, (pilot_id, pilot_name) in enumerate(display_results, 1):
            print(f"{i}. {pilot_name} (ID: {pilot_id})")
        if len(results) > 50:
            print(f"\n... and {len(results) - 50} more pilots")
        
        # Ask if user wants to see details
        if len(display_results) > 0:
            choice = input("\nEnter pilot number to see full details (or press Enter to skip): ").strip()
            if choice:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(display_results):
                        pilot_id, pilot_name = display_results[index]
                        print(f"\nFetching full profile for {pilot_name}...")
                        profile = client.get_pilot_profile(pilot_id)
                        _display_full_profile(profile, client, pilot_name)
                    else:
                        print("Invalid pilot number.")
                except ValueError:
                    print("Invalid input.")
    else:
        print("\nNo pilots found.")


def search_advanced():
    """Search pilots by multiple criteria at once."""
    print("\n" + "=" * 80)
    print("ADVANCED SEARCH - Multiple Criteria")
    print("=" * 80)
    
    print("\nYou can combine multiple search criteria.")
    print("Leave any field empty to skip that criterion.\n")
    
    # Get name
    name = input("Enter pilot name (or press Enter to skip): ").strip()
    name = name if name else None
    
    # Get country
    country_id = None
    country_input = input("Enter country name or ID (or press Enter to skip): ").strip()
    if country_input:
        try:
            country_id = int(country_input)
            if country_id not in COUNTRIES:
                print(f"Warning: Country ID {country_id} not found. Skipping country filter.")
                country_id = None
        except ValueError:
            country_id = COUNTRY_NAME_TO_ID.get(country_input.lower())
            if country_id is None:
                print(f"Warning: Country '{country_input}' not found. Skipping country filter.")
    
    # Get rank
    rank_level = None
    rank_input = input("Enter rank level 1-7 (or press Enter to skip): ").strip()
    if rank_input:
        try:
            rank_level = int(rank_input)
            if rank_level not in RANKS:
                print(f"Warning: Invalid rank level {rank_level}. Skipping rank filter.")
                rank_level = None
        except ValueError:
            print(f"Warning: Invalid rank level. Skipping rank filter.")
    
    # Check if any criteria were provided
    if not any([name, country_id, rank_level]):
        print("\nNo search criteria provided.")
        return
    
    # Build description of search
    criteria = []
    if name:
        criteria.append(f"name containing '{name}'")
    if country_id:
        criteria.append(f"from {COUNTRIES[country_id]}")
    if rank_level:
        criteria.append(f"rank {RANKS[rank_level]} or higher")
    
    print(f"\nSearching for pilots with: {', '.join(criteria)}...")
    
    client = EuroflyClient()
    results = client.search_pilots_advanced(name=name, country_id=country_id, rank_level=rank_level)
    
    if results:
        display_results = results[:50]  # Limit to 50 for display
        print(f"\nFound {len(results)} pilot(s):\n")
        for i, (pilot_id, pilot_name) in enumerate(display_results, 1):
            print(f"{i}. {pilot_name} (ID: {pilot_id})")
        if len(results) > 50:
            print(f"\n... and {len(results) - 50} more pilots")
        
        # Ask if user wants to see details
        if len(display_results) > 0:
            choice = input("\nEnter pilot number to see full details (or press Enter to skip): ").strip()
            if choice:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(display_results):
                        pilot_id, pilot_name = display_results[index]
                        print(f"\nFetching full profile for {pilot_name}...")
                        profile = client.get_pilot_profile(pilot_id)
                        _display_full_profile(profile, client, pilot_name)
                    else:
                        print("Invalid pilot number.")
                except ValueError:
                    print("Invalid input.")
    else:
        print("\nNo pilots found matching all criteria.")


def main():
    """Main menu for pilot search."""
    while True:
        print("\n" + "=" * 80)
        print("EUROFLY PILOT SEARCH")
        print("=" * 80)
        print("\nSearch options:")
        print("  1. Search by name")
        print("  2. Search by country")
        print("  3. Search by rank")
        print("  4. Advanced search (multiple criteria)")
        print("  5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            search_by_name()
        elif choice == "2":
            search_by_country()
        elif choice == "3":
            search_by_rank()
        elif choice == "4":
            search_advanced()
        elif choice == "5":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    main()
