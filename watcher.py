#!/usr/bin/env python3
"""
Eurofly Traffic Watcher

A simple tool that monitors a specific pilot's flight status and prints changes.
Checks for updates every 15 seconds.
"""

from eurofly import EuroflyClient
from eurofly.models import EuroflyTraffic
import time
import sys
from datetime import datetime


def format_pilot_status(pilot):
    """Format pilot status for display."""
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"{pilot.name} ({pilot.callsign}) - {pilot.airline}")
    lines.append(f"{'='*80}")
    
    if pilot.flight.description:
        lines.append(f"Description: {pilot.flight.description}")
    
    lines.append(f"Status: {pilot.flight.status}")
    
    if pilot.flight.aircraft:
        lines.append(f"Aircraft: {pilot.flight.aircraft}")
    
    if pilot.flight.passengers:
        lines.append(f"Passengers: {pilot.flight.passengers}")
    
    if pilot.flight.location_from:
        lines.append(f"From: {pilot.flight.location_from}")
    
    if pilot.flight.location_to:
        lines.append(f"To: {pilot.flight.location_to}")
    
    if pilot.flight.last_position:
        lines.append(f"Last Position: {pilot.flight.last_position}")
    
    return "\n".join(lines)


def print_change(field, old_value, new_value):
    """Print a change in a formatted way."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 🔔 CHANGE DETECTED:")
    print(f"  {field}: {old_value} → {new_value}")
    
    # Special messages for common transitions
    if field == "status":
        if new_value == "Rolling":
            print("  📍 Pilot is now taxiing")
        elif new_value == "Taking off":
            print("  🛫 Pilot is taking off!")
        elif new_value == "In air":
            print("  ✈️  Pilot is now in the air")
        elif new_value == "Standing":
            print("  🛬 Pilot has landed/stopped")
    elif field == "last_position":
        print("  📍 Position updated")


def watch_pilot(client, pilot_name):
    """Watch a specific pilot and print changes."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"\n{'='*80}")
    print(f"[{timestamp}] Watching: {pilot_name}")
    print(f"[{timestamp}] Checking every 15 seconds... (Press Ctrl+C to stop)")
    print(f"{'='*80}")
    
    # Get initial state
    traffic = client.get_traffic()
    pilots = traffic.filter_by_name(pilot_name)
    
    if not pilots:
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] ❌ No pilot found matching '{pilot_name}'")
        return
    
    current_pilot = pilots[0]
    pilot_id = current_pilot.pilot_id
    
    if not pilot_id:
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] ⚠️  Warning: Pilot has no ID. Tracking by name only.")
    
    # Display initial status
    print(format_pilot_status(current_pilot))
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{timestamp}] ⏰ Started watching")
    
    check_count = 0
    
    try:
        while True:
            # Wait 15 seconds
            time.sleep(15)
            check_count += 1
            
            # Fetch new traffic
            new_traffic = client.get_traffic()
            
            # Find the pilot (by ID if available, otherwise by name)
            if pilot_id:
                new_pilot = new_traffic.get_pilot_by_id(pilot_id)
            else:
                new_pilots = new_traffic.filter_by_name(pilot_name)
                new_pilot = new_pilots[0] if new_pilots else None
            
            if not new_pilot:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{timestamp}] ⚠️  Pilot went offline")
                print(f"[{timestamp}] Waiting for pilot to come back online...")
                continue
            
            # Check for changes
            changes_detected = False
            
            # Check status change
            if current_pilot.flight.status != new_pilot.flight.status:
                print_change("status", current_pilot.flight.status, new_pilot.flight.status)
                changes_detected = True
            
            # Check position change
            if current_pilot.flight.last_position != new_pilot.flight.last_position:
                print_change("last_position", current_pilot.flight.last_position, new_pilot.flight.last_position)
                changes_detected = True
            
            # Check location_from change
            if current_pilot.flight.location_from != new_pilot.flight.location_from:
                print_change("location_from", current_pilot.flight.location_from, new_pilot.flight.location_from)
                changes_detected = True
            
            # Check location_to change
            if current_pilot.flight.location_to != new_pilot.flight.location_to:
                print_change("location_to", current_pilot.flight.location_to, new_pilot.flight.location_to)
                changes_detected = True
            
            # Check passengers change
            if current_pilot.flight.passengers != new_pilot.flight.passengers:
                print_change("passengers", current_pilot.flight.passengers, new_pilot.flight.passengers)
                changes_detected = True
            
            # Check aircraft change
            if current_pilot.flight.aircraft != new_pilot.flight.aircraft:
                print_change("aircraft", current_pilot.flight.aircraft, new_pilot.flight.aircraft)
                changes_detected = True
            
            # Check description change
            if current_pilot.flight.description != new_pilot.flight.description:
                print_change("description", current_pilot.flight.description, new_pilot.flight.description)
                changes_detected = True
            
            if not changes_detected:
                # Print a dot to show we're still watching
                print(".", end="", flush=True)
                if check_count % 20 == 0:  # New line every 20 checks (5 minutes)
                    print(f" [{datetime.now().strftime('%H:%M:%S')}]")
            else:
                # Reset the dot counter after a change
                check_count = 0
            
            # Update current pilot
            current_pilot = new_pilot
            
    except KeyboardInterrupt:
        print(f"\n\n{'='*80}")
        print(f"⏹️  Stopped watching at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}")


def main():
    """Main entry point."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print("="*80)
    print(f"[{timestamp}] Eurofly Traffic Watcher")
    print("="*80)
    
    # Ask for search prompt
    print("\nEnter search prompt (pilot name, callsign, or location):")
    search_prompt = input("> ").strip()
    
    if not search_prompt:
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] ❌ No search prompt provided. Exiting.")
        sys.exit(1)
    
    # Initialize client
    client = EuroflyClient()
    
    # Search for pilots
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"\n[{timestamp}] Searching for '{search_prompt}'...")
    traffic = client.get_traffic()
    
    # Try different search methods
    pilots = traffic.filter_by_name(search_prompt)
    
    if not pilots:
        # Try by callsign
        pilots = traffic.filter_by_callsign(search_prompt)
    
    if not pilots:
        # Try by location
        pilots = traffic.filter_by_location(search_prompt)
    
    if not pilots:
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{timestamp}] ❌ No pilots found matching '{search_prompt}'")
        print(f"[{timestamp}] Try searching for:")
        print(f"[{timestamp}]   - Pilot name (e.g., 'Deniz Sincar')")
        print(f"[{timestamp}]   - Callsign (e.g., 'SK903')")
        print(f"[{timestamp}]   - Location (e.g., 'Murmansk')")
        sys.exit(1)
    
    # Display found pilots
    timestamp = datetime.now().strftime('%H:%M:%S')
    if len(pilots) > 1:
        print(f"\n[{timestamp}] ✓ Found {len(pilots)} pilots matching '{search_prompt}':")
        for i, pilot in enumerate(pilots, 1):
            print(f"[{timestamp}]   {i}. {pilot.name} ({pilot.callsign}) - {pilot.airline}")
            if pilot.flight.status:
                print(f"[{timestamp}]      Status: {pilot.flight.status}")
        
        # Ask which one to watch
        print(f"\nEnter number to watch (1-{len(pilots)}, or press Enter for first):")
        choice = input("> ").strip()
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        if choice:
            try:
                index = int(choice) - 1
                if 0 <= index < len(pilots):
                    selected_pilot = pilots[index]
                else:
                    print(f"[{timestamp}] Invalid choice. Watching first pilot.")
                    selected_pilot = pilots[0]
            except ValueError:
                print(f"[{timestamp}] Invalid input. Watching first pilot.")
                selected_pilot = pilots[0]
        else:
            selected_pilot = pilots[0]
    else:
        selected_pilot = pilots[0]
        print(f"\n[{timestamp}] ✓ Found: {selected_pilot.name} ({selected_pilot.callsign})")
    
    # Start watching
    watch_pilot(client, selected_pilot.name)


if __name__ == "__main__":
    main()
