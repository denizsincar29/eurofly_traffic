#!/usr/bin/env python3
"""MCP Server for Eurofly Traffic Library.

This server exposes all Eurofly capabilities through the Model Context Protocol.
"""

from mcp.server import FastMCP
from typing import Optional
import os

from eurofly import EuroflyClient, EuroflyTraffic

# Initialize FastMCP server
mcp = FastMCP("Eurofly Traffic")

# Global client instance
client = EuroflyClient()

# Cache directory for storing traffic snapshots
CACHE_DIR = os.path.expanduser("~/.eurofly_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


@mcp.tool()
def get_traffic() -> str:
    """Fetch current traffic from Eurofly and return summary.
    
    Returns:
        Summary of current traffic including pilot counts and timestamp.
    """
    traffic = client.get_traffic()
    
    result = f"Traffic at {traffic.timestamp}\n"
    result += f"Total pilots: {len(traffic.all_pilots)}\n"
    result += f"  - On ground: {len(traffic.pilots_on_ground)}\n"
    result += f"  - In air: {len(traffic.pilots_in_air)}\n"
    
    return result


@mcp.tool()
def get_all_pilots() -> str:
    """Get list of all currently online pilots with their status.
    
    Returns:
        Formatted list of all pilots with their current status and location.
    """
    traffic = client.get_traffic()
    
    result = f"All Pilots ({len(traffic.all_pilots)} online)\n"
    result += "=" * 80 + "\n\n"
    
    for pilot in traffic.all_pilots:
        result += f"{pilot.name} ({pilot.callsign}) - {pilot.airline}\n"
        if pilot.flight.description:
            result += f"  Description: {pilot.flight.description}\n"
        result += f"  Status: {pilot.flight.status}\n"
        if pilot.flight.aircraft:
            result += f"  Aircraft: {pilot.flight.aircraft}\n"
        if pilot.flight.location_from:
            result += f"  From: {pilot.flight.location_from}\n"
        if pilot.flight.location_to:
            result += f"  To: {pilot.flight.location_to}\n"
        if pilot.flight.last_position:
            result += f"  Last Position: {pilot.flight.last_position}\n"
        result += "\n"
    
    return result


@mcp.tool()
def filter_pilots_by_status(status: str) -> str:
    """Filter pilots by their flight status.
    
    Args:
        status: Flight status to filter by (Standing, Rolling, Taking off, In air, Crashed)
    
    Returns:
        List of pilots matching the status.
    """
    traffic = client.get_traffic()
    pilots = traffic.filter_by_status(status)
    
    result = f"Pilots with status '{status}' ({len(pilots)} found)\n"
    result += "=" * 80 + "\n\n"
    
    for pilot in pilots:
        result += f"{pilot.name} ({pilot.callsign})\n"
        if pilot.flight.location_from:
            result += f"  At: {pilot.flight.location_from}\n"
        result += "\n"
    
    return result


@mcp.tool()
def filter_pilots_by_name(name: str) -> str:
    """Search for pilots by name (case-insensitive partial match).
    
    Args:
        name: Name or partial name to search for
    
    Returns:
        List of matching pilots with their details.
    """
    traffic = client.get_traffic()
    pilots = traffic.filter_by_name(name)
    
    result = f"Pilots matching '{name}' ({len(pilots)} found)\n"
    result += "=" * 80 + "\n\n"
    
    for pilot in pilots:
        result += f"{pilot.name} ({pilot.callsign}) - {pilot.airline}\n"
        if pilot.flight.description:
            result += f"  Description: {pilot.flight.description}\n"
        result += f"  Status: {pilot.flight.status}\n"
        if pilot.flight.location_from:
            result += f"  From: {pilot.flight.location_from}\n"
        if pilot.flight.location_to:
            result += f"  To: {pilot.flight.location_to}\n"
        if pilot.flight.last_position:
            result += f"  Last Position: {pilot.flight.last_position}\n"
        result += "\n"
    
    return result


@mcp.tool()
def filter_pilots_by_location(location: str) -> str:
    """Search for pilots by location (departure, destination, or current position).
    
    Args:
        location: Location name or partial name to search for
    
    Returns:
        List of pilots related to that location.
    """
    traffic = client.get_traffic()
    pilots = traffic.filter_by_location(location)
    
    result = f"Pilots related to '{location}' ({len(pilots)} found)\n"
    result += "=" * 80 + "\n\n"
    
    for pilot in pilots:
        result += f"{pilot.name} ({pilot.callsign})\n"
        result += f"  Status: {pilot.flight.status}\n"
        if pilot.flight.location_from:
            result += f"  From: {pilot.flight.location_from}\n"
        if pilot.flight.location_to:
            result += f"  To: {pilot.flight.location_to}\n"
        if pilot.flight.last_position:
            result += f"  Last Position: {pilot.flight.last_position}\n"
        result += "\n"
    
    return result


@mcp.tool()
def get_pilot_info(pilot_name: str) -> str:
    """Get detailed information about a specific pilot including their profile.
    
    Args:
        pilot_name: Name of the pilot to look up
    
    Returns:
        Detailed pilot information including profile stats.
    """
    traffic = client.get_traffic()
    pilots = traffic.filter_by_name(pilot_name)
    
    if not pilots:
        return f"No pilot found with name '{pilot_name}'"
    
    pilot = pilots[0]
    result = f"Pilot Information: {pilot.name}\n"
    result += "=" * 80 + "\n\n"
    
    result += f"Callsign: {pilot.callsign}\n"
    result += f"Airline: {pilot.airline}\n"
    
    if pilot.flight.description:
        result += f"Description: {pilot.flight.description}\n"
    
    result += f"\nCurrent Flight:\n"
    result += f"  Status: {pilot.flight.status}\n"
    if pilot.flight.aircraft:
        result += f"  Aircraft: {pilot.flight.aircraft}\n"
    if pilot.flight.passengers:
        result += f"  Passengers: {pilot.flight.passengers}\n"
    if pilot.flight.location_from:
        result += f"  From: {pilot.flight.location_from}\n"
    if pilot.flight.location_to:
        result += f"  To: {pilot.flight.location_to}\n"
    if pilot.flight.last_position:
        result += f"  Last Position: {pilot.flight.last_position}\n"
    
    # Try to get full profile
    if pilot.pilot_id:
        try:
            profile = pilot.get_info()
            result += f"\nProfile Statistics:\n"
            if profile.rank:
                result += f"  Rank: {profile.rank}\n"
            if profile.overall_rank:
                result += f"  Overall Rank: {profile.overall_rank}\n"
            if profile.flights_overall:
                result += f"  Total Flights: {profile.flights_overall}\n"
            if profile.total_distance_km:
                result += f"  Total Distance: {profile.total_distance_km:,} km\n"
            if profile.total_flight_time:
                result += f"  Total Flight Time: {profile.total_flight_time}\n"
            if profile.points:
                result += f"  Points: {profile.points:,}\n"
        except Exception as e:
            result += f"\nCould not fetch profile: {e}\n"
    
    return result


@mcp.tool()
def save_traffic_snapshot(filename: Optional[str] = None) -> str:
    """Save current traffic to a cache file for later comparison.
    
    Args:
        filename: Optional filename (defaults to timestamp-based name)
    
    Returns:
        Confirmation message with file path.
    """
    traffic = client.get_traffic()
    
    if filename is None:
        filename = f"traffic_{traffic.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    
    filepath = os.path.join(CACHE_DIR, filename)
    traffic.to_cache(filepath)
    
    return f"Traffic snapshot saved to {filepath}\n{len(traffic.all_pilots)} pilots saved."


@mcp.tool()
def compare_traffic_snapshots(old_filename: str, new_filename: Optional[str] = None) -> str:
    """Compare two traffic snapshots to detect changes.
    
    Args:
        old_filename: Filename of the older snapshot
        new_filename: Filename of newer snapshot (if None, fetches current traffic)
    
    Returns:
        Summary of changes between the snapshots.
    """
    old_path = os.path.join(CACHE_DIR, old_filename)
    
    if not os.path.exists(old_path):
        return f"Error: Snapshot file '{old_filename}' not found in {CACHE_DIR}"
    
    old_traffic = EuroflyTraffic.from_cache(old_path)
    
    if new_filename:
        new_path = os.path.join(CACHE_DIR, new_filename)
        if not os.path.exists(new_path):
            return f"Error: Snapshot file '{new_filename}' not found in {CACHE_DIR}"
        new_traffic = EuroflyTraffic.from_cache(new_path)
    else:
        new_traffic = client.get_traffic()
    
    diff = new_traffic.compare(old_traffic)
    
    result = f"Traffic Comparison\n"
    result += f"Old snapshot: {old_traffic.timestamp}\n"
    result += f"New snapshot: {new_traffic.timestamp}\n"
    result += "=" * 80 + "\n\n"
    
    result += f"New pilots online: {len(diff['new_pilots'])}\n"
    if diff['new_pilots']:
        for pilot in diff['new_pilots']:
            result += f"  + {pilot.name} ({pilot.callsign})\n"
    
    result += f"\nPilots went offline: {len(diff['departed_pilots'])}\n"
    if diff['departed_pilots']:
        for pilot in diff['departed_pilots']:
            result += f"  - {pilot.name} ({pilot.callsign})\n"
    
    result += f"\nPilots with changes: {len(diff['changed_pilots'])}\n"
    if diff['changed_pilots']:
        for item in diff['changed_pilots']:
            pilot = item['pilot']
            changes = item['changes']
            result += f"\n  {pilot.name} ({pilot.callsign}):\n"
            for key, change in changes.items():
                result += f"    {key}: {change['old']} → {change['new']}\n"
    
    return result


@mcp.tool()
def search_pilots(query: str) -> str:
    """Search for pilots in the Eurofly database by name.
    
    Args:
        query: Name or partial name to search for in the database
    
    Returns:
        List of pilot IDs and names matching the query.
    """
    results = client.search_pilots(query)
    
    result = f"Pilot search results for '{query}' ({len(results)} found)\n"
    result += "=" * 80 + "\n\n"
    
    for pilot_id, name in results:
        result += f"ID: {pilot_id} - {name}\n"
    
    return result


@mcp.tool()
def get_pilot_profile(pilot_id: int) -> str:
    """Get detailed profile for a pilot by their ID.
    
    Args:
        pilot_id: The pilot's unique ID
    
    Returns:
        Complete profile information for the pilot.
    """
    try:
        profile = client.get_pilot_profile(pilot_id)
        
        result = f"Pilot Profile: {profile.name}\n"
        result += "=" * 80 + "\n\n"
        
        result += f"Pilot ID: {profile.pilot_id}\n"
        if profile.rank:
            result += f"Rank: {profile.rank} (#{profile.rank_number})\n"
        if profile.overall_rank:
            result += f"Overall Rank: #{profile.overall_rank}\n"
        if profile.country:
            result += f"Country: {profile.country}\n"
        if profile.age:
            result += f"Age: {profile.age}\n"
        
        result += f"\nStatistics:\n"
        if profile.flights_overall:
            result += f"  Flights: {profile.flights_overall}\n"
        if profile.total_distance_km:
            result += f"  Distance: {profile.total_distance_km:,} km\n"
        if profile.total_flight_time:
            result += f"  Flight Time: {profile.total_flight_time}\n"
        if profile.points:
            result += f"  Points: {profile.points:,}\n"
        if profile.earnings:
            result += f"  Earnings: ${profile.earnings:,}\n"
        
        if profile.registered:
            result += f"\nRegistered: {profile.registered}\n"
        if profile.last_login:
            result += f"Last Login: {profile.last_login}\n"
        if profile.last_flight:
            result += f"Last Flight: {profile.last_flight}\n"
        
        return result
    except Exception as e:
        return f"Error fetching profile for pilot ID {pilot_id}: {e}"


@mcp.tool()
def list_cache_snapshots() -> str:
    """List all saved traffic snapshots in the cache directory.
    
    Returns:
        List of available snapshot files with timestamps.
    """
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.json')]
    files.sort(reverse=True)  # Most recent first
    
    result = f"Saved Traffic Snapshots ({len(files)} found)\n"
    result += f"Cache directory: {CACHE_DIR}\n"
    result += "=" * 80 + "\n\n"
    
    for filename in files:
        filepath = os.path.join(CACHE_DIR, filename)
        size = os.path.getsize(filepath)
        result += f"{filename} ({size:,} bytes)\n"
    
    return result


@mcp.tool()
def get_all_airplanes(sort_by: Optional[str] = None) -> str:
    """Get list of all available private airplanes in Eurofly.
    
    Args:
        sort_by: Optional sort parameter (name, cat, type, thrust, eng, pas, speed, range, height, price, qual)
    
    Returns:
        Formatted list of all airplanes with their specifications.
    """
    airplanes = client.get_airplanes(sort_by=sort_by)
    
    result = f"Private Airplanes in Eurofly ({len(airplanes)} total)\n"
    result += "=" * 80 + "\n\n"
    
    for plane in airplanes:
        result += f"{plane.name}\n"
        result += f"  Category: {plane.category}, Type: {plane.type}\n"
        result += f"  Passengers: {plane.passengers}, Engines: {plane.engines} ({plane.propulsion_type})\n"
        result += f"  Speed: {plane.speed_kmh} km/h, Range: {plane.range_km} km\n"
        result += f"  Cruising altitude: {plane.cruising_altitude_m}m\n"
        result += f"  Price: ${plane.price:,}, Qualification: ${plane.qualification_price}\n"
        result += "\n"
    
    return result


@mcp.tool()
def find_airplanes_by_passengers(min_passengers: int, max_passengers: Optional[int] = None) -> str:
    """Find airplanes by passenger capacity range.
    
    Args:
        min_passengers: Minimum number of passengers
        max_passengers: Maximum number of passengers (optional)
    
    Returns:
        List of airplanes matching the passenger capacity criteria.
    """
    airplanes = client.get_airplanes()
    filtered = client.filter_airplanes_by_passengers(airplanes, min_passengers, max_passengers)
    
    result = f"Airplanes with {min_passengers}"
    if max_passengers:
        result += f"-{max_passengers}"
    else:
        result += "+"
    result += f" passengers ({len(filtered)} found)\n"
    result += "=" * 80 + "\n\n"
    
    for plane in filtered:
        result += f"{plane.name} - {plane.passengers} passengers, ${plane.price:,}\n"
    
    return result


@mcp.tool()
def find_airplanes_by_price(max_price: int) -> str:
    """Find airplanes within a budget.
    
    Args:
        max_price: Maximum price in dollars
    
    Returns:
        List of airplanes under the specified price.
    """
    airplanes = client.get_airplanes()
    filtered = client.filter_airplanes_by_price(airplanes, max_price)
    
    result = f"Airplanes under ${max_price:,} ({len(filtered)} found)\n"
    result += "=" * 80 + "\n\n"
    
    for plane in filtered:
        result += f"{plane.name}\n"
        result += f"  Price: ${plane.price:,}, Passengers: {plane.passengers}\n"
        result += f"  Speed: {plane.speed_kmh} km/h, Range: {plane.range_km} km\n"
        result += "\n"
    
    return result


@mcp.tool()
def find_airplanes_by_category(category: int) -> str:
    """Find airplanes in a specific category.
    
    Args:
        category: Category number (1-7)
    
    Returns:
        List of airplanes in the specified category.
    """
    airplanes = client.get_airplanes()
    filtered = client.filter_airplanes_by_category(airplanes, category)
    
    result = f"Category {category} Airplanes ({len(filtered)} found)\n"
    result += "=" * 80 + "\n\n"
    
    for plane in filtered:
        result += f"{plane.name} - {plane.passengers} pax, ${plane.price:,}\n"
    
    return result


@mcp.tool()
def get_airports(country_id: Optional[int] = None, category: Optional[int] = None) -> str:
    """Get list of airports, optionally filtered by country and category.
    
    Args:
        country_id: Optional country ID to filter by (e.g., 151 for Russia)
        category: Optional category to filter by (1-7)
    
    Returns:
        Formatted list of airports with their details.
    """
    airports = client.get_airports(country_id=country_id, category=category)
    
    result = f"Airports ({len(airports)} found)\n"
    if country_id:
        result += f"Country ID: {country_id}\n"
    if category:
        result += f"Category: {category}\n"
    result += "=" * 80 + "\n\n"
    
    for airport in airports:
        result += f"{airport.name}"
        if airport.code:
            result += f" ({airport.code})"
        result += "\n"
        if airport.country:
            result += f"  Country: {airport.country}"
            if airport.region:
                result += f", Region: {airport.region}"
            result += "\n"
        if airport.category:
            result += f"  Category: {airport.category}"
        if airport.difficulty:
            result += f", Difficulty: {airport.difficulty}"
        if airport.category or airport.difficulty:
            result += "\n"
        if airport.runways is not None:
            result += f"  Runways: {airport.runways}"
        if airport.elevation is not None:
            result += f", Elevation: {airport.elevation}m"
        if airport.runways is not None or airport.elevation is not None:
            result += "\n"
        if airport.approach_frequency:
            result += f"  Approach frequency: {airport.approach_frequency} MHz\n"
        result += "\n"
    
    return result


@mcp.tool()
def find_airports_with_runways(min_runways: int = 1, country_id: Optional[int] = None, category: Optional[int] = None) -> str:
    """Find airports with at least a certain number of runways.
    
    Args:
        min_runways: Minimum number of runways (default: 1)
        country_id: Optional country ID to filter by
        category: Optional category to filter by (1-7)
    
    Returns:
        List of airports with sufficient runways.
    """
    airports = client.get_airports(country_id=country_id, category=category)
    filtered = client.filter_airports_by_runway_length(airports, min_runways)
    
    result = f"Airports with {min_runways}+ runway(s) ({len(filtered)} found)\n"
    result += "=" * 80 + "\n\n"
    
    for airport in filtered:
        result += f"{airport.name}"
        if airport.code:
            result += f" ({airport.code})"
        result += f" - {airport.runways} runway(s)\n"
        if airport.elevation is not None:
            result += f"  Elevation: {airport.elevation}m\n"
    
    return result


@mcp.tool()
def find_airports_by_elevation(max_elevation: int, country_id: Optional[int] = None, category: Optional[int] = None) -> str:
    """Find airports below a certain elevation.
    
    Args:
        max_elevation: Maximum elevation in meters
        country_id: Optional country ID to filter by
        category: Optional category to filter by (1-7)
    
    Returns:
        List of airports below the specified elevation.
    """
    airports = client.get_airports(country_id=country_id, category=category)
    filtered = client.filter_airports_by_elevation(airports, max_elevation)
    
    result = f"Airports below {max_elevation}m elevation ({len(filtered)} found)\n"
    result += "=" * 80 + "\n\n"
    
    for airport in filtered:
        result += f"{airport.name}"
        if airport.code:
            result += f" ({airport.code})"
        result += f" - {airport.elevation}m\n"
        if airport.runways is not None:
            result += f"  Runways: {airport.runways}\n"
    
    return result


@mcp.tool()
def find_smallest_runway_airplane() -> str:
    """Find the airplane that requires the smallest runway.
    
    This is a convenience function that helps answer questions like
    "what airplane requires the smallest runway?"
    
    Returns:
        Information about airplanes suitable for small runways.
    """
    airplanes = client.get_airplanes()
    
    # Category 1 airplanes typically require smaller runways
    # Also consider smaller passenger counts and lower speeds
    cat1 = client.filter_airplanes_by_category(airplanes, category=1)
    
    # Sort by passengers (smaller planes need smaller runways)
    cat1_sorted = sorted(cat1, key=lambda x: (x.passengers, x.speed_kmh))
    
    result = "Airplanes Suitable for Small Runways\n"
    result += "=" * 80 + "\n\n"
    result += "Category 1 airplanes with smallest capacity (best for small runways):\n\n"
    
    for plane in cat1_sorted[:10]:  # Top 10
        result += f"{plane.name}\n"
        result += f"  Passengers: {plane.passengers}, Speed: {plane.speed_kmh} km/h\n"
        result += f"  Range: {plane.range_km} km, Price: ${plane.price:,}\n"
        result += "\n"
    
    return result


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
