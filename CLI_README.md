# Eurofly CLI

Comprehensive command-line tool for Eurofly traffic monitoring and pilot management.

## Features

### 1. Traffic Monitoring
- **View all traffic**: See all pilots currently online (on ground and in air)
- **Search traffic**: Filter current traffic by name, callsign, aircraft, location, etc.
- **View favorites flying**: See only your favorite pilots who are currently online

### 2. Pilot Search
Search the Eurofly pilot database with multiple options:
- **Search by name**: Find pilots by their name
- **Search by country**: Find pilots from a specific country
- **Search by rank**: Find pilots by their rank level (intraining, novice, captain, etc.)
- **Advanced search**: Combine multiple criteria (name, country, rank)

### 3. Favorites Management
- **Add pilots to favorites**: Mark pilots you want to track
- **Remove from favorites**: Unmark pilots
- **View favorite pilots**: See your complete favorites list with profiles
- **Favorite indicator**: See ⭐ next to favorite pilots in all views

### 4. Pilot Profiles
View detailed pilot information including:
- Bio/description
- Current flight status (if flying)
- Rank and overall rank
- Personal info (country, language, age)
- Statistics (flights, distance, flight time)
- Points and earnings
- Registration and activity dates

### 5. Pilot Watcher
Watch a specific pilot in real-time:
- Refreshes every 15 seconds
- Shows current status, aircraft, location, route
- Automatically stops if pilot goes offline
- Press Ctrl+C to stop manually

## Usage

### Starting the CLI

```bash
python3 eurofly_cli.py
```

### Main Menu Options

```
1. View all traffic          - See all pilots currently online
2. Search traffic           - Filter current traffic by search term
3. View favorites flying    - See only your favorites who are online
4. Search pilots            - Search the pilot database
5. Manage favorites         - View and manage your favorite pilots
6. Watch pilot              - Monitor a specific pilot in real-time
7. Exit                     - Quit the application
```

### Examples

#### Adding a Pilot to Favorites

1. Choose option 4 (Search pilots)
2. Search by name, country, or rank
3. When results appear, type `f <number>` (e.g., `f 1` to add the first pilot)
4. Pilot is added to favorites with confirmation

#### Viewing Favorites Who Are Flying

1. Choose option 3 (View favorites flying)
2. See all your favorite pilots currently online
3. ⭐ marker shows they're in your favorites

#### Watching a Pilot

1. Choose option 6 (Watch pilot)
2. Enter the pilot ID
3. See real-time updates every 15 seconds
4. Press Ctrl+C to stop watching

#### Viewing a Pilot Profile

1. Search for a pilot (option 4)
2. Enter the pilot number from results
3. See complete profile including:
   - Bio/description
   - Current flight (if flying)
   - Statistics and history
4. Option to add/remove from favorites

## Favorites Storage

Favorites are stored in: `~/.eurofly_favorites.json`

This file persists between sessions, so your favorites are saved permanently.

## Flight Type Display

The CLI correctly identifies and displays flight types:
- **FRE**: Free flight
- **COF**: Company flight
- **CHF**: Charter flight
- **BCF**: Business cargo flight
- **BTF**: Business transport flight
- **MAF**: MAF flight

## Tips

- Use search to quickly find pilots by name or location
- Add frequently watched pilots to favorites for easy access
- Use "View favorites flying" to see if your friends are online
- The pilot watcher is great for monitoring a specific flight
- Profiles show both historical stats and current flight status

## Previous Scripts Consolidated

This CLI replaces the following individual scripts:
- `main.py` - Basic traffic viewing
- `pilot_search.py` - Pilot database search
- `language_filter.py` - Language/country filtering
- `watcher.py` - Real-time pilot monitoring

All functionality is now in one comprehensive tool with an easy-to-use menu interface.
