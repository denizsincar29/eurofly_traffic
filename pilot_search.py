#!/usr/bin/env python3
"""
Pilot Search Tool - Search for pilots using various criteria
"""
from eurofly import EuroflyClient

# Full country mapping from the pilots page
COUNTRIES = {
    1: "Algeria",
    5: "Burkina Faso",
    15: "Egypt",
    19: "Ethiopia",
    22: "Ghana",
    23: "Guinea",
    26: "Kenya",
    29: "Libya",
    31: "Malawi",
    36: "Morocco",
    45: "Senegal",
    49: "South Africa",
    54: "Tunisia",
    59: "Afghanistan",
    60: "Armenia",
    61: "Azerbaijan",
    63: "Bangladesh",
    67: "Cambodia",
    68: "Georgia",
    70: "China",
    71: "India",
    72: "Indonesia",
    73: "Iran",
    74: "Iraq",
    75: "Israel",
    76: "Japan",
    77: "Jordan",
    78: "Kazakhstan",
    79: "North Korea",
    80: "South Korea",
    81: "Kuwait",
    84: "Lebanon",
    86: "Malaisia",
    88: "Mongolia",
    89: "Miammar",
    90: "Nepal",
    92: "Pakistan",
    93: "Palestinian Territories",
    94: "Philippines",
    96: "Saudi Arabia",
    97: "Singapore",
    98: "Sri Lanka",
    99: "Syria",
    100: "Taiwan",
    102: "Thailand",
    103: "Turkey",
    106: "Uzbekistan",
    107: "Vietnam",
    108: "Yemen",
    109: "Aland Islands",
    110: "Albania",
    111: "Andorra",
    112: "Austria",
    113: "Belarus",
    114: "Belgium",
    115: "Bosnia and Herzegovina",
    116: "Bulgaria",
    117: "Croatia",
    118: "Cyprus",
    119: "Czech Republic",
    120: "Denmark",
    121: "Estonia",
    123: "Finland",
    124: "France",
    125: "Germany",
    126: "Gibraltar",
    127: "Greece",
    130: "Hungary",
    131: "Iceland",
    132: "Ireland",
    134: "Italy",
    137: "Latvia",
    139: "Lithuania",
    140: "Luxembourg",
    141: "Malta",
    145: "Netherlands",
    146: "North Macedonia",
    147: "Norway",
    148: "Poland",
    149: "Portugal",
    150: "Romania",
    151: "Russia",
    153: "Serbia",
    154: "Slovakia",
    155: "Slovenia",
    156: "Spain",
    158: "Sweden",
    159: "Switzerland",
    160: "Ukraine",
    164: "Aruba",
    167: "Belize",
    172: "Costa Rica",
    173: "Cuba",
    176: "Dominican Republic",
    177: "Salvador",
    179: "Grenada",
    181: "Guatemala",
    183: "Honduras",
    184: "Jamaica",
}

# Reverse mapping for country name to ID lookup
COUNTRY_NAME_TO_ID = {name.lower(): cid for cid, name in COUNTRIES.items()}

# Rank levels
RANKS = {
    1: "intraining",
    2: "novices",
    3: "assistants",
    4: "copilot",
    5: "first pilot",
    6: "captain",
    7: "teacher pilot",
}


def search_by_name():
    """Search pilots by name."""
    print("\n" + "=" * 80)
    print("SEARCH PILOTS BY NAME")
    print("=" * 80)
    
    name = input("\nEnter pilot name (or part of name): ").strip()
    if not name:
        print("No name entered.")
        return
    
    client = EuroflyClient()
    print(f"\nSearching for pilots matching '{name}'...")
    results = client.search_pilots(name)
    
    if results:
        print(f"\nFound {len(results)} pilot(s):\n")
        for i, (pilot_id, pilot_name) in enumerate(results, 1):
            print(f"{i}. {pilot_name} (ID: {pilot_id})")
    else:
        print("\nNo pilots found.")


def search_by_country():
    """Search pilots by country."""
    print("\n" + "=" * 80)
    print("SEARCH PILOTS BY COUNTRY")
    print("=" * 80)
    
    print("\nYou can search by:")
    print("  1. Country name (e.g., 'Russia', 'France', 'USA')")
    print("  2. Country ID (e.g., 151, 124, etc.)")
    print("\nAvailable countries (showing first 20):")
    
    # Display first 20 countries
    country_list = list(COUNTRIES.items())[:20]
    for i in range(0, len(country_list), 3):
        row = country_list[i:i+3]
        print("  ".join([f"{cid:3d}. {name:20s}" for cid, name in row]))
    print(f"\n... and {len(COUNTRIES) - 20} more countries")
    
    user_input = input("\nEnter country name or ID: ").strip()
    if not user_input:
        print("No input provided.")
        return
    
    # Try to parse as ID first
    country_id = None
    try:
        country_id = int(user_input)
        if country_id not in COUNTRIES:
            print(f"Country ID {country_id} not found.")
            return
    except ValueError:
        # Not a number, try as country name
        country_id = COUNTRY_NAME_TO_ID.get(user_input.lower())
        if country_id is None:
            print(f"Country '{user_input}' not found.")
            print("Please check spelling or use country ID.")
            return
    
    client = EuroflyClient()
    country_name = COUNTRIES.get(country_id, f"Country {country_id}")
    print(f"\nSearching for pilots from {country_name}...")
    results = client.search_pilots_by_country(country_id)
    
    if results:
        print(f"\nFound {len(results)} pilot(s):\n")
        for i, (pilot_id, pilot_name) in enumerate(results[:50], 1):  # Limit to 50
            print(f"{i}. {pilot_name} (ID: {pilot_id})")
        if len(results) > 50:
            print(f"\n... and {len(results) - 50} more pilots")
    else:
        print("\nNo pilots found.")


def search_by_rank():
    """Search pilots by rank level."""
    print("\n" + "=" * 80)
    print("SEARCH PILOTS BY RANK")
    print("=" * 80)
    
    print("\nAvailable ranks:")
    for rank_id, rank_name in RANKS.items():
        print(f"  {rank_id}. {rank_name}")
    
    try:
        rank_level = int(input("\nEnter rank level (1-7): ").strip())
        if rank_level not in RANKS:
            print("Invalid rank level.")
            return
    except ValueError:
        print("Invalid rank level.")
        return
    
    client = EuroflyClient()
    rank_name = RANKS[rank_level]
    print(f"\nSearching for pilots with rank '{rank_name}' or higher...")
    results = client.search_pilots_by_rank(rank_level)
    
    if results:
        print(f"\nFound {len(results)} pilot(s):\n")
        for i, (pilot_id, pilot_name) in enumerate(results[:50], 1):  # Limit to 50
            print(f"{i}. {pilot_name} (ID: {pilot_id})")
        if len(results) > 50:
            print(f"\n... and {len(results) - 50} more pilots")
    else:
        print("\nNo pilots found.")


def search_advanced():
    """Search pilots by multiple criteria at once."""
    print("\n" + "=" * 80)
    print("ADVANCED SEARCH - Multiple Criteria")
    print("=" * 80)
    
    print("\nYou can combine multiple search criteria.")
    print("Leave any field empty to skip that criterion.\n")
    
    # Get name
    name = input("Enter pilot name (or press Enter to skip): ").strip()
    name = name if name else None
    
    # Get country
    country_id = None
    country_input = input("Enter country name or ID (or press Enter to skip): ").strip()
    if country_input:
        try:
            country_id = int(country_input)
            if country_id not in COUNTRIES:
                print(f"Warning: Country ID {country_id} not found. Skipping country filter.")
                country_id = None
        except ValueError:
            country_id = COUNTRY_NAME_TO_ID.get(country_input.lower())
            if country_id is None:
                print(f"Warning: Country '{country_input}' not found. Skipping country filter.")
    
    # Get rank
    rank_level = None
    rank_input = input("Enter rank level 1-7 (or press Enter to skip): ").strip()
    if rank_input:
        try:
            rank_level = int(rank_input)
            if rank_level not in RANKS:
                print(f"Warning: Invalid rank level {rank_level}. Skipping rank filter.")
                rank_level = None
        except ValueError:
            print(f"Warning: Invalid rank level. Skipping rank filter.")
    
    # Check if any criteria were provided
    if not any([name, country_id, rank_level]):
        print("\nNo search criteria provided.")
        return
    
    # Build description of search
    criteria = []
    if name:
        criteria.append(f"name containing '{name}'")
    if country_id:
        criteria.append(f"from {COUNTRIES[country_id]}")
    if rank_level:
        criteria.append(f"rank {RANKS[rank_level]} or higher")
    
    print(f"\nSearching for pilots with: {', '.join(criteria)}...")
    
    client = EuroflyClient()
    results = client.search_pilots_advanced(name=name, country_id=country_id, rank_level=rank_level)
    
    if results:
        print(f"\nFound {len(results)} pilot(s):\n")
        for i, (pilot_id, pilot_name) in enumerate(results[:50], 1):
            print(f"{i}. {pilot_name} (ID: {pilot_id})")
        if len(results) > 50:
            print(f"\n... and {len(results) - 50} more pilots")
    else:
        print("\nNo pilots found matching all criteria.")


def main():
    """Main menu for pilot search."""
    while True:
        print("\n" + "=" * 80)
        print("EUROFLY PILOT SEARCH")
        print("=" * 80)
        print("\nSearch options:")
        print("  1. Search by name")
        print("  2. Search by country")
        print("  3. Search by rank")
        print("  4. Advanced search (multiple criteria)")
        print("  5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            search_by_name()
        elif choice == "2":
            search_by_country()
        elif choice == "3":
            search_by_rank()
        elif choice == "4":
            search_advanced()
        elif choice == "5":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    main()
