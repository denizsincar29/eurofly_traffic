import httpx
from bs4 import BeautifulSoup
from typing import List, Optional

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

class Pilot:
    def __init__(self, name: str, callsign: str, airline: str, flight: Flight, url: Optional[str]=None):
        self.name = name
        self.callsign = callsign
        self.airline = airline
        self.flight = flight
        self.url = url

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

            h3s = section.find_all_next("h3")
            for h3 in h3s:
                a_tag = h3.find("a")
                if not a_tag or "/ef3/pilot" not in a_tag.get("href", ""):
                    break

                href = a_tag.get("href")
                text = a_tag.get_text(strip=True)

                # Разделяем имя, callsign и авиакомпанию
                if ' - ' in text:
                    name_callsign, airline = text.rsplit(' - ', 1)
                else:
                    name_callsign, airline = text, ""
                if ' ' in name_callsign:
                    name, callsign = name_callsign.rsplit(' ', 1)
                else:
                    name, callsign = name_callsign, ""

                # собираем текстовые линии до следующего h3, учитывая <br>
                flight_lines = []
                sibling = h3.next_sibling
                while sibling and sibling.name != "h3":
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
                    if "Standing at" in line:
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
                pilot = Pilot(name, callsign, airline, flight, url=href)
                pilots_list.append(pilot)

            return pilots_list

        pilots_on_ground = parse_section("On earth")
        pilots_in_air = parse_section("In air")
        return EuroflyTraffic(pilots_on_ground, pilots_in_air)

    def get_traffic(self) -> EuroflyTraffic:
        html = self.fetch_traffic_html()
        return self.parse_traffic(html)

# --- Пример использования ---
if __name__ == "__main__":
    client = EuroflyClient()
    result = client.get_traffic()
    print(result)

    print("\n--- Pilots on ground ---")
    for pilot in result.pilots_on_ground[:10]:
        print(pilot, pilot.flight, pilot.url)

    print("\n--- Pilots in air ---")
    for pilot in result.pilots_in_air[:10]:
        print(pilot, pilot.flight, pilot.url)
