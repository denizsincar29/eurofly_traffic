from eurofly import EuroflyClient

# --- Пример использования ---
if __name__ == "__main__":
    client = EuroflyClient()
    result = client.get_traffic()
    print(result)

    print("\n--- Pilots on ground ---")
    for pilot in result.pilots_on_ground[:10]:
        print(f"{pilot} | Flight: {pilot.flight} | Pilot ID: {pilot.pilot_id}")

    print("\n--- Pilots in air ---")
    for pilot in result.pilots_in_air[:10]:
        print(f"{pilot} | Flight: {pilot.flight} | Pilot ID: {pilot.pilot_id}")
    
    # Example: Fetch profile for the first pilot
    if result.pilots_on_ground and result.pilots_on_ground[0].pilot_id:
        print("\n--- Example: Fetching profile for first pilot on ground ---")
        pilot = result.pilots_on_ground[0]
        profile = client.get_pilot_profile(pilot.pilot_id)
        print(f"Profile: {profile}")
        print(f"  Country: {profile.country}")
        print(f"  Flights: {profile.flights_overall}")
        print(f"  Overall Rank: {profile.overall_rank}")
        print(f"  Total Distance: {profile.total_distance_km} km")
