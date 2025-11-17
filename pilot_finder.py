"""
Pilot Finder - Caches and searches for pilots by country and language
"""
import json
import os
from typing import Dict, List, Optional
from eurofly import EuroflyClient

CACHE_FILE = "pilots_cache.json"

class PilotFinder:
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache: Dict[int, Dict] = {}
        self.client = EuroflyClient()
        self.load_cache()
    
    def load_cache(self):
        """Load cached pilot data from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"Loaded {len(self.cache)} pilots from cache")
            except Exception as e:
                print(f"Error loading cache: {e}")
                self.cache = {}
        else:
            print("No cache file found, starting fresh")
    
    def save_cache(self):
        """Save cached pilot data to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(self.cache)} pilots to cache")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def get_pilot_info(self, pilot_id: int) -> Optional[Dict]:
        """Get pilot info from cache or fetch if not cached."""
        # Convert to string for JSON compatibility
        pilot_id_str = str(pilot_id)
        
        # Check if already cached
        if pilot_id_str in self.cache:
            return self.cache[pilot_id_str]
        
        # Fetch from server
        try:
            print(f"Fetching pilot {pilot_id} from server...")
            profile = self.client.get_pilot_profile(pilot_id)
            
            # Store only essential data
            pilot_data = {
                'id': pilot_id,
                'name': profile.name,
                'country': profile.country,
                'language': profile.language
            }
            
            self.cache[pilot_id_str] = pilot_data
            return pilot_data
        except Exception as e:
            print(f"Error fetching pilot {pilot_id}: {e}")
            return None
    
    def update_cache_from_traffic(self):
        """Fetch current traffic and cache all pilot data."""
        print("\nFetching current traffic...")
        traffic = self.client.get_traffic()
        
        all_pilots = traffic.pilots_on_ground + traffic.pilots_in_air
        print(f"Found {len(all_pilots)} pilots in traffic")
        
        newly_cached = 0
        for pilot in all_pilots:
            if pilot.pilot_id:
                pilot_id_str = str(pilot.pilot_id)
                if pilot_id_str not in self.cache:
                    info = self.get_pilot_info(pilot.pilot_id)
                    if info:
                        newly_cached += 1
        
        print(f"Newly cached: {newly_cached} pilots")
        self.save_cache()
    
    def find_pilots_by_country(self, *countries: str) -> List[Dict]:
        """Find all cached pilots from specified countries."""
        countries_lower = [c.lower() for c in countries]
        results = []
        
        for pilot_data in self.cache.values():
            if pilot_data.get('country') and pilot_data['country'].lower() in countries_lower:
                results.append(pilot_data)
        
        return results
    
    def find_pilots_by_language(self, *languages: str) -> List[Dict]:
        """Find all cached pilots who speak specified languages."""
        languages_lower = [lang.lower() for lang in languages]
        results = []
        
        for pilot_data in self.cache.values():
            if pilot_data.get('language'):
                # Check if any of the target languages are in the pilot's language
                pilot_lang_lower = pilot_data['language'].lower()
                if any(lang in pilot_lang_lower for lang in languages_lower):
                    results.append(pilot_data)
        
        return results
    
    def find_russian_speaking_pilots(self) -> List[Dict]:
        """Find pilots from Russia, Belarus, or who speak Russian."""
        # Find by country
        by_country = self.find_pilots_by_country('russia', 'belarus')
        
        # Find by language
        by_language = self.find_pilots_by_language('russian')
        
        # Combine and deduplicate
        all_pilots = {p['id']: p for p in by_country}
        for pilot in by_language:
            all_pilots[pilot['id']] = pilot
        
        return list(all_pilots.values())


def main():
    print("=" * 80)
    print("EUROFLY PILOT FINDER")
    print("=" * 80)
    
    finder = PilotFinder()
    
    # Update cache with current traffic
    finder.update_cache_from_traffic()
    
    # Get current traffic to check who's flying
    print("\nFetching current traffic to find flying Russian-speaking pilots...")
    traffic = finder.client.get_traffic()
    
    # Find Russian-speaking pilots who are currently in the air
    print("\n" + "=" * 80)
    print("CURRENTLY FLYING RUSSIAN-SPEAKING PILOTS")
    print("=" * 80)
    
    flying_russian_pilots = []
    
    for pilot in traffic.pilots_in_air:
        if pilot.pilot_id:
            pilot_id_str = str(pilot.pilot_id)
            if pilot_id_str in finder.cache:
                pilot_data = finder.cache[pilot_id_str]
                # Check if pilot is Russian-speaking
                country = pilot_data.get('country', '').lower()
                language = pilot_data.get('language', '').lower()
                
                is_russian_speaking = (
                    country in ['russia', 'belarus'] or
                    'russian' in language
                )
                
                if is_russian_speaking:
                    flying_russian_pilots.append((pilot, pilot_data))
    
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
    
    print("=" * 80)
    print(f"Total pilots in cache: {len(finder.cache)}")
    print(f"Total pilots in air: {len(traffic.pilots_in_air)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
