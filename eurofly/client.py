"""Eurofly client for fetching and parsing traffic data."""
import httpx
import json
import os
import logging
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import re

from .models import Flight, Pilot, PilotProfile, EuroflyTraffic, Airplane, Airport

# Configure logger for this module
logger = logging.getLogger(__name__)


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

                # parse lines - track unrecognized lines for description
                unrecognized_lines_for_desc = []
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
                    elif "Landing at" in line:
                        status = "Landing"
                        location_to = line.split("Landing at")[1].strip()
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
                    
                    # Collect unrecognized lines - description is always the last line
                    if not is_recognized and line:
                        unrecognized_lines_for_desc.append(line)
                
                # Description is the last unrecognized line
                if unrecognized_lines_for_desc:
                    description = unrecognized_lines_for_desc[-1]

                # Debug logging when status is None
                if status is None:
                    # Get the HTML snippet for this pilot entry (compact)
                    pilot_html = str(center)
                    temp_sibling = center.next_sibling
                    html_context = pilot_html
                    for _ in range(10):  # Get up to 10 sibling elements for context
                        if temp_sibling and temp_sibling.name != "center":
                            if hasattr(temp_sibling, 'name'):
                                html_context += str(temp_sibling)
                            elif isinstance(temp_sibling, str):
                                html_context += temp_sibling
                            temp_sibling = temp_sibling.next_sibling
                        else:
                            break
                    
                    # Create a concise, informative debug message
                    reason = "Missing status line (e.g., 'Standing at', 'Landing at', 'Took of from', etc.)"
                    if unrecognized_lines_for_desc:
                        reason += f" - Check if unrecognized line should be a status: {unrecognized_lines_for_desc}"
                    
                    logger.debug(
                        f"⚠️  Status=None for {name} ({callsign}) | Reason: {reason}\n"
                        f"    All lines: {flight_lines}\n"
                        f"    HTML: {html_context[:500]}{'...' if len(html_context) > 500 else ''}"
                    )

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
        
        # Extract bio from h2 tag after "About the pilot"
        bio = None
        h2_tags = content_div.find_all('h2')
        for h2 in h2_tags:
            text = h2.get_text()  # Don't strip yet to preserve line breaks
            if 'About the pilot' in text:
                # Bio is the rest of the text after "About the pilot"
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                # Remove "About the pilot" line
                filtered_lines = [line for line in lines if line != 'About the pilot']
                if filtered_lines:
                    bio = '\n'.join(filtered_lines)
                break
        
        text = content_div.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        profile_data = {'pilot_id': pilot_id}
        if bio:
            profile_data['bio'] = bio
        
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
    
    def fetch_airplanes_html(self, sort_by: Optional[str] = None) -> str:
        """Fetch the private airplanes HTML page.
        
        Args:
            sort_by: Optional sort parameter (name, cat, type, thrust, eng, pas, speed, range, height, price, qual)
        
        Returns:
            HTML content of the airplanes page
        """
        params = {}
        if sort_by:
            params["sort"] = sort_by
        
        response = self.session.get(f"{self.BASE_URL}/private-planes", params=params)
        response.raise_for_status()
        return response.text
    
    def parse_airplanes(self, html: str) -> List[Airplane]:
        """Parse airplanes HTML into list of Airplane objects.
        
        Args:
            html: HTML content from the private-planes page
            
        Returns:
            List of Airplane objects
        """
        soup = BeautifulSoup(html, "html.parser")
        airplanes = []
        
        # Find the main table
        table = soup.find('table')
        if not table:
            return airplanes
        
        # Find all rows, skip the header row
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header row
            cols = row.find_all('td')
            if len(cols) >= 12:
                try:
                    airplane = Airplane(
                        row=int(cols[0].get_text(strip=True)),
                        name=cols[1].get_text(strip=True),
                        category=int(cols[2].get_text(strip=True)),
                        type=cols[3].get_text(strip=True),
                        propulsion_type=cols[4].get_text(strip=True),
                        engines=int(cols[5].get_text(strip=True)),
                        passengers=int(cols[6].get_text(strip=True)),
                        speed_kmh=int(cols[7].get_text(strip=True)),
                        range_km=int(cols[8].get_text(strip=True)),
                        cruising_altitude_m=int(cols[9].get_text(strip=True)),
                        price=int(cols[10].get_text(strip=True)),
                        qualification_price=int(cols[11].get_text(strip=True))
                    )
                    airplanes.append(airplane)
                except (ValueError, IndexError) as e:
                    logger.debug(f"Error parsing airplane row: {e}")
                    continue
        
        return airplanes
    
    def get_airplanes(self, sort_by: Optional[str] = None) -> List[Airplane]:
        """Fetch and parse all private airplanes.
        
        Args:
            sort_by: Optional sort parameter (name, cat, type, thrust, eng, pas, speed, range, height, price, qual)
            
        Returns:
            List of Airplane objects
        """
        html = self.fetch_airplanes_html(sort_by=sort_by)
        return self.parse_airplanes(html)
    
    def filter_airplanes_by_passengers(self, airplanes: List[Airplane], min_passengers: int, max_passengers: Optional[int] = None) -> List[Airplane]:
        """Filter airplanes by passenger capacity.
        
        Args:
            airplanes: List of Airplane objects
            min_passengers: Minimum number of passengers
            max_passengers: Maximum number of passengers (optional)
            
        Returns:
            Filtered list of Airplane objects
        """
        if max_passengers is None:
            return [a for a in airplanes if a.passengers >= min_passengers]
        return [a for a in airplanes if min_passengers <= a.passengers <= max_passengers]
    
    def filter_airplanes_by_price(self, airplanes: List[Airplane], max_price: int) -> List[Airplane]:
        """Filter airplanes by maximum price.
        
        Args:
            airplanes: List of Airplane objects
            max_price: Maximum price
            
        Returns:
            Filtered list of Airplane objects
        """
        return [a for a in airplanes if a.price <= max_price]
    
    def filter_airplanes_by_category(self, airplanes: List[Airplane], category: int) -> List[Airplane]:
        """Filter airplanes by category.
        
        Args:
            airplanes: List of Airplane objects
            category: Category number (1-7)
            
        Returns:
            Filtered list of Airplane objects
        """
        return [a for a in airplanes if a.category == category]
    
    def fetch_airports_html(self, country_id: Optional[int] = None, category: Optional[int] = None) -> str:
        """Fetch the airports HTML page.
        
        Args:
            country_id: Optional country ID to filter by
            category: Optional category to filter by (1-7)
        
        Returns:
            HTML content of the airports page
        """
        params = {}
        if country_id is not None:
            params["state"] = str(country_id)
        if category is not None:
            params["cat"] = str(category)
        
        response = self.session.get(f"{self.BASE_URL}/airports", params=params)
        response.raise_for_status()
        return response.text
    
    def parse_airports(self, html: str) -> List[Airport]:
        """Parse airports HTML into list of Airport objects.
        
        Args:
            html: HTML content from the airports page
            
        Returns:
            List of Airport objects
        """
        soup = BeautifulSoup(html, "html.parser")
        airports = []
        
        # Find all h3 tags which contain airport names
        h3_tags = soup.find_all('h3')
        
        for h3 in h3_tags:
            try:
                # Airport name is in the h3 tag
                name_parts = h3.get_text(strip=True).split(' - ')
                if len(name_parts) < 2:
                    continue
                
                name = name_parts[0].strip()
                code = name_parts[1].strip() if len(name_parts) > 1 else None
                airport_type = name_parts[2].strip() if len(name_parts) > 2 else None
                
                # Find the following text with location info (comes AFTER h3, not before)
                # Need to get parent center tag's next siblings
                center = h3.parent
                next_elements = []
                for sibling in center.next_siblings:
                    if isinstance(sibling, str):
                        text = sibling.strip()
                        if text and text != '--':
                            next_elements.append(text)
                    if len(next_elements) >= 3:
                        break
                
                # Parse the location line (e.g., "Russia - Europe - ")
                country = None
                region = None
                if next_elements:
                    location_text = next_elements[0]
                    location_parts = [p.strip() for p in location_text.split(' - ') if p.strip()]
                    if len(location_parts) >= 1:
                        country = location_parts[0]
                    if len(location_parts) >= 2:
                        region = location_parts[1]
                
                # Parse the details line (e.g., "Cat: 1; Difficulty: 1; Latitude: 51.824; Longitude: 143.082; elevation 69")
                category = None
                difficulty = None
                latitude = None
                longitude = None
                elevation = None
                
                if len(next_elements) >= 2:
                    details_text = next_elements[1]
                    
                    cat_match = re.search(r'Cat:\s*(\d+)', details_text)
                    if cat_match:
                        category = int(cat_match.group(1))
                    
                    diff_match = re.search(r'Difficulty:\s*(\d+)', details_text)
                    if diff_match:
                        difficulty = int(diff_match.group(1))
                    
                    lat_match = re.search(r'Latitude:\s*([\d.-]+)', details_text)
                    if lat_match:
                        latitude = float(lat_match.group(1))
                    
                    lon_match = re.search(r'Longitude:\s*([\d.-]+)', details_text)
                    if lon_match:
                        longitude = float(lon_match.group(1))
                    
                    elev_match = re.search(r'elevation\s+(\d+)', details_text)
                    if elev_match:
                        elevation = int(elev_match.group(1))
                
                # Parse runway info (e.g., "Runways: 1;  Aproach frequency: 118.7; ")
                runways = None
                approach_frequency = None
                
                if len(next_elements) >= 3:
                    runway_text = next_elements[2]
                    
                    runway_match = re.search(r'Runways:\s*(\d+)', runway_text)
                    if runway_match:
                        runways = int(runway_match.group(1))
                    
                    freq_match = re.search(r'Aproach frequency:\s*([\d.]+)', runway_text)
                    if freq_match:
                        approach_frequency = float(freq_match.group(1))
                
                airport = Airport(
                    name=name,
                    code=code,
                    type=airport_type,
                    country=country,
                    region=region,
                    category=category,
                    difficulty=difficulty,
                    latitude=latitude,
                    longitude=longitude,
                    elevation=elevation,
                    runways=runways,
                    approach_frequency=approach_frequency
                )
                airports.append(airport)
            except Exception as e:
                logger.debug(f"Error parsing airport: {e}")
                continue
        
        return airports
    
    def get_airports(self, country_id: Optional[int] = None, category: Optional[int] = None) -> List[Airport]:
        """Fetch and parse airports.
        
        Args:
            country_id: Optional country ID to filter by
            category: Optional category to filter by (1-7)
            
        Returns:
            List of Airport objects
        """
        html = self.fetch_airports_html(country_id=country_id, category=category)
        return self.parse_airports(html)
    
    def filter_airports_by_runway_length(self, airports: List[Airport], min_runways: int = 1) -> List[Airport]:
        """Filter airports by minimum number of runways.
        
        Args:
            airports: List of Airport objects
            min_runways: Minimum number of runways
            
        Returns:
            Filtered list of Airport objects
        """
        return [a for a in airports if a.runways is not None and a.runways >= min_runways]
    
    def filter_airports_by_category(self, airports: List[Airport], category: int) -> List[Airport]:
        """Filter airports by category.
        
        Args:
            airports: List of Airport objects
            category: Category number (1-7)
            
        Returns:
            Filtered list of Airport objects
        """
        return [a for a in airports if a.category == category]
    
    def filter_airports_by_elevation(self, airports: List[Airport], max_elevation: int) -> List[Airport]:
        """Filter airports by maximum elevation.
        
        Args:
            airports: List of Airport objects
            max_elevation: Maximum elevation in meters
            
        Returns:
            Filtered list of Airport objects
        """
        return [a for a in airports if a.elevation is not None and a.elevation <= max_elevation]
