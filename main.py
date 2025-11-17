from eurofly import EuroflyClient

def display_traffic(traffic, search_prompt=None):
    """Display traffic information, optionally filtered by search prompt."""
    pilots_on_ground = traffic.pilots_on_ground
    pilots_in_air = traffic.pilots_in_air
    
    # Filter if search prompt is provided
    if search_prompt:
        search_lower = search_prompt.lower()
        
        def matches_search(pilot):
            """Check if pilot matches the search prompt."""
            return (search_lower in pilot.name.lower() or
                    search_lower in pilot.callsign.lower() or
                    search_lower in pilot.airline.lower() or
                    (pilot.flight.location_from and search_lower in pilot.flight.location_from.lower()) or
                    (pilot.flight.location_to and search_lower in pilot.flight.location_to.lower()) or
                    (pilot.flight.aircraft and search_lower in pilot.flight.aircraft.lower()))
        
        pilots_on_ground = [p for p in pilots_on_ground if matches_search(p)]
        pilots_in_air = [p for p in pilots_in_air if matches_search(p)]
    
    # Display results
    if search_prompt:
        print(f"\n{'=' * 80}")
        print(f"TRAFFIC SEARCH RESULTS FOR: '{search_prompt}'")
        print(f"{'=' * 80}")
    else:
        print(f"\n{'=' * 80}")
        print(f"ALL TRAFFIC")
        print(f"{'=' * 80}")
    
    print(f"\n--- Pilots on ground ({len(pilots_on_ground)}) ---")
    if pilots_on_ground:
        for pilot in pilots_on_ground:
            print(f"\n{pilot.name} ({pilot.callsign}) - {pilot.airline}")
            if pilot.pilot_id:
                print(f"  Pilot ID: {pilot.pilot_id}")
            print(f"  Status: {pilot.flight.status}")
            if pilot.flight.aircraft:
                print(f"  Aircraft: {pilot.flight.aircraft}")
            if pilot.flight.passengers:
                print(f"  Passengers: {pilot.flight.passengers}")
            if pilot.flight.location_from:
                print(f"  Location: {pilot.flight.location_from}")
    else:
        print("  No pilots found on ground")
    
    print(f"\n--- Pilots in air ({len(pilots_in_air)}) ---")
    if pilots_in_air:
        for pilot in pilots_in_air:
            print(f"\n{pilot.name} ({pilot.callsign}) - {pilot.airline}")
            if pilot.pilot_id:
                print(f"  Pilot ID: {pilot.pilot_id}")
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
                print(f"  Last Position: {pilot.flight.last_position}")
    else:
        print("  No pilots found in air")
    
    print(f"\n{'=' * 80}")
    print(f"Total: {len(pilots_on_ground)} on ground, {len(pilots_in_air)} in air")
    print(f"{'=' * 80}")

# --- Main program ---
if __name__ == "__main__":
    client = EuroflyClient()
    
    # Ask for search prompt
    print("=" * 80)
    print("EUROFLY TRAFFIC VIEWER")
    print("=" * 80)
    print("\nEnter search prompt (pilot name, airport, aircraft, etc.)")
    print("Press Enter for no filter (show all traffic):")
    search_prompt = input("> ").strip()
    
    # Fetch traffic
    print("\nFetching current traffic...")
    traffic = client.get_traffic()
    
    # Display traffic with optional filter
    display_traffic(traffic, search_prompt if search_prompt else None)
