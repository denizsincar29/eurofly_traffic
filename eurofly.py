import httpx
from bs4 import BeautifulSoup
from typing import List, Optional
import re

class Flight:
    def __init__(self, aircraft: str, passengers: int, status: str,
                 location_from: Optional[str]=None, location_to: Optional[str]=None,
                 last_position: Optional[str]=None):
        self.aircraft = aircraft
        self.passengers = passengers
        self.status = status
        self.location_from = location_from
        self.location_to = location_to
        self.last_position = last_position

    def __repr__(self):
        return (f"<Flight {self.aircraft}, {self.passengers} pax, status={self.status}, "
                f"from={self.location_from}, to={self.location_to}, last={self.last_position}>")

class PilotProfile:
    def __init__(self, pilot_id: int, name: str, rank: Optional[str]=None, rank_number: Optional[int]=None,
                 sex: Optional[str]=None, country: Optional[str]=None, language: Optional[str]=None,
                 age: Optional[int]=None, overall_rank: Optional[int]=None, registered: Optional[str]=None,
                 last_login: Optional[str]=None, last_flight: Optional[str]=None, points: Optional[int]=None,
                 earnings: Optional[int]=None, flights_overall: Optional[int]=None,
                 total_distance_km: Optional[int]=None, total_flight_time: Optional[str]=None):
        self.pilot_id = pilot_id
        self.name = name
        self.rank = rank
        self.rank_number = rank_number
        self.sex = sex
        self.country = country
        self.language = language
        self.age = age
        self.overall_rank = overall_rank
        self.registered = registered
        self.last_login = last_login
        self.last_flight = last_flight
        self.points = points
        self.earnings = earnings
        self.flights_overall = flights_overall
        self.total_distance_km = total_distance_km
        self.total_flight_time = total_flight_time

    def __repr__(self):
        return f"<PilotProfile {self.name} (ID:{self.pilot_id}), Rank:{self.overall_rank}, Flights:{self.flights_overall}>"

class Pilot:
    def __init__(self, name: str, callsign: str, airline: str, flight: Flight, pilot_id: Optional[int]=None, client: Optional['EuroflyClient']=None):
        self.name = name
        self.callsign = callsign
        self.airline = airline
        self.flight = flight
        self.pilot_id = pilot_id
        self.client = client

    def get_info(self) -> Optional[PilotProfile]:
        """Fetch full pilot profile information using the client."""
        if not self.client:
            raise ValueError("Client reference not set for this Pilot object")
        if not self.pilot_id:
            raise ValueError("Pilot ID not available for this Pilot object")
        return self.client.get_pilot_profile(self.pilot_id)

    def __repr__(self):
        return f"<Pilot {self.name} ({self.callsign}) - {self.airline}>"

class EuroflyTraffic:
    def __init__(self, pilots_on_ground: List[Pilot], pilots_in_air: List[Pilot]):
        self.pilots_on_ground = pilots_on_ground
        self.pilots_in_air = pilots_in_air

    def __repr__(self):
        return f"<EuroflyTraffic ground={len(self.pilots_on_ground)}, air={len(self.pilots_in_air)}>"

class EuroflyClient:
    BASE_URL = "https://eurofly.stefankiss.sk/ef3"

    def __init__(self):
        self.session = httpx.Client(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "X-Requested-With": "XMLHttpRequest"
        })

    def fetch_traffic_html(self) -> str:
        response = self.session.post(
            f"{self.BASE_URL}/[object%20Object]",
            data={"type": "xhr", "offset": "-180", "method": "current_flights3", "let": '""'}
        )
        response.raise_for_status()
        return response.text

    def parse_traffic(self, html: str) -> EuroflyTraffic:
        soup = BeautifulSoup(html, "html.parser")

        def parse_section(header_text: str):
            section = soup.find("center", string=lambda t: t and header_text in t)
            pilots_list = []
            if not section:
                return pilots_list

            # Find all center tags with h3 containing pilot links
            pilot_centers = section.find_all_next("center")
            for center in pilot_centers:
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

                # Разделяем имя, callsign и авиакомпанию
                if ' - ' in text:
                    name_callsign, airline = text.rsplit(' - ', 1)
                else:
                    name_callsign, airline = text, ""
                if ' ' in name_callsign:
                    name, callsign = name_callsign.rsplit(' ', 1)
                else:
                    name, callsign = name_callsign, ""

                # собираем текстовые линии до следующего center, учитывая <br>
                flight_lines = []
                sibling = center.next_sibling
                while sibling and sibling.name != "center":
                    # текстовые узлы
                    if isinstance(sibling, str):
                        line = sibling.strip()
                        if line:
                            flight_lines.append(line)
                    # <br> с текстом
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

                # парсим строки
                for line in flight_lines:
                    if "with" in line and "passengers" in line:
                        aircraft_part, pax_part = line.split("with", 1)
                        aircraft = aircraft_part.strip()
                        try:
                            passengers = int(pax_part.split("passengers")[0].strip())
                        except ValueError:
                            passengers = 0
                    if line == "Crashed":
                        status = "Crashed"
                    elif "Standing at" in line:
                        status = "Standing"
                        location_from = line.split("Standing at")[1].strip()
                    elif "Rolling at" in line:
                        status = "Rolling"
                        location_from = line.split("Rolling at")[1].strip()
                    elif "Taking off at" in line:
                        status = "Taking off"
                        location_from = line.split("Taking off at")[1].strip()
                    elif "Took of from" in line:
                        status = "In air"
                        location_from = line.split("Took of from:")[1].strip()
                    elif line.startswith("Course:"):
                        location_to = line.split("Course:")[1].strip()
                    elif line.startswith("Last known position:"):
                        last_position = line.split("Last known position:")[1].strip()
                    elif line.startswith("Flightplan:"):
                        locations = line.split("Flightplan:")[1].strip().split(" - ")
                        if locations:
                            location_from = locations[0]
                            location_to = locations[-1]

                flight = Flight(aircraft, passengers, status, location_from, location_to, last_position)
                pilot = Pilot(name, callsign, airline, flight, pilot_id=pilot_id, client=self)
                pilots_list.append(pilot)

            return pilots_list

        pilots_on_ground = parse_section("On earth")
        pilots_in_air = parse_section("In air")
        return EuroflyTraffic(pilots_on_ground, pilots_in_air)

    def get_traffic(self) -> EuroflyTraffic:
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

    def get_pilot_profile(self, pilot_id: int) -> PilotProfile:
        """Fetch and parse a pilot's profile."""
        html = self.fetch_pilot_profile_html(pilot_id)
        return self.parse_pilot_profile(html, pilot_id)

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
