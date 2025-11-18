"""
Example showing how to enable debug logging for traffic parsing.

This demonstrates the debug logging feature that helps identify
why a status might be parsed as None.
"""
import logging
from eurofly.client import EuroflyClient

# Configure logging to show DEBUG messages
# This will enable the debug logs when status is None
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

def main():
    # Create client and fetch traffic
    client = EuroflyClient()
    
    print("Fetching traffic...")
    traffic = client.get_traffic()
    
    print(f"\nTotal pilots: {len(traffic.all_pilots)}")
    print(f"Pilots on ground: {len(traffic.pilots_on_ground)}")
    print(f"Pilots in air: {len(traffic.pilots_in_air)}")
    
    # Check for pilots with None status
    none_status_pilots = [p for p in traffic.all_pilots if p.flight.status is None]
    print(f"\nPilots with None status: {len(none_status_pilots)}")
    
    if none_status_pilots:
        print("\nPilots with None status:")
        for pilot in none_status_pilots:
            print(f"  - {pilot.name} ({pilot.callsign})")
            print(f"    Description: {pilot.flight.description}")
    else:
        print("\nNo pilots with None status found.")
    
    print("\nNote: If any pilot has status=None, debug logs above will show:")
    print("  - The HTML context for that pilot")
    print("  - All parsed lines")
    print("  - Unrecognized lines that might need parser rules")

if __name__ == "__main__":
    main()
