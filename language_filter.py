#!/usr/bin/env python3
"""
Language Filter - Find pilots by language and country criteria

This tool finds pilots who speak specific languages or are from specific countries
by fetching current traffic and checking pilot profiles.
"""
from typing import List, Tuple
from eurofly import EuroflyClient
from eurofly.models import Pilot


def find_russian_speaking_pilots(client: EuroflyClient) -> List[Tuple[Pilot, dict]]:
    """
    Find pilots from Russia, Belarus, or who speak Russian.
    
    Returns:
        List of tuples (Pilot, profile_data) for Russian-speaking pilots
    """
    # Get current traffic
    traffic = client.get_traffic()
    all_pilots = traffic.pilots_on_ground + traffic.pilots_in_air
    
    print(f"Checking {len(all_pilots)} pilots in current traffic...")
    
    russian_speaking_pilots = []
    
    for pilot in all_pilots:
        if not pilot.pilot_id:
            continue
        
        try:
            # Fetch profile (uses library's built-in cache)
            profile = client.get_pilot_profile(pilot.pilot_id)
            
            # Check if pilot is Russian-speaking
            country = (profile.country or '').lower()
            language = (profile.language or '').lower()
            
            is_russian_speaking = (
                country in ['russia', 'belarus'] or
                'russian' in language
            )
            
            if is_russian_speaking:
                profile_data = {
                    'id': pilot.pilot_id,
                    'name': profile.name,
                    'country': profile.country,
                    'language': profile.language
                }
                russian_speaking_pilots.append((pilot, profile_data))
        except Exception as e:
            print(f"Error fetching profile for pilot {pilot.pilot_id}: {e}")
            continue
    
    return russian_speaking_pilots


def find_pilots_by_language(client: EuroflyClient, *languages: str) -> List[Tuple[Pilot, dict]]:
    """
    Find all pilots who speak any of the specified languages.
    
    Args:
        client: EuroflyClient instance
        languages: Language names to search for (e.g., 'russian', 'english')
    
    Returns:
        List of tuples (Pilot, profile_data) for matching pilots
    """
    traffic = client.get_traffic()
    all_pilots = traffic.pilots_on_ground + traffic.pilots_in_air
    
    languages_lower = [lang.lower() for lang in languages]
    print(f"Searching for pilots who speak: {', '.join(languages)}")
    print(f"Checking {len(all_pilots)} pilots in current traffic...")
    
    matching_pilots = []
    
    for pilot in all_pilots:
        if not pilot.pilot_id:
            continue
        
        try:
            profile = client.get_pilot_profile(pilot.pilot_id)
            
            if profile.language:
                pilot_lang_lower = profile.language.lower()
                if any(lang in pilot_lang_lower for lang in languages_lower):
                    profile_data = {
                        'id': pilot.pilot_id,
                        'name': profile.name,
                        'country': profile.country,
                        'language': profile.language
                    }
                    matching_pilots.append((pilot, profile_data))
        except Exception as e:
            print(f"Error fetching profile for pilot {pilot.pilot_id}: {e}")
            continue
    
    return matching_pilots


def find_pilots_by_country(client: EuroflyClient, *countries: str) -> List[Tuple[Pilot, dict]]:
    """
    Find all pilots from specified countries.
    
    Args:
        client: EuroflyClient instance
        countries: Country names to search for (e.g., 'russia', 'france')
    
    Returns:
        List of tuples (Pilot, profile_data) for matching pilots
    """
    traffic = client.get_traffic()
    all_pilots = traffic.pilots_on_ground + traffic.pilots_in_air
    
    countries_lower = [c.lower() for c in countries]
    print(f"Searching for pilots from: {', '.join(countries)}")
    print(f"Checking {len(all_pilots)} pilots in current traffic...")
    
    matching_pilots = []
    
    for pilot in all_pilots:
        if not pilot.pilot_id:
            continue
        
        try:
            profile = client.get_pilot_profile(pilot.pilot_id)
            
            if profile.country and profile.country.lower() in countries_lower:
                profile_data = {
                    'id': pilot.pilot_id,
                    'name': profile.name,
                    'country': profile.country,
                    'language': profile.language
                }
                matching_pilots.append((pilot, profile_data))
        except Exception as e:
            print(f"Error fetching profile for pilot {pilot.pilot_id}: {e}")
            continue
    
    return matching_pilots


def main():
    """Main function - finds and displays Russian-speaking pilots in the air."""
    print("=" * 80)
    print("EUROFLY LANGUAGE FILTER - Russian-Speaking Pilots")
    print("=" * 80)
    
    client = EuroflyClient()
    
    # Find Russian-speaking pilots
    print("\nFetching current traffic and checking pilot profiles...")
    all_russian_pilots = find_russian_speaking_pilots(client)
    
    # Get current traffic to filter only flying pilots
    traffic = client.get_traffic()
    flying_pilot_ids = {p.pilot_id for p in traffic.pilots_in_air if p.pilot_id}
    
    # Filter only flying Russian-speaking pilots
    flying_russian_pilots = [
        (pilot, profile) for pilot, profile in all_russian_pilots
        if pilot.pilot_id in flying_pilot_ids
    ]
    
    # Display results
    print("\n" + "=" * 80)
    print("CURRENTLY FLYING RUSSIAN-SPEAKING PILOTS")
    print("=" * 80)
    
    if flying_russian_pilots:
        print(f"\nFound {len(flying_russian_pilots)} currently flying Russian-speaking pilot(s):\n")
        for i, (pilot, pilot_data) in enumerate(flying_russian_pilots, 1):
            print(f"{i}. {pilot.name} ({pilot.callsign}) - {pilot.airline}")
            print(f"   Pilot ID: {pilot.pilot_id}")
            print(f"   Country: {pilot_data.get('country', 'N/A')}")
            print(f"   Language: {pilot_data.get('language', 'N/A')}")
            print(f"   Flight Status: {pilot.flight.status}")
            if pilot.flight.aircraft:
                print(f"   Aircraft: {pilot.flight.aircraft}")
            if pilot.flight.passengers:
                print(f"   Passengers: {pilot.flight.passengers}")
            if pilot.flight.location_from:
                print(f"   From: {pilot.flight.location_from}")
            if pilot.flight.location_to:
                print(f"   To: {pilot.flight.location_to}")
            if pilot.flight.last_position:
                print(f"   Last Position: {pilot.flight.last_position}")
            print()
    else:
        print("\nNo Russian-speaking pilots currently flying.")
    
    # Summary
    print("=" * 80)
    print(f"Total Russian-speaking pilots in traffic: {len(all_russian_pilots)}")
    print(f"Currently flying: {len(flying_russian_pilots)}")
    print(f"On ground: {len(all_russian_pilots) - len(flying_russian_pilots)}")
    print(f"Total pilots in traffic: {len(traffic.all_pilots)}")
    print("=" * 80)
    print("\nNote: Pilot profiles are cached by the library for better performance.")


if __name__ == "__main__":
    main()
