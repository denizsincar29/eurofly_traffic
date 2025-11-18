#!/usr/bin/env python3
"""
Eurofly GUI - Native wxPython GUI for Eurofly traffic monitoring.

Screenreader-accessible GUI with all library features:
- View current traffic
- Search for pilots
- Manage favorites
- Watch specific pilots
- View pilot profiles and flight details
- Browse airplanes and airports
"""

import wx
import wx.lib.scrolledpanel as scrolled
import json
import os
import threading
import time
from pathlib import Path
from typing import List, Optional, Set

from eurofly import EuroflyClient, COUNTRIES, RANKS, FLIGHT_TYPES
from eurofly.models import Pilot, PilotProfile, Airplane, Airport


# Favorites file location
FAVORITES_FILE = Path.home() / ".eurofly_favorites.json"


class FavoritesManager:
    """Manage favorite pilots."""
    
    def __init__(self):
        self.favorites: Set[int] = set()
        self.load()
    
    def load(self):
        """Load favorites from file."""
        if FAVORITES_FILE.exists():
            try:
                with open(FAVORITES_FILE, 'r') as f:
                    data = json.load(f)
                    self.favorites = set(data.get('favorites', []))
            except Exception:
                self.favorites = set()
    
    def save(self):
        """Save favorites to file."""
        try:
            with open(FAVORITES_FILE, 'w') as f:
                json.dump({'favorites': list(self.favorites)}, f, indent=2)
        except Exception as e:
            print(f"Error saving favorites: {e}")
    
    def add(self, pilot_id: int) -> bool:
        """Add a pilot to favorites."""
        if pilot_id not in self.favorites:
            self.favorites.add(pilot_id)
            self.save()
            return True
        return False
    
    def remove(self, pilot_id: int) -> bool:
        """Remove a pilot from favorites."""
        if pilot_id in self.favorites:
            self.favorites.discard(pilot_id)
            self.save()
            return True
        return False
    
    def is_favorite(self, pilot_id: int) -> bool:
        """Check if a pilot is a favorite."""
        return pilot_id in self.favorites
    
    def get_all(self) -> List[int]:
        """Get all favorite pilot IDs."""
        return list(self.favorites)


class TrafficPanel(scrolled.ScrolledPanel):
    """Panel showing current traffic."""
    
    def __init__(self, parent, client, favorites_mgr):
        super().__init__(parent)
        self.client = client
        self.favorites_mgr = favorites_mgr
        self.pilots = []
        
        # Main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Controls
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.refresh_btn = wx.Button(self, label="Refresh Traffic")
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        ctrl_sizer.Add(self.refresh_btn, 0, wx.ALL, 5)
        
        self.favorites_only_cb = wx.CheckBox(self, label="Show Favorites Only")
        self.favorites_only_cb.Bind(wx.EVT_CHECKBOX, self.on_filter_changed)
        ctrl_sizer.Add(self.favorites_only_cb, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        ctrl_sizer.Add(wx.StaticText(self, label="Search:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.search_text = wx.TextCtrl(self, size=(200, -1))
        self.search_text.Bind(wx.EVT_TEXT, self.on_filter_changed)
        ctrl_sizer.Add(self.search_text, 0, wx.ALL, 5)
        
        sizer.Add(ctrl_sizer, 0, wx.EXPAND)
        
        # Pilots list
        self.pilots_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.pilots_list.InsertColumn(0, "Favorite", width=60)
        self.pilots_list.InsertColumn(1, "Pilot", width=150)
        self.pilots_list.InsertColumn(2, "Callsign", width=80)
        self.pilots_list.InsertColumn(3, "Status", width=100)
        self.pilots_list.InsertColumn(4, "Aircraft", width=150)
        self.pilots_list.InsertColumn(5, "From", width=150)
        self.pilots_list.InsertColumn(6, "To", width=150)
        self.pilots_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_pilot_activated)
        self.pilots_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_pilot_context)
        
        sizer.Add(self.pilots_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Status bar
        self.status_text = wx.StaticText(self, label="Ready")
        sizer.Add(self.status_text, 0, wx.ALL, 5)
        
        self.SetSizer(sizer)
        self.SetupScrolling()
        
        # Load traffic on startup
        wx.CallAfter(self.load_traffic)
    
    def load_traffic(self):
        """Load traffic in background."""
        self.status_text.SetLabel("Loading traffic...")
        self.refresh_btn.Enable(False)
        
        def load():
            try:
                self.pilots = self.client.get_traffic()
                wx.CallAfter(self.update_display)
            except Exception as e:
                wx.CallAfter(lambda: wx.MessageBox(f"Error loading traffic: {e}", "Error", wx.OK | wx.ICON_ERROR))
                wx.CallAfter(lambda: self.status_text.SetLabel("Error loading traffic"))
            finally:
                wx.CallAfter(lambda: self.refresh_btn.Enable(True))
        
        threading.Thread(target=load, daemon=True).start()
    
    def update_display(self):
        """Update the pilots list display."""
        self.pilots_list.DeleteAllItems()
        
        # Apply filters
        filtered_pilots = self.pilots
        
        # Filter by favorites
        if self.favorites_only_cb.GetValue():
            filtered_pilots = [p for p in filtered_pilots if self.favorites_mgr.is_favorite(p.pilot_id)]
        
        # Filter by search text
        search = self.search_text.GetValue().lower()
        if search:
            filtered_pilots = [p for p in filtered_pilots if 
                             search in p.name.lower() or
                             search in p.callsign.lower() or
                             search in (p.aircraft or "").lower() or
                             search in (p.location_from or "").lower() or
                             search in (p.location_to or "").lower()]
        
        # Display pilots
        for pilot in filtered_pilots:
            idx = self.pilots_list.InsertItem(self.pilots_list.GetItemCount(), 
                                             "YES" if self.favorites_mgr.is_favorite(pilot.pilot_id) else "")
            self.pilots_list.SetItem(idx, 1, pilot.name)
            self.pilots_list.SetItem(idx, 2, pilot.callsign)
            self.pilots_list.SetItem(idx, 3, pilot.status or "")
            self.pilots_list.SetItem(idx, 4, pilot.aircraft or "")
            self.pilots_list.SetItem(idx, 5, pilot.location_from or "")
            self.pilots_list.SetItem(idx, 6, pilot.location_to or "")
            self.pilots_list.SetItemData(idx, pilot.pilot_id)
        
        self.status_text.SetLabel(f"Showing {len(filtered_pilots)} of {len(self.pilots)} pilots")
    
    def on_refresh(self, event):
        """Refresh traffic."""
        self.load_traffic()
    
    def on_filter_changed(self, event):
        """Filter changed."""
        self.update_display()
    
    def on_pilot_activated(self, event):
        """Pilot double-clicked - show profile."""
        idx = event.GetIndex()
        pilot_id = self.pilots_list.GetItemData(idx)
        pilot = next((p for p in self.pilots if p.pilot_id == pilot_id), None)
        if pilot:
            self.show_pilot_profile(pilot)
    
    def on_pilot_context(self, event):
        """Right-click on pilot - show context menu."""
        idx = event.GetIndex()
        if idx == -1:
            return
        
        pilot_id = self.pilots_list.GetItemData(idx)
        
        menu = wx.Menu()
        view_item = menu.Append(wx.ID_ANY, "View Profile")
        menu.AppendSeparator()
        
        if self.favorites_mgr.is_favorite(pilot_id):
            fav_item = menu.Append(wx.ID_ANY, "Remove from Favorites")
            self.Bind(wx.EVT_MENU, lambda e: self.toggle_favorite(pilot_id, False), fav_item)
        else:
            fav_item = menu.Append(wx.ID_ANY, "Add to Favorites")
            self.Bind(wx.EVT_MENU, lambda e: self.toggle_favorite(pilot_id, True), fav_item)
        
        self.Bind(wx.EVT_MENU, lambda e: self.on_pilot_activated(event), view_item)
        self.PopupMenu(menu)
        menu.Destroy()
    
    def toggle_favorite(self, pilot_id, add):
        """Toggle favorite status."""
        if add:
            self.favorites_mgr.add(pilot_id)
        else:
            self.favorites_mgr.remove(pilot_id)
        self.update_display()
    
    def show_pilot_profile(self, pilot):
        """Show detailed pilot profile."""
        dialog = PilotProfileDialog(self, self.client, self.favorites_mgr, pilot)
        dialog.ShowModal()
        dialog.Destroy()
        # Refresh display in case favorites changed
        self.update_display()


class PilotSearchPanel(scrolled.ScrolledPanel):
    """Panel for searching pilots."""
    
    def __init__(self, parent, client, favorites_mgr):
        super().__init__(parent)
        self.client = client
        self.favorites_mgr = favorites_mgr
        self.results = []
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Search controls
        search_sizer = wx.FlexGridSizer(3, 2, 5, 5)
        search_sizer.AddGrowableCol(1)
        
        search_sizer.Add(wx.StaticText(self, label="Name:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.name_text = wx.TextCtrl(self)
        search_sizer.Add(self.name_text, 1, wx.EXPAND)
        
        search_sizer.Add(wx.StaticText(self, label="Country:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.country_choice = wx.Choice(self, choices=["All"] + list(COUNTRIES.keys()))
        self.country_choice.SetSelection(0)
        search_sizer.Add(self.country_choice, 1, wx.EXPAND)
        
        search_sizer.Add(wx.StaticText(self, label="Rank:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.rank_choice = wx.Choice(self, choices=["All"] + list(RANKS.keys()))
        self.rank_choice.SetSelection(0)
        search_sizer.Add(self.rank_choice, 1, wx.EXPAND)
        
        sizer.Add(search_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Search button
        self.search_btn = wx.Button(self, label="Search")
        self.search_btn.Bind(wx.EVT_BUTTON, self.on_search)
        sizer.Add(self.search_btn, 0, wx.ALL, 5)
        
        # Results list
        self.results_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.results_list.InsertColumn(0, "Favorite", width=60)
        self.results_list.InsertColumn(1, "Name", width=200)
        self.results_list.InsertColumn(2, "Country", width=150)
        self.results_list.InsertColumn(3, "Rank", width=100)
        self.results_list.InsertColumn(4, "Flights", width=80)
        self.results_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_result_activated)
        self.results_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_result_context)
        
        sizer.Add(self.results_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Status
        self.status_text = wx.StaticText(self, label="Enter search criteria and click Search")
        sizer.Add(self.status_text, 0, wx.ALL, 5)
        
        self.SetSizer(sizer)
        self.SetupScrolling()
    
    def on_search(self, event):
        """Perform search."""
        name = self.name_text.GetValue().strip()
        country_idx = self.country_choice.GetSelection()
        rank_idx = self.rank_choice.GetSelection()
        
        if not name and country_idx == 0 and rank_idx == 0:
            wx.MessageBox("Please enter at least one search criterion", "Search", wx.OK | wx.ICON_INFORMATION)
            return
        
        self.status_text.SetLabel("Searching...")
        self.search_btn.Enable(False)
        self.results_list.DeleteAllItems()
        
        def search():
            try:
                results = []
                
                if name:
                    results = self.client.search_pilots_by_name(name)
                
                # Filter by country
                if country_idx > 0:
                    country = list(COUNTRIES.keys())[country_idx - 1]
                    if results:
                        results = [r for r in results if r.country == country]
                    else:
                        results = self.client.search_pilots_by_country(country)
                
                # Filter by rank
                if rank_idx > 0:
                    rank = list(RANKS.keys())[rank_idx - 1]
                    if results:
                        results = [r for r in results if r.rank == rank]
                    else:
                        results = self.client.search_pilots_by_rank(rank)
                
                self.results = results
                wx.CallAfter(self.update_results)
            except Exception as e:
                wx.CallAfter(lambda: wx.MessageBox(f"Search error: {e}", "Error", wx.OK | wx.ICON_ERROR))
                wx.CallAfter(lambda: self.status_text.SetLabel("Search failed"))
            finally:
                wx.CallAfter(lambda: self.search_btn.Enable(True))
        
        threading.Thread(target=search, daemon=True).start()
    
    def update_results(self):
        """Update results display."""
        self.results_list.DeleteAllItems()
        
        for profile in self.results:
            idx = self.results_list.InsertItem(self.results_list.GetItemCount(),
                                              "YES" if self.favorites_mgr.is_favorite(profile.pilot_id) else "")
            self.results_list.SetItem(idx, 1, profile.name)
            self.results_list.SetItem(idx, 2, profile.country or "")
            self.results_list.SetItem(idx, 3, profile.rank or "")
            self.results_list.SetItem(idx, 4, str(profile.flights or 0))
            self.results_list.SetItemData(idx, profile.pilot_id)
        
        self.status_text.SetLabel(f"Found {len(self.results)} pilots")
    
    def on_result_activated(self, event):
        """Result double-clicked - show profile."""
        idx = event.GetIndex()
        pilot_id = self.results_list.GetItemData(idx)
        profile = next((p for p in self.results if p.pilot_id == pilot_id), None)
        if profile:
            self.show_pilot_profile_from_search(profile)
    
    def on_result_context(self, event):
        """Right-click on result - show context menu."""
        idx = event.GetIndex()
        if idx == -1:
            return
        
        pilot_id = self.results_list.GetItemData(idx)
        
        menu = wx.Menu()
        view_item = menu.Append(wx.ID_ANY, "View Profile")
        menu.AppendSeparator()
        
        if self.favorites_mgr.is_favorite(pilot_id):
            fav_item = menu.Append(wx.ID_ANY, "Remove from Favorites")
            self.Bind(wx.EVT_MENU, lambda e: self.toggle_favorite(pilot_id, False), fav_item)
        else:
            fav_item = menu.Append(wx.ID_ANY, "Add to Favorites")
            self.Bind(wx.EVT_MENU, lambda e: self.toggle_favorite(pilot_id, True), fav_item)
        
        self.Bind(wx.EVT_MENU, lambda e: self.on_result_activated(event), view_item)
        self.PopupMenu(menu)
        menu.Destroy()
    
    def toggle_favorite(self, pilot_id, add):
        """Toggle favorite status."""
        if add:
            self.favorites_mgr.add(pilot_id)
        else:
            self.favorites_mgr.remove(pilot_id)
        self.update_results()
    
    def show_pilot_profile_from_search(self, profile):
        """Show detailed pilot profile from search result."""
        dialog = PilotProfileDialog(self, self.client, self.favorites_mgr, pilot_profile=profile)
        dialog.ShowModal()
        dialog.Destroy()
        self.update_results()


class PilotProfileDialog(wx.Dialog):
    """Dialog showing detailed pilot profile."""
    
    def __init__(self, parent, client, favorites_mgr, pilot=None, pilot_profile=None):
        super().__init__(parent, title="Pilot Profile", size=(600, 700))
        
        self.client = client
        self.favorites_mgr = favorites_mgr
        self.pilot = pilot
        self.profile = pilot_profile
        
        # Load full profile if only pilot given
        if pilot and not pilot_profile:
            self.profile = client.get_pilot_profile(pilot.pilot_id)
        
        # Main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Scrolled panel for content
        panel = scrolled.ScrolledPanel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Name header
        name_text = wx.StaticText(panel, label=f"PILOT PROFILE: {self.profile.name}")
        font = name_text.GetFont()
        font.PointSize += 2
        font = font.Bold()
        name_text.SetFont(font)
        panel_sizer.Add(name_text, 0, wx.ALL, 10)
        
        # Bio
        if self.profile.bio:
            bio_label = wx.StaticText(panel, label=f"Bio: {self.profile.bio}")
            bio_label.Wrap(550)
            panel_sizer.Add(bio_label, 0, wx.ALL, 5)
        
        # Flight status if available
        if pilot:
            flight_sizer = wx.BoxSizer(wx.VERTICAL)
            flight_sizer.Add(wx.StaticText(panel, label="CURRENTLY FLYING"), 0, wx.ALL, 5)
            
            info = [
                f"Flight Type: {pilot.get_flight_type_name()} ({pilot.flight_type})",
                f"Callsign: {pilot.callsign}",
                f"Status: {pilot.status}",
                f"Aircraft: {pilot.aircraft}",
                f"Passengers: {pilot.passengers}",
                f"From: {pilot.location_from}",
                f"To: {pilot.location_to}",
                f"Position: {pilot.location_position}",
            ]
            
            if pilot.description:
                info.append(f"Description: {pilot.description}")
            
            for line in info:
                flight_sizer.Add(wx.StaticText(panel, label=f"  {line}"), 0, wx.ALL, 2)
            
            panel_sizer.Add(flight_sizer, 0, wx.ALL, 5)
        
        # Profile information
        info_grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=5)
        info_grid.AddGrowableCol(1)
        
        fields = [
            ("Country", self.profile.country),
            ("Language", self.profile.language),
            ("Sex", self.profile.sex),
            ("Age", str(self.profile.age) if self.profile.age else ""),
            ("Rank", self.profile.rank),
            ("Rank Number", str(self.profile.rank_number) if self.profile.rank_number else ""),
            ("Overall Rank", str(self.profile.overall_rank) if self.profile.overall_rank else ""),
            ("Flights", str(self.profile.flights) if self.profile.flights else "0"),
            ("Distance", f"{self.profile.distance:,} km" if self.profile.distance else "0 km"),
            ("Flight Time", f"{self.profile.flight_time:,} min" if self.profile.flight_time else "0 min"),
            ("Points", f"{self.profile.points:,}" if self.profile.points else "0"),
            ("Earnings", f"${self.profile.earnings:,}" if self.profile.earnings else "$0"),
            ("Registered", self.profile.registered or ""),
            ("Last Login", self.profile.last_login or ""),
            ("Last Flight", self.profile.last_flight or ""),
        ]
        
        for label, value in fields:
            if value:
                info_grid.Add(wx.StaticText(panel, label=f"{label}:"), 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
                info_grid.Add(wx.StaticText(panel, label=value), 0, wx.EXPAND)
        
        panel_sizer.Add(info_grid, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(panel_sizer)
        panel.SetupScrolling()
        sizer.Add(panel, 1, wx.EXPAND)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        if self.favorites_mgr.is_favorite(self.profile.pilot_id):
            fav_btn = wx.Button(self, label="Remove from Favorites")
            fav_btn.Bind(wx.EVT_BUTTON, self.on_remove_favorite)
        else:
            fav_btn = wx.Button(self, label="Add to Favorites")
            fav_btn.Bind(wx.EVT_BUTTON, self.on_add_favorite)
        btn_sizer.Add(fav_btn, 0, wx.ALL, 5)
        
        close_btn = wx.Button(self, wx.ID_CLOSE, "Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        btn_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        
        self.SetSizer(sizer)
        self.Centre()
    
    def on_add_favorite(self, event):
        """Add pilot to favorites."""
        self.favorites_mgr.add(self.profile.pilot_id)
        wx.MessageBox(f"Added {self.profile.name} to favorites", "Favorites", wx.OK | wx.ICON_INFORMATION)
        self.Close()
    
    def on_remove_favorite(self, event):
        """Remove pilot from favorites."""
        self.favorites_mgr.remove(self.profile.pilot_id)
        wx.MessageBox(f"Removed {self.profile.name} from favorites", "Favorites", wx.OK | wx.ICON_INFORMATION)
        self.Close()


class FavoritesPanel(scrolled.ScrolledPanel):
    """Panel for managing favorites."""
    
    def __init__(self, parent, client, favorites_mgr):
        super().__init__(parent)
        self.client = client
        self.favorites_mgr = favorites_mgr
        self.favorites_profiles = []
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Controls
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.refresh_btn = wx.Button(self, label="Refresh")
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        ctrl_sizer.Add(self.refresh_btn, 0, wx.ALL, 5)
        
        sizer.Add(ctrl_sizer, 0, wx.EXPAND)
        
        # Favorites list
        self.fav_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.fav_list.InsertColumn(0, "Name", width=200)
        self.fav_list.InsertColumn(1, "Country", width=150)
        self.fav_list.InsertColumn(2, "Rank", width=100)
        self.fav_list.InsertColumn(3, "Flights", width=80)
        self.fav_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_favorite_activated)
        self.fav_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_favorite_context)
        
        sizer.Add(self.fav_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Status
        self.status_text = wx.StaticText(self, label="Ready")
        sizer.Add(self.status_text, 0, wx.ALL, 5)
        
        self.SetSizer(sizer)
        self.SetupScrolling()
        
        # Load favorites on startup
        wx.CallAfter(self.load_favorites)
    
    def load_favorites(self):
        """Load favorite pilots."""
        fav_ids = self.favorites_mgr.get_all()
        
        if not fav_ids:
            self.status_text.SetLabel("No favorites yet")
            return
        
        self.status_text.SetLabel("Loading favorites...")
        self.refresh_btn.Enable(False)
        
        def load():
            try:
                profiles = []
                for pilot_id in fav_ids:
                    try:
                        profile = self.client.get_pilot_profile(pilot_id)
                        profiles.append(profile)
                    except:
                        pass  # Skip if pilot not found
                
                self.favorites_profiles = profiles
                wx.CallAfter(self.update_display)
            except Exception as e:
                wx.CallAfter(lambda: wx.MessageBox(f"Error loading favorites: {e}", "Error", wx.OK | wx.ICON_ERROR))
            finally:
                wx.CallAfter(lambda: self.refresh_btn.Enable(True))
        
        threading.Thread(target=load, daemon=True).start()
    
    def update_display(self):
        """Update favorites display."""
        self.fav_list.DeleteAllItems()
        
        for profile in self.favorites_profiles:
            idx = self.fav_list.InsertItem(self.fav_list.GetItemCount(), profile.name)
            self.fav_list.SetItem(idx, 1, profile.country or "")
            self.fav_list.SetItem(idx, 2, profile.rank or "")
            self.fav_list.SetItem(idx, 3, str(profile.flights or 0))
            self.fav_list.SetItemData(idx, profile.pilot_id)
        
        self.status_text.SetLabel(f"{len(self.favorites_profiles)} favorites")
    
    def on_refresh(self, event):
        """Refresh favorites."""
        self.load_favorites()
    
    def on_favorite_activated(self, event):
        """Favorite double-clicked."""
        idx = event.GetIndex()
        pilot_id = self.fav_list.GetItemData(idx)
        profile = next((p for p in self.favorites_profiles if p.pilot_id == pilot_id), None)
        if profile:
            dialog = PilotProfileDialog(self, self.client, self.favorites_mgr, pilot_profile=profile)
            dialog.ShowModal()
            dialog.Destroy()
            self.load_favorites()
    
    def on_favorite_context(self, event):
        """Right-click on favorite."""
        idx = event.GetIndex()
        if idx == -1:
            return
        
        pilot_id = self.fav_list.GetItemData(idx)
        
        menu = wx.Menu()
        view_item = menu.Append(wx.ID_ANY, "View Profile")
        remove_item = menu.Append(wx.ID_ANY, "Remove from Favorites")
        
        self.Bind(wx.EVT_MENU, lambda e: self.on_favorite_activated(event), view_item)
        self.Bind(wx.EVT_MENU, lambda e: self.remove_favorite(pilot_id), remove_item)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def remove_favorite(self, pilot_id):
        """Remove from favorites."""
        self.favorites_mgr.remove(pilot_id)
        self.load_favorites()


class MainFrame(wx.Frame):
    """Main application window."""
    
    def __init__(self):
        super().__init__(None, title="Eurofly Traffic Monitor", size=(1000, 700))
        
        # Initialize client and favorites
        self.client = EuroflyClient()
        self.favorites_mgr = FavoritesManager()
        
        # Create notebook for tabs
        notebook = wx.Notebook(self)
        
        # Add tabs
        self.traffic_panel = TrafficPanel(notebook, self.client, self.favorites_mgr)
        notebook.AddPage(self.traffic_panel, "Current Traffic")
        
        self.search_panel = PilotSearchPanel(notebook, self.client, self.favorites_mgr)
        notebook.AddPage(self.search_panel, "Search Pilots")
        
        self.favorites_panel = FavoritesPanel(notebook, self.client, self.favorites_mgr)
        notebook.AddPage(self.favorites_panel, "Favorites")
        
        # Menu bar
        menubar = wx.MenuBar()
        
        file_menu = wx.Menu()
        refresh_item = file_menu.Append(wx.ID_REFRESH, "Refresh\tCtrl+R", "Refresh current view")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "Exit\tCtrl+Q", "Exit application")
        menubar.Append(file_menu, "&File")
        
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "About", "About Eurofly Traffic Monitor")
        menubar.Append(help_menu, "&Help")
        
        self.SetMenuBar(menubar)
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, self.on_refresh, refresh_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        
        # Status bar
        self.CreateStatusBar()
        self.SetStatusText("Ready")
        
        self.Centre()
        self.Show()
    
    def on_refresh(self, event):
        """Refresh current tab."""
        page = self.GetChildren()[0].GetCurrentPage()
        if hasattr(page, 'on_refresh'):
            page.on_refresh(None)
    
    def on_exit(self, event):
        """Exit application."""
        self.Close()
    
    def on_about(self, event):
        """Show about dialog."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("Eurofly Traffic Monitor")
        info.SetVersion("1.0")
        info.SetDescription("Native GUI for monitoring Eurofly flight traffic\n\nFeatures:\n• View current traffic\n• Search pilots\n• Manage favorites\n• View detailed profiles\n• Screenreader accessible")
        info.SetWebSite("https://eurofly.stefankiss.sk")
        wx.adv.AboutBox(info)


def main():
    """Run the application."""
    app = wx.App()
    frame = MainFrame()
    app.MainLoop()


if __name__ == '__main__':
    main()
