#!/usr/bin/env python3
"""
Pilot Search Tool - Search for pilots using various criteria
"""
from eurofly import EuroflyClient

# Common country IDs from the pilots page
COUNTRIES = {
    1: "Algeria",
    15: "Egypt",
    36: "Morocco",
    46: "South Africa",
    51: "Afghanistan",
    61: "China",
    67: "India",
    72: "Indonesia",
    73: "Iran",
    75: "Israel",
    76: "Japan",
    83: "Pakistan",
    88: "Saudi Arabia",
    94: "Turkey",
    105: "Austria",
    107: "Belarus",
    108: "Belgium",
    113: "Czech Republic",
    115: "Denmark",
    118: "France",
    119: "Germany",
    122: "Greece",
    123: "Hungary",
    126: "Ireland",
    127: "Italy",
    131: "Netherlands",
    133: "Norway",
    134: "Poland",
    135: "Portugal",
    136: "Romania",
    137: "Russia",
    138: "Serbia",
    139: "Slovakia",
    141: "Spain",
    142: "Sweden",
    143: "Switzerland",
    144: "Ukraine",
    145: "United Kingdom",
    159: "USA",
}

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
    
    print("\nAvailable countries:")
    print("(Showing common countries - see full list at https://eurofly.stefankiss.sk/ef3/pilots)\n")
    
    # Display countries in columns
    country_list = list(COUNTRIES.items())
    for i in range(0, len(country_list), 3):
        row = country_list[i:i+3]
        print("  ".join([f"{cid:3d}. {name:20s}" for cid, name in row]))
    
    try:
        country_id = int(input("\nEnter country ID: ").strip())
    except ValueError:
        print("Invalid country ID.")
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
        print("  4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            search_by_name()
        elif choice == "2":
            search_by_country()
        elif choice == "3":
            search_by_rank()
        elif choice == "4":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")


if __name__ == "__main__":
    main()
