#!/usr/bin/env python3
"""
Example demonstrating airplane and airport functionality.

Shows how to fetch and filter airplanes and airports.
"""
from eurofly import EuroflyClient


def main():
    print("=" * 80)
    print("EUROFLY AIRPLANES AND AIRPORTS EXAMPLE")
    print("=" * 80)
    
    client = EuroflyClient()
    
    # === AIRPLANES ===
    print("\n" + "=" * 80)
    print("AIRPLANES")
    print("=" * 80)
    
    print("\nFetching all airplanes...")
    airplanes = client.get_airplanes()
    print(f"Found {len(airplanes)} airplanes")
    
    # Show some examples
    print("\nExample airplanes:")
    for plane in airplanes[:3]:
        print(f"  - {plane.name}")
        print(f"    Passengers: {plane.passengers}, Price: ${plane.price:,}")
        print(f"    Speed: {plane.speed_kmh} km/h, Range: {plane.range_km} km")
    
    # Filter by passengers
    print("\n--- Filtering large airplanes (100+ passengers) ---")
    large_planes = client.filter_airplanes_by_passengers(airplanes, min_passengers=100)
    print(f"Found {len(large_planes)} airplanes with 100+ passengers")
    if large_planes:
        print(f"Example: {large_planes[0].name} - {large_planes[0].passengers} passengers")
    
    # Filter by price
    print("\n--- Filtering affordable airplanes (under $500,000) ---")
    affordable = client.filter_airplanes_by_price(airplanes, max_price=500000)
    print(f"Found {len(affordable)} airplanes under $500,000")
    if affordable:
        print(f"Cheapest: {affordable[0].name} - ${affordable[0].price:,}")
    
    # Filter by category
    print("\n--- Filtering category 1 airplanes ---")
    cat1 = client.filter_airplanes_by_category(airplanes, category=1)
    print(f"Found {len(cat1)} category 1 airplanes")
    
    # === AIRPORTS ===
    print("\n" + "=" * 80)
    print("AIRPORTS")
    print("=" * 80)
    
    print("\nFetching airports in Russia (country_id=151, category=1)...")
    airports = client.get_airports(country_id=151, category=1)
    print(f"Found {len(airports)} airports")
    
    # Show some examples
    print("\nExample airports:")
    for airport in airports[:3]:
        print(f"  - {airport.name} ({airport.code})")
        print(f"    Country: {airport.country}, Category: {airport.category}")
        print(f"    Runways: {airport.runways}, Elevation: {airport.elevation}m")
        if airport.approach_frequency:
            print(f"    Approach frequency: {airport.approach_frequency} MHz")
    
    # Filter by runways
    print("\n--- Filtering airports with runways ---")
    with_runways = client.filter_airports_by_runway_length(airports, min_runways=1)
    print(f"Found {len(with_runways)} airports with at least 1 runway")
    if with_runways:
        print(f"Example: {with_runways[0].name} - {with_runways[0].runways} runway(s)")
    
    # Filter by elevation
    print("\n--- Filtering low-elevation airports (below 200m) ---")
    low_elevation = client.filter_airports_by_elevation(airports, max_elevation=200)
    print(f"Found {len(low_elevation)} airports below 200m elevation")
    if low_elevation:
        print(f"Example: {low_elevation[0].name} - {low_elevation[0].elevation}m")
    
    # === COMBINED FILTERS ===
    print("\n" + "=" * 80)
    print("COMBINED FILTERS")
    print("=" * 80)
    
    print("\n--- Finding suitable airplane-airport combinations ---")
    # Find affordable small planes
    small_affordable = client.filter_airplanes_by_passengers(airplanes, min_passengers=4, max_passengers=10)
    small_affordable = client.filter_airplanes_by_price(small_affordable, max_price=200000)
    
    # Find low-elevation airports with runways
    suitable_airports = client.filter_airports_by_runway_length(airports, min_runways=1)
    suitable_airports = client.filter_airports_by_elevation(suitable_airports, max_elevation=300)
    
    print(f"Found {len(small_affordable)} small affordable planes")
    print(f"Found {len(suitable_airports)} suitable low-elevation airports")
    
    if small_affordable and suitable_airports:
        print(f"\nExample match:")
        print(f"  Plane: {small_affordable[0].name} - {small_affordable[0].passengers} pax, ${small_affordable[0].price:,}")
        print(f"  Airport: {suitable_airports[0].name} - {suitable_airports[0].elevation}m elevation")
    
    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == "__main__":
    main()
