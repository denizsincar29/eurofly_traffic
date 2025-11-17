#!/usr/bin/env python3
"""
Complete example: Monitor pilot status changes every minute.

This example demonstrates:
1. Traffic caching
2. Comparison/diff functionality
3. Filtering methods
4. Monitoring specific pilots
"""

from eurofly import EuroflyClient
from eurofly.models import EuroflyTraffic
import time
import os

# Initialize client
client = EuroflyClient()

# Cache file
CACHE_FILE = "traffic_cache.json"

def monitor_traffic():
    """Monitor traffic and detect changes."""
    
    # Load previous snapshot if it exists
    if os.path.exists(CACHE_FILE):
        print("Loading previous snapshot...")
        old_traffic = EuroflyTraffic.from_cache(CACHE_FILE)
        print(f"Previous snapshot: {old_traffic.timestamp}")
        print(f"  {len(old_traffic.all_pilots)} pilots\n")
    else:
        old_traffic = None
        print("No previous snapshot found. Starting fresh.\n")
    
    # Fetch current traffic
    print("Fetching current traffic...")
    new_traffic = client.get_traffic()
    print(f"Current traffic: {new_traffic.timestamp}")
    print(f"  {len(new_traffic.all_pilots)} pilots")
    print(f"  On ground: {len(new_traffic.pilots_on_ground)}")
    print(f"  In air: {len(new_traffic.pilots_in_air)}\n")
    
    # Show some stats
    standing = new_traffic.filter_standing()
    rolling = new_traffic.filter_rolling()
    taking_off = new_traffic.filter_taking_off()
    
    print(f"Current status breakdown:")
    print(f"  Standing: {len(standing)}")
    print(f"  Rolling: {len(rolling)}")
    print(f"  Taking off: {len(taking_off)}")
    print(f"  In air: {len(new_traffic.pilots_in_air)}\n")
    
    # If we have a previous snapshot, compare
    if old_traffic:
        print("Comparing with previous snapshot...")
        diff = new_traffic.compare(old_traffic)
        
        print(f"\nChanges detected:")
        print(f"  New pilots online: {len(diff['new_pilots'])}")
        if diff['new_pilots']:
            for pilot in diff['new_pilots']:
                print(f"    + {pilot.name} ({pilot.callsign})")
        
        print(f"  Pilots went offline: {len(diff['departed_pilots'])}")
        if diff['departed_pilots']:
            for pilot in diff['departed_pilots']:
                print(f"    - {pilot.name} ({pilot.callsign})")
        
        print(f"  Pilots with changes: {len(diff['changed_pilots'])}")
        if diff['changed_pilots']:
            for item in diff['changed_pilots'][:5]:  # Show first 5
                pilot = item['pilot']
                changes = item['changes']
                print(f"\n    {pilot.name} ({pilot.callsign}):")
                for key, change in changes.items():
                    print(f"      {key}: {change['old']} → {change['new']}")
    
    # Check specific pilot (example: Deniz Sincar)
    print("\n" + "="*80)
    print("Checking specific pilots:")
    print("="*80)
    
    deniz = new_traffic.filter_by_name("Deniz Sincar")
    if deniz:
        pilot = deniz[0]
        print(f"\n✓ Found: {pilot.name}")
        print(f"  Callsign: {pilot.callsign}")
        print(f"  Status: {pilot.flight.status}")
        if pilot.flight.description:
            print(f"  Description: {pilot.flight.description}")
        if pilot.flight.location_from:
            print(f"  From: {pilot.flight.location_from}")
        if pilot.flight.location_to:
            print(f"  To: {pilot.flight.location_to}")
        if pilot.flight.last_position:
            print(f"  Last Position: {pilot.flight.last_position}")
    else:
        print("\nDeniz Sincar is not currently online")
    
    # Save current snapshot for next comparison
    print("\nSaving current snapshot...")
    new_traffic.to_cache(CACHE_FILE)
    print(f"✓ Saved to {CACHE_FILE}")


if __name__ == "__main__":
    print("="*80)
    print("Eurofly Traffic Monitoring Example")
    print("="*80)
    print()
    
    # Run once
    monitor_traffic()
    
    print("\n" + "="*80)
    print("To monitor continuously, run this script every minute")
    print("Example: */1 * * * * python monitoring_example.py")
    print("="*80)
