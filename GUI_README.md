# Eurofly GUI - Native Desktop Application

A native wxPython GUI application for monitoring Eurofly flight traffic. Fully accessible with screenreaders.

## Features

### 🛫 Current Traffic Tab
- View all pilots currently flying
- Real-time traffic display
- Filter by favorites only
- Search by any field (name, callsign, aircraft, location)
- Refresh button for latest data
- Double-click to view pilot profile
- Right-click context menu for favorites management

### 🔍 Search Pilots Tab
- Search by name, country, or rank
- Combine multiple search criteria
- View search results in sortable table
- Add/remove favorites from search results
- Double-click to view detailed profile

### ⭐ Favorites Tab
- View all your favorite pilots
- See their profiles and statistics
- Remove pilots from favorites
- Refresh to update information

### 👤 Pilot Profile Dialog
- Complete pilot information display
- Bio/description at the top (with 📝 emoji)
- Current flight status (if flying)
- Personal information (country, language, age)
- Rank and statistics
- Flight history
- Add/remove from favorites

## Installation

wxPython is now included as a main dependency, so it will be installed automatically when you install the library.

### Install the library

```bash
pip install -e .
```

Or with uv:
```bash
uv pip install -e .
```

**Note:** If you encounter issues with wxPython installation on Linux, you may need to install system dependencies:

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install libgtk-3-dev python3-dev
pip install wxPython
```

**macOS/Windows:**
wxPython should install without additional dependencies.

## Usage

### Running the GUI

```bash
python3 eurofly_gui.py
```

Or if installed as a script:
```bash
eurofly-gui
```

## Accessibility

The GUI is designed to be fully accessible with screenreaders:

- **Keyboard Navigation**: All features accessible via keyboard
  - Tab: Move between controls
  - Arrow keys: Navigate lists
  - Enter: Activate item
  - Space: Toggle checkboxes
  - Ctrl+R: Refresh
  - Ctrl+Q: Exit

- **Screenreader Support**: 
  - All controls have proper labels
  - Lists announce content correctly
  - Status messages are announced
  - Context menus are accessible

- **Native Controls**: Uses native OS controls for best compatibility

## Features in Detail

### Traffic Monitoring
1. Click "Refresh Traffic" to load current flights
2. Use "Show Favorites Only" checkbox to filter
3. Type in search box to filter by any field
4. Double-click any pilot to see full profile
5. Right-click for quick favorites management

### Pilot Search
1. Enter name (partial match works)
2. Select country from dropdown (optional)
3. Select rank from dropdown (optional)
4. Click "Search" button
5. Results appear in table
6. Double-click to view profile

### Managing Favorites
- **Add to favorites**: Right-click pilot → "Add to Favorites"
- **Remove from favorites**: Right-click pilot → "Remove from Favorites"
- **View all favorites**: Go to "Favorites" tab
- **Favorites indicator**: ⭐ shows next to favorite pilots

Favorites are stored in `~/.eurofly_favorites.json` and persist between sessions.

### Viewing Profiles
When you double-click a pilot or click "View Profile":
- See complete bio/description
- View current flight status (if flying)
- See all statistics and history
- Add/remove from favorites
- All information in readable format

## Keyboard Shortcuts

- `Ctrl+R` - Refresh current view
- `Ctrl+Q` - Exit application
- `Enter` - Activate selected item
- `Tab` - Move to next control
- `Shift+Tab` - Move to previous control
- `Arrow keys` - Navigate lists
- `F10` - Open menu bar

## Tips

1. **Refresh Regularly**: Click refresh button to see latest traffic
2. **Use Favorites**: Add pilots you follow often for quick access
3. **Context Menus**: Right-click on any pilot for quick actions
4. **Search Tips**: Partial name matches work (e.g., "deniz" finds "Deniz Sincar")
5. **Multiple Tabs**: Switch between tabs with Ctrl+Tab

## Troubleshooting

### wxPython Installation Issues

**Linux**: If pip install fails, install system package:
```bash
sudo apt-get install python3-wxgtk4.0
```

**Windows**: Ensure you have Visual C++ redistributables installed

**macOS**: May need to install from wheel:
```bash
pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04 wxPython
```

### GUI Not Starting

1. Check wxPython is installed:
   ```bash
   python3 -c "import wx; print(wx.version())"
   ```

2. Check library is installed:
   ```bash
   python3 -c "from eurofly import EuroflyClient"
   ```

3. Run with error output:
   ```bash
   python3 eurofly_gui.py 2>&1 | tee gui.log
   ```

## Comparison with CLI

| Feature | CLI | GUI |
|---------|-----|-----|
| View traffic | ✅ | ✅ |
| Search pilots | ✅ | ✅ |
| Manage favorites | ✅ | ✅ |
| View profiles | ✅ | ✅ |
| Watch pilot | ✅ | ❌ |
| Screenreader accessible | ✅ | ✅ |
| Mouse support | ❌ | ✅ |
| Multiple views | Sequential | Tabs |
| Startup time | Fast | Moderate |

## Future Enhancements

Planned features:
- Real-time pilot watcher tab
- Airplanes and airports browser
- Flight history visualization
- Map view of current flights
- Notifications for favorite pilots
- Dark mode support

## Support

For issues or questions:
- GitHub: https://github.com/denizsincar29/eurofly_traffic
- Eurofly: https://eurofly.stefankiss.sk
