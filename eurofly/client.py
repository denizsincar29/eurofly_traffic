"""Eurofly client for fetching and parsing traffic data."""
import httpx
import json
import os
from bs4 import BeautifulSoup
from typing import List, Optional
import re

from .models import Flight, Pilot, PilotProfile, EuroflyTraffic


class EuroflyClient:
    """Client for interacting with the Eurofly traffic system."""
    
    BASE_URL = "https://eurofly.stefankiss.sk/ef3"
    CACHE_FILE = ".cache.json"

    def __init__(self, cache_file: Optional[str] = None):
        """Initialize the Eurofly client.
        
        Args:
            cache_file: Path to cache file. Defaults to '.cache.json' in current directory.
        """
        self.session = httpx.Client(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "X-Requested-With": "XMLHttpRequest"
        })
        self.cache_file = cache_file or self.CACHE_FILE
        self._cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load pilot profiles from cache file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self):
        """Save pilot profiles to cache file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except IOError:
            pass  # Silent fail on cache write errors

    def fetch_traffic_html(self) -> str:
        """Fetch the current traffic HTML from Eurofly."""
        response = self.session.post(
            f"{self.BASE_URL}/[object%20Object]",
            data={"type": "xhr", "offset": "-180", "method": "current_flights3", "let": '""'}
        )
        response.raise_for_status()
        return response.text

    def parse_traffic(self, html: str) -> EuroflyTraffic:
        """Parse traffic HTML into EuroflyTraffic object."""
        soup = BeautifulSoup(html, "html.parser")

        def parse_section(header_text: str):
            section = soup.find("center", string=lambda t: t and header_text in t)
            pilots_list = []
            if not section:
                return pilots_list

            # Find all center tags with h3 containing pilot links
            pilot_centers = section.find_all_next("center")
            for center in pilot_centers:
                # Stop if we hit another section header
                center_text = center.get_text(strip=True)
                if center_text in ["On earth", "In air"]:
                    break
                
                h3 = center.find("h3")
                if not h3:
                    continue
                
                a_tag = h3.find("a")
                if not a_tag or "/ef3/pilot" not in a_tag.get("href", ""):
                    break

                href = a_tag.get("href")
                text = a_tag.get_text(strip=True)
                
                # Extract pilot_id from URL (e.g., /ef3/pilot?pid=661)
                pilot_id = None
                if href:
                    pid_match = re.search(r'pid=(\d+)', href)
                    if pid_match:
                        pilot_id = int(pid_match.group(1))

                # Parse name, callsign and airline
                if ' - ' in text:
                    name_callsign, airline = text.rsplit(' - ', 1)
                else:
                    name_callsign, airline = text, ""
                if ' ' in name_callsign:
                    name, callsign = name_callsign.rsplit(' ', 1)
                else:
                    name, callsign = name_callsign, ""

                # Collect text lines until next center, considering <br>
                flight_lines = []
                sibling = center.next_sibling
                while sibling and sibling.name != "center":
                    # text nodes
                    if isinstance(sibling, str):
                        line = sibling.strip()
                        if line:
                            flight_lines.append(line)
                    # <br> with text
                    elif sibling.name == "br":
                        next_text = sibling.next_sibling
                        if isinstance(next_text, str):
                            line = next_text.strip()
                            if line:
                                flight_lines.append(line)
                    sibling = sibling.next_sibling

                # default values
                aircraft = None
                passengers = 0
                status = None
                location_from = None
                location_to = None
                last_position = None
                description = None

                # parse lines
                for line in flight_lines:
                    # Check if this is a recognized line type
                    is_recognized = False
                    
                    if "with" in line and "passengers" in line:
                        aircraft_part, pax_part = line.split("with", 1)
                        aircraft = aircraft_part.strip()
                        try:
                            passengers = int(pax_part.split("passengers")[0].strip())
                        except ValueError:
                            passengers = 0
                        is_recognized = True
                    elif line == "Crashed":
                        status = "Crashed"
                        is_recognized = True
                    elif "Standing at" in line:
                        status = "Standing"
                        location_from = line.split("Standing at")[1].strip()
                        is_recognized = True
                    elif "Rolling at" in line:
                        status = "Rolling"
                        location_from = line.split("Rolling at")[1].strip()
                        is_recognized = True
                    elif "Taking off at" in line:
                        status = "Taking off"
                        location_from = line.split("Taking off at")[1].strip()
                        is_recognized = True
                    elif "Took of from" in line:
                        status = "In air"
                        location_from = line.split("Took of from:")[1].strip()
                        is_recognized = True
                    elif line.startswith("Course:"):
                        location_to = line.split("Course:")[1].strip()
                        is_recognized = True
                    elif line.startswith("Last known position:"):
                        last_position = line.split("Last known position:")[1].strip()
                        is_recognized = True
                    elif line.startswith("Flightplan:"):
                        locations = line.split("Flightplan:")[1].strip().split(" - ")
                        if locations:
                            location_from = locations[0]
                            location_to = locations[-1]
                        is_recognized = True
                    elif line.startswith("No flightplan"):
                        is_recognized = True
                    
                    # If line is not recognized, it's likely a description
                    if not is_recognized and line and not description:
                        description = line

                flight = Flight(
                    aircraft=aircraft,
                    passengers=passengers,
                    status=status,
                    location_from=location_from,
                    location_to=location_to,
                    last_position=last_position,
                    description=description
                )
                pilot = Pilot(
                    name=name,
                    callsign=callsign,
                    airline=airline,
                    flight=flight,
                    pilot_id=pilot_id
                )
                pilot.set_client(self)
                pilots_list.append(pilot)

            return pilots_list

        pilots_on_ground = parse_section("On earth")
        pilots_in_air = parse_section("In air")
        return EuroflyTraffic(pilots_on_ground=pilots_on_ground, pilots_in_air=pilots_in_air)

    def get_traffic(self) -> EuroflyTraffic:
        """Fetch and parse current traffic."""
        html = self.fetch_traffic_html()
        return self.parse_traffic(html)

    def fetch_pilot_profile_html(self, pilot_id: int) -> str:
        """Fetch the HTML of a pilot's profile page."""
        response = self.session.get(f"{self.BASE_URL}/pilot?pid={pilot_id}")
        response.raise_for_status()
        return response.text

    def parse_pilot_profile(self, html: str, pilot_id: int) -> PilotProfile:
        """Parse a pilot's profile page HTML and return a PilotProfile object."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Find the content div
        content_div = soup.find('div', class_='content')
        if not content_div:
            raise ValueError("Could not find content div in pilot profile page")
        
        text = content_div.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        profile_data = {'pilot_id': pilot_id}
        
        # Extract pilot name and info from first line
        if lines:
            first_line = lines[0]
            # Format: 'Pilot Name - rank - number'
            match = re.match(r'Pilot (.+?) - (.+?) - (\d+)', first_line)
            if match:
                profile_data['name'] = match.group(1)
                profile_data['rank'] = match.group(2)
                profile_data['rank_number'] = int(match.group(3))
            else:
                # Try simpler format: 'Pilot Name'
                match = re.match(r'Pilot (.+)', first_line)
                if match:
                    profile_data['name'] = match.group(1)
        
        # Parse the rest of the content
        i = 1
        while i < len(lines):
            line = lines[i]
            
            if line.startswith('Sex:') and i + 1 < len(lines):
                profile_data['sex'] = lines[i + 1]
                i += 2
            elif line.startswith('Country:'):
                profile_data['country'] = line.replace('Country:', '').strip()
                i += 1
            elif line.startswith('Language:'):
                profile_data['language'] = line.replace('Language:', '').strip()
                i += 1
            elif 'years old' in line:
                age_match = re.search(r'(\d+) years old', line)
                if age_match:
                    profile_data['age'] = int(age_match.group(1))
                i += 1
            elif line.startswith('Rank') and not line.startswith('Rank:'):
                rank_match = re.search(r'Rank (\d+)', line)
                if rank_match:
                    profile_data['overall_rank'] = int(rank_match.group(1))
                i += 1
            elif line.startswith('Registered:'):
                profile_data['registered'] = line.replace('Registered:', '').strip()
                i += 1
            elif line.startswith('Last login:'):
                profile_data['last_login'] = line.replace('Last login:', '').strip()
                i += 1
            elif line.startswith('Last performed flight:'):
                profile_data['last_flight'] = line.replace('Last performed flight:', '').strip()
                i += 1
            elif line.startswith('Points:'):
                points_match = re.search(r'Points: (\d+)', line)
                if points_match:
                    profile_data['points'] = int(points_match.group(1))
                i += 1
            elif line.startswith('Earnings:'):
                earnings_match = re.search(r'Earnings: (\d+)', line)
                if earnings_match:
                    profile_data['earnings'] = int(earnings_match.group(1))
                i += 1
            elif line.startswith('Flights overall:'):
                flights_match = re.search(r'Flights overall: (\d+)', line)
                if flights_match:
                    profile_data['flights_overall'] = int(flights_match.group(1))
                i += 1
            elif line.startswith('Total distance travelled:'):
                dist_match = re.search(r'Total distance travelled: ([\d,]+) Km', line)
                if dist_match:
                    profile_data['total_distance_km'] = int(dist_match.group(1).replace(',', ''))
                i += 1
            elif line.startswith('Total time spent flying:'):
                time_match = re.search(r'Total time spent flying: (.+)', line)
                if time_match:
                    profile_data['total_flight_time'] = time_match.group(1)
                i += 1
            else:
                i += 1
        
        return PilotProfile(**profile_data)

    def get_pilot_profile(self, pilot_id: int, use_cache: bool = True) -> PilotProfile:
        """Fetch and parse a pilot's profile.
        
        Args:
            pilot_id: The pilot's ID
            use_cache: If True, try to load from cache first and save to cache. Default True.
            
        Returns:
            PilotProfile object
        """
        cache_key = str(pilot_id)
        
        # Try to load from cache first if use_cache is True
        if use_cache and cache_key in self._cache:
            try:
                return PilotProfile(**self._cache[cache_key])
            except Exception:
                # If cache is invalid, fetch fresh data
                pass
        
        # Fetch from server
        html = self.fetch_pilot_profile_html(pilot_id)
        profile = self.parse_pilot_profile(html, pilot_id)
        
        # Save to cache if use_cache is True
        if use_cache:
            self._cache[cache_key] = profile.model_dump()
            self._save_cache()
        
        return profile

    def search_pilots(self, query: str) -> List[tuple]:
        """Search for pilots by name.
        
        Args:
            query: Search query (pilot name, partial name, etc.)
            
        Returns:
            List of tuples (pilot_id, pilot_name)
        """
        response = self.session.get(f"{self.BASE_URL}/pilots", params={"name": query})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all pilot links
        pilot_links = soup.find_all('a', href=lambda h: h and '/ef3/pilot?pid=' in h)
        
        results = []
        for link in pilot_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Extract pilot_id from URL
            pid_match = re.search(r'pid=(\d+)', href)
            if pid_match:
                pilot_id = int(pid_match.group(1))
                results.append((pilot_id, text))
        
        return results

    def search_pilots_by_country(self, country_id: int) -> List[tuple]:
        """Search for pilots by country ID.
        
        Args:
            country_id: Country ID from the pilots page
            
        Returns:
            List of tuples (pilot_id, pilot_name)
        """
        response = self.session.get(f"{self.BASE_URL}/pilots", params={"state": str(country_id)})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all pilot links
        pilot_links = soup.find_all('a', href=lambda h: h and '/ef3/pilot?pid=' in h)
        
        results = []
        for link in pilot_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Extract pilot_id from URL
            pid_match = re.search(r'pid=(\d+)', href)
            if pid_match:
                pilot_id = int(pid_match.group(1))
                results.append((pilot_id, text))
        
        return results

    def search_pilots_by_rank(self, rank_level: int) -> List[tuple]:
        """Search for pilots by rank level.
        
        Args:
            rank_level: Rank level (1=intraining, 2=novices, 3=assistants, 4=copilot, 
                        5=first pilot, 6=captain, 7=teacher pilot)
            
        Returns:
            List of tuples (pilot_id, pilot_name)
        """
        response = self.session.get(f"{self.BASE_URL}/pilots", params={"level": str(rank_level)})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all pilot links
        pilot_links = soup.find_all('a', href=lambda h: h and '/ef3/pilot?pid=' in h)
        
        results = []
        for link in pilot_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Extract pilot_id from URL
            pid_match = re.search(r'pid=(\d+)', href)
            if pid_match:
                pilot_id = int(pid_match.group(1))
                results.append((pilot_id, text))
        
        return results

    def search_pilots_advanced(self, name: Optional[str] = None, 
                               country_id: Optional[int] = None, 
                               rank_level: Optional[int] = None) -> List[tuple]:
        """Search for pilots using multiple criteria at once.
        
        Args:
            name: Pilot name or partial name (optional)
            country_id: Country ID from the pilots page (optional)
            rank_level: Rank level 1-7 (optional)
            
        Returns:
            List of tuples (pilot_id, pilot_name)
            
        Note:
            When multiple criteria are specified, they are combined (AND operation).
            The search is performed by passing all parameters to the server.
        """
        params = {}
        if name:
            params["name"] = name
        if country_id is not None:
            params["state"] = str(country_id)
        if rank_level is not None:
            params["level"] = str(rank_level)
        
        if not params:
            # No criteria specified, return empty list
            return []
        
        response = self.session.get(f"{self.BASE_URL}/pilots", params=params)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all pilot links
        pilot_links = soup.find_all('a', href=lambda h: h and '/ef3/pilot?pid=' in h)
        
        results = []
        for link in pilot_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Extract pilot_id from URL
            pid_match = re.search(r'pid=(\d+)', href)
            if pid_match:
                pilot_id = int(pid_match.group(1))
                results.append((pilot_id, text))
        
        return results
