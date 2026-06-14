# 🚀 ED Multi Route Navigation (EDMRN) v3.3.0

***"I saw the darkness and was inspired by the light! - CMDR Ninurta KALHU"***

---

**The Ultimate Multi-Route Optimization & Tracking Tool for Elite Dangerous**  

Completely modular architecture with professional theme system, advanced route planning, and real-time tracking.
![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue) ![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-green) ![Version 3.3.0](https://img.shields.io/badge/Version-3.3.0-brightgreen) ![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D4) ![Status: Active](https://img.shields.io/badge/Status-Active-success)

---


## Table of Contents

- [What's New in v3.3](#-whats-new-in-v33)
- [Key Features](#-key-features)
- [Download & Installation](#-download--installation)
- [Quick Start Guide](#-quick-start-guide)
- [System Requirements](#-system-requirements)
- [In-Game Overlay](#-in-game-overlay-features)
- [Settings & Configuration](#-settings--configuration)
- [API Credits & Attribution](#-api-credits--attribution)
- [Project Structure](#-project-structure)
- [License](#-license)
- [Developer](#-developer)
---
## What's New in v3.3

### Custom Route Planner (Brand New)

**Route Planning Features:**
- New "Custom Route" tab for manual system route planning
- Add systems by name with autocomplete support (Spansh + EDSM)
- Add systems by coordinates (X, Y, Z) manually
- TSP optimization for shortest route calculation
- Neutron Path mode for reduced jumps using neutron star boosts
- 3D MiniMap visualization with route lines
- Navigation through waypoints with Previous/Next buttons
- Jump range calculation based on ship's FSD (auto-detected from journal)
- LY distance display between systems
- Total jump count with neutron boost comparison

**System List Management:**
- Click-to-select systems for batch operations
- Remove selected systems or Clear All
- Visual feedback: orange=current, yellow=selected, gray=pending
- Drag-to-reorder support

**Import/Export:**
- JSON format with full metadata
- TXT format for simple system lists
- Bidirectional compatibility

**Overlay Integration:**
- Custom Route tab added to overlay (CR button)
- Previous/Next navigation from overlay
- Auto-copy system names to clipboard
- Auto-start overlay after optimization

### Code Refactoring & Architecture Improvements (June 2026)

**Dead Code Cleanup**
- Removed duplicate modules: `platform.py`, `route_manager.py`, `table_widget.py`
- Cleaned up `exceptions.py` - removed unused exception classes
- Fixed duplicate method definitions in `app.py`
- Removed duplicate imports

**New Modules - System Info Split**
- `exobiology.py` - Exobiology tracking and display (444 lines)
- `journal_cache.py` - Journal file reading and caching (218 lines)
- `log_viewer.py` - Log table and filtering (782 lines)
- `system_info_section.py` reduced from 2419 to 784 lines

**New Modules - App.py Split**
- `galaxy_handler.py` - Galaxy Plotter logic (349 lines)
- `app_window.py` - Window management and borderless mode (297 lines)
- `journal_handler.py` - Journal event processing (419 lines)
- `custom_route.py` - Custom Route Planner (963 lines)

**Bug Fixes**
- Fixed EDSM API 403 errors by adding User-Agent headers
- Fixed Galaxy Plotter 414 Request-URI Too Large error
- Fixed overlay freeze on rapid button clicks
- Fixed autocomplete dropdown orphan windows
- Fixed MiniMap matplotlib 3D rendering errors
- Added thread-safe operations for overlay interactions
- Journal auto-detects ship jump range from Loadout event

**Architecture Improvements**
- Composition pattern for better separation of concerns
- Delegation methods for cleaner API
- Thread-safe cache for overlay tab state
- All modules verified with syntax checks
- Application tested and confirmed working

### System Info Tab (Brand New)

- Comprehensive system details, statistics, exobiology summary, celestial bodies, stations, and galactic notes in one screen
- Advanced autocomplete with Spansh.co.uk and EDSM.net API integration for fast system search
- System statistics, exobiology findings, planets, and surface details
- Detailed tables for all celestial bodies and stations with filtering and quick access
- Galactic notes and custom annotations
- Fully theme-compatible with modern, readable interface

### Log Tab (Brand New)

- Advanced journal viewing, filtering, and analysis for game logs
- Multi-filtering with time range, text search, and column selection
- Column selector, auto-sizing, pinned columns, custom icons, note annotations
- Double-click any row for detail window with two-column data display and notes
- Advanced data formatting, quick copy, detailed tooltips, and context menu
-  **Performance & Stability:** Cumulative logs with smart cache + background processing to prevent freezing
-  **Faster Updates:** One-time initial read, then append-only new entries
-  **UI Protection:** Preserves previous records instead of instant clearing, safe listing at high volume

### Other Improvements

- Modernization, readability, and performance improvements across all themes and UI
- New modules: system_info_section.py, column_display_names.py, codex_translation.py, slef_store.py
- Refactored modules: exobiology.py, journal_cache.py, log_viewer.py, galaxy_handler.py, app_window.py, journal_handler.py
- Bug fixes and performance optimizations

### Enhanced User Experience (v3.3.0 - June 2026)

**Visit History System**

- Track your exploration patterns with persistent visit history
- Automatic system visit tracking across sessions
- Historical data survives route changes and app restarts
- Smart duplicate prevention

**Smart Backup & Recovery**

- Atomic file operations prevent data corruption
- Automatic backup creation before critical operations
- Backup restoration with integrity verification
- Enhanced error recovery mechanisms

**GeForce Now Overlay Controls**

- Special support for cloud gaming platforms
- Borderless window mode detection
- Automatic overlay launch configuration
- Enhanced window management for streaming

**Nearest System Finder**

- Auto-detection of current CMDR location from journal
- Intelligent distance calculation to CSV systems
- Dropdown selector for manual system choice
- Separated finder for Neutron tab (coordinate-based)

**API Optimizations**

- Neutron Router API compatibility improvements
- Proper User-Agent headers for all API calls
- Rate limiting and request optimization
- Better error handling and recovery

### v3.0 Foundation - Complete Architecture Redesign

**Fully Modular Architecture**

- 35+ independent, maintainable modules
- Thread-safe design with proper locking
- Separated concerns for better scalability
- Enhanced performance and memory management

**Revolutionary Theme System**

- 11 Elite Dangerous PowerPlay faction themes
- JSON-based CustomTkinter native themes
- Smart color tone generation algorithm
- Professional dark UI aesthetics

**Advanced Route Planning**

- TSP-based optimization for shortest paths
- Neutron highway integration
- Galaxy Plotter with Spansh Exact Router
- Real-time 3D visualization

---

##  Key Features (v3.3.0)


### Core Functionality

 **Custom Route Planner** - Manual system route planning with autocomplete, coordinates, neutron boosts, and 3D visualization
 **System Info Tab** - Complete system details, statistics, exobiology, bodies, stations, and notes in one screen
 **Log Tab** - Advanced journal viewing, filtering, column selection, and detail panel
-  **Smart Route Optimization** - TSP-based shortest path algorithm with configurable starting points
-  **Interactive 3D Visualization** - Real-time 3D mini-map with zoom, rotate, and pan controls
-  **In-Game Overlay** - Transparent overlay with live progress tracking (Ctrl+O toggle)
-  **Auto Journal Monitoring** - Real-time Elite Dangerous journal tracking with multi-commander support
-  **Intelligent Auto-Save** - Configurable intervals (1/5/10 min) with atomic operations
-  **Visit History Tracking** - Persistent exploration history survives app restarts

### Advanced Features

 **Advanced Filtering & Table Features** - Time/text/column filters in Log tab, detail panel, note annotations
-  **Neutron Highway Router** - Advanced neutron jump routing with range optimization
-  **Galaxy Plotter** - Spansh Exact Router integration with fuel calculations
-  **Smart System Autocomplete** - Real-time Spansh (70M+ systems) API suggestions with EDSM fallback and 300ms debouncing
-  **11 PowerPlay Themes** - Elite Dangerous faction color schemes with automatic restart
-  **Smart Backup System** - Atomic writes, automatic backups, integrity verification
-  **GeForce Now Support** - Cloud gaming optimized with borderless mode detection

### Custom Route Planner Features

-  **System Management** - Add by name (autocomplete) or coordinates (X, Y, Z)
-  **Route Optimization** - TSP algorithm with shortest distance or neutron path modes
-  **Neutron Boost** - Calculate jumps using neutron star boosts (6x range)
-  **Jump Statistics** - LY distance and jump count between systems
-  **System Selection** - Click-to-select for batch operations
-  **Import/Export** - JSON and TXT format support
-  **Overlay Integration** - Full overlay support with navigation controls

### Technical Excellence

-  **Modular Architecture** - 35+ independent modules for maintainability
-  **Thread-Safe Design** - Proper locking mechanisms throughout
-  **Optimized Performance** - Smart caching, debouncing, efficient memory usage
-  **Robust Error Handling** - Comprehensive error recovery and logging

---

## Download & Installation

### Recommended: Pre-built Executable (Windows)

**Latest Release: v3.3.0**

[📥 DOWNLOAD EDMRN v3.3.0 CLICK HERE](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/download/v3.3/EDMRN.v3.3.exe)

**Quick Start (Windows):**

1. Download `EDMRN_v3.3.exe` from [Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases)
2. Run the executable - no installation required!
3. Fully portable - runs from any location
4. All dependencies included

  

### Run from Source (All Platforms)

**Requirements:**

- Python 3.12 or higher
- pip package manager
- Git (for cloning)

**Installation Steps:**
```bash

# Clone the repository

git  clone  https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer.git

cd  Elite-Dangerous-Multi-Route-Optimizer

# Install dependencies

pip  install  -r  requirements.txt

# Run the application

python  run.py

```

**Building Executable (Windows):**

```bash

# Install PyInstaller

pip  install  pyinstaller

# Run build script

build_edmrn.bat

```

---

  

## System Requirements

### Minimum Requirements

-  **OS**: Windows 10/11 (64-bit)
-  **Python**: 3.12+ (for source installation)
-  **RAM**: 4 GB
-  **Storage**: 200 MB free space
-  **Elite Dangerous**: Journal logging enabled

### Recommended Requirements

-  **OS**: Windows 11 (64-bit)
-  **RAM**: 8 GB
-  **Monitor**: 1920x1080 or higher
-  **Elite Dangerous**: Borderless Window mode (for overlay)

### Required Elite Dangerous Settings

1. Enable Journal logging (default: enabled)
2. Use Borderless Window mode for overlay functionality
3. Journal path: `%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous\`

---

## Quick Start Guide

### Step 1: Export Your Route

1. Use Spansh.co.uk to create your system list
2. Export as CSV with **required** columns: `System Name`, `X`, `Y`, `Z`
3.  **Optional**: Include `Body Name` for biological/geological signals

**Note**: Only 4 columns are required (System Name, X, Y, Z). Body Name is optional but recommended for exploration routes.

### Step 2: Optimize Route

1.  **Route Optimization**

- Click "Browse" to select your CSV file
- Enter ship jump range (e.g., 75.23 LY)
- Optional: Set starting system for optimized pathing
- Click "Optimize Route and Start Tracking"
- Wait for TSP optimization to complete


### Step 3: Track Progress

1.  **Route Tracking**

- Interactive 3D map displays your optimized route
- Systems update automatically via journal monitoring
- Click systems to manually mark visited/skipped
- Use quick actions:
-  **Copy Next**: Copy next system to clipboard
-  **Data Folder**: Open EDMRN data directory
-  **Open Excel**: View route in spreadsheet
-  **Load Backup**: Restore previous route state

### Step 4: Neutron Highway (Optional)

1.  **Neutron Highway**

- Enter source and destination systems (with autocomplete)
- Set ship jump range and fuel tank capacity
- Select neutron mode and efficiency
- Click "Calculate Route" for optimized neutron routing
- Export route or copy to clipboard

### Step 5: Galaxy Plotter (Optional)

1.  **Galaxy Plotter**

- Use Spansh Exact Router integration
- Enter ship build from Coriolis.io or EDSY.org
- Configure route preferences (neutron, boosts, etc.)
- Get precise fuel consumption calculations
- Export route for navigation

### Step 6: Use In-Game Overlay

1.  **Settings → Overlay**
2. Click "Start Overlay" button
3. Configure overlay settings:
-  **Opacity**: 50-100% transparency
-  **Size**: Small/Medium/Large
-  **Position**: Drag overlay to preferred location
4. In Elite Dangerous (Borderless Window mode):
- Press **Ctrl+O** to toggle overlay visibility
- Overlay shows current system, next target, and bodies to scan
- Real-time progress tracking with distance stats

 
### Step 7: Choose Your Theme

1.  **Settings → Appearance**
2. Select from 11 PowerPlay faction themes:
- Elite Dangerous (default)
- Aisling Duval, Archon Delaine, Arissa Lavigny-Duval
- Denton Patreus, Edmund Mahon, Felicia Winters
- Li Yong-Rui, Pranav Antal, Zachary Hudson, Zemina Torval
3. App automatically restarts to apply theme
4. Enjoy your faction-themed EDMRN experience!

---

## In-Game Overlay Features

### Display Components

| Component | Description | Details |
|-----------|-------------|---------|  
| **Current System** | Your current location | Real-time journal tracking with status |
| **Next Target** | Next system in route | Distance and direction indicator |
| **Bodies to Scan** | Biological/geological signals | Filtered by current system |
| **Progress Tracker** | Route completion stats | Visited/Skipped/Remaining counts |
| **Distance Stats** | Total and traveled distance | Live calculation in light-years |
| **Route Info** | Total systems and completion % | Progress bar visualization |


### Overlay Controls

-  **Toggle**: Press **Ctrl+O** to show/hide overlay
-  **Reposition**: Click and drag overlay to any screen position
-  **Resize**: Choose Small/Medium/Large in settings
-  **Opacity**: Adjust 50-100% transparency in settings
-  **Always On Top**: Overlay stays visible over Elite Dangerous

### Overlay Tips

**Best Performance:**

- Use Borderless Window mode in Elite Dangerous
- Disable VSync for better overlay responsiveness
- Place overlay in non-critical screen areas

**GeForce Now Users:**

- Enable "Auto-Launch Overlay" in settings
- Borderless mode automatically detected
- Optimized for cloud gaming latency


 **Troubleshooting:**

- If overlay doesn't appear: Check Borderless Window mode
- If overlay won't drag: Restart overlay from settings
- If data not updating: Verify journal path in settings

---

## Settings & Configuration

### Overlay Settings

- **Start/Stop Overlay**: Toggle overlay visibility
- **Opacity Control**: 50-100% (default: 90%)
- **Size Selection**: Small/Medium/Large
- **Hotkey**: Ctrl+O (customizable in future versions)
- **Auto-Launch**: Start overlay with route optimization
- **Position Memory**: Remembers last overlay position

### Auto-Save System

- **Intervals**: 1/5/10 minutes or Never
- **Status Indicator**: Shows next save countdown
- **Manual Save**: Force save anytime with Ctrl+S
- **Atomic Operations**: Prevents data corruption
- **Auto-Backup**: Creates backup before each save
- **Recovery**: Automatic recovery on corrupt data detection

### Journal Monitoring

- **Auto-Detection**: Automatically finds Elite Dangerous journal
- **Multi-Commander**: Supports multiple CMDR profiles
- **Manual Path**: Custom journal location support
- **Real-Time Updates**: Instant system change detection
- **Status Display**: Shows current CMDR and location
- **Test Function**: Verify journal connection

### Appearance & Themes

- **11 Faction Themes**: PowerPlay-inspired color schemes
- **Automatic Restart**: Seamless theme application
- **Color Consistency**: Professional dark UI throughout
- **Custom Fonts**: Elite Dangerous-style typography
- **High Contrast**: Optimized for long exploration sessions

### Advanced Settings

- **Starting System**: Override for route optimization
- **Jump Range**: Precise to 0.01 LY
- **Backup Management**: Manual backup creation/restoration
- **Data Export**: CSV export with customizable columns
- **Log Level**: Adjust logging verbosity for troubleshooting

---

## Scientific Heritage & The "Light" Principle

> *"Light doesn't choose the shortest path... it chooses the fastest."*

EDMRN is built on the philosophy of **Fermat's Principle of Least Time**. While the galaxy is vast, navigation is an optimization problem. To solve this, EDMRN utilizes a custom-reimplemented version of the **Lin-Kernighan (LK) Algorithm**.

### The Minds Behind the Logic:
- **Brian Kernighan (1942-)**: A living legend of computer science (co-creator of C, Unix, and AWK). His work at Bell Labs laid the foundation for the efficiency you see in EDMRN today.
- **Shen Lin (1932-2017)**: The mathematical genius who, alongside Kernighan, solved the TSP complexity with the variable n-opt heuristic.

In version 3.3.0, this engine is more refined than ever, allowing 500+ system routes to be optimized in seconds on modern CPUs like the Ryzen 9, while maintaining minimal system overhead.

---

## API Credits & Attribution
 
EDMRN relies on these excellent community services:

### Spansh - Elite Dangerous Tools

- **Usage**:
  - Neutron highway route calculation
  - Galaxy plotter / exact router
  - System name autocomplete (primary source)
- **API**: Route planning and system data
- **Website**: [spansh.co.uk](https://spansh.co.uk)
- **Attribution**: Required under Spansh terms of use
- **Optimizations**:
  - 300ms debouncing for autocomplete
  - 1-hour caching to reduce server load
  - Minimum 3-character requirement


### EDSM - Elite Dangerous Star Map

- **Usage**:
  - System name autocomplete (fallback source)
  - System information and statistics
  - Celestial body data and station information
- **API**: System search, coordinate data, and detailed system information
- **Website**: [edsm.net](https://www.edsm.net)
- **Attribution**: Required under EDSM terms of use
- **Rate Limiting**: Respectful API usage with smart caching
- **Optimizations**:
  - Intelligent request batching
  - Long-term caching for static data
  - Fallback mechanism for reliability

### API Usage Optimization

EDMRN implements responsible API usage:

- Smart caching reduces redundant requests
- Debouncing prevents request flooding
- Proper User-Agent headers for tracking
- Fallback mechanisms for reliability
- Rate limiting respects server resources

**Note**: EDMRN is not affiliated with EDSM or Spansh. We're grateful for their services!

---

### Performance Tips

- Close other applications during route optimization
- Use SSD for better file I/O performance
- Disable antivirus real-time scanning for EDMRN folder
- Keep only necessary tabs open
- Clear old backups periodically to save space

### Antivirus False Positives
Some antivirus software may flag EDMRN.exe (common with PyInstaller-built apps):

 **Safe Options:**

1. Add EDMRN folder to antivirus exceptions
2. Run from source code instead of executable
3. Check [https://www.virustotal.com/](https://www.virustotal.com/gui/file/0574687e50946876e88e695f7e67a447d6969a372014645b8e4b0205c90fc152) for verification
4. Download only from official GitHub releases
 
### Getting More Help

-  **Discord**: [EDMRN Community](https://discord.gg/DWvCEXH7ae) - fastest support
-  **GitHub Issues**: [Report bugs](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues)
-  **Email**: ninurtakalhu@gmail.com
-  **Wiki**: Detailed guides and tutorials (coming soon)


---

## Project Structure

```
EDMRN_v3.3/
├── edmrn/                          # Main application package
│   ├── app.py                      # Main GUI application & orchestrator
│   ├── app_window.py               # Window management & borderless mode
│   ├── galaxy_handler.py           # Galaxy Plotter logic & navigation
│   ├── journal_handler.py          # Journal event processing & CMDR data
│   ├── custom_route.py             # Custom Route Planner
│   ├── exobiology.py               # Exobiology tracking & display
│   ├── journal_cache.py            # Journal file reading & caching
│   ├── log_viewer.py               # Log table & filtering
│   ├── system_info_section.py      # System Info tab UI
│   ├── optimizer.py                # TSP route optimization engine
│   ├── tracker.py                  # Route tracking & visit history
│   ├── minimap.py                  # 3D visualization with matplotlib
│   ├── overlay.py                  # In-game overlay window system
│   ├── journal.py                  # Journal file monitoring & parsing
│   ├── journal_operations.py       # Journal file operations & detection
│   ├── logger.py                   # Centralized logging system
│   ├── backup.py                   # Backup management & restoration
│   ├── autosave.py                 # Auto-save functionality
│   ├── platform_detector.py        # Platform detection
│   ├── exceptions.py               # Custom exception definitions
│   ├── utils.py                    # Utility functions & helpers
│   ├── config.py                   # Configuration management
│   ├── gui.py                      # GUI dialogs & components
│   ├── ui_components.py            # Reusable UI widgets
│   ├── theme_manager.py            # Theme switching & colors
│   ├── theme_editor.py             # Theme editor for customization
│   ├── ed_theme.py                 # Elite Dangerous theme constants
│   ├── route_management.py         # Route handling & CSV operations
│   ├── settings_manager.py         # Settings UI & persistence
│   ├── neutron_manager.py          # Neutron highway UI & controls
│   ├── neutron.py                  # Neutron routing engine
│   ├── galaxy_plotter.py           # Galaxy plotter Spansh API
│   ├── file_operations.py          # File I/O operations
│   ├── system_autocomplete.py      # EDSM/Spansh autocomplete
│   ├── autocomplete_entry.py       # Custom autocomplete widget
│   ├── edmrn_sheet.py              # Themed spreadsheet widget
│   ├── column_display_names.py     # Column display names
│   ├── codex_translation.py        # Codex translation support
│   ├── slef_store.py               # Ship build storage
│   ├── icons.py                    # Unicode emoji constants
│   ├── updater.py                  # GitHub update checker
│   ├── visit_history.py            # Visit history manager
│   ├── visit_history_dialog.py     # Visit history dialog
│   ├── themes/                     # JSON theme definitions
│   │   ├── elite_dangerous.json
│   │   ├── aisling_duval.json
│   │   ├── archon_delaine.json
│   │   ├── arissa_lavigny_duval.json
│   │   ├── denton_patreus.json
│   │   ├── edmund_mahon.json
│   │   ├── felicia_winters.json
│   │   ├── li_yong_rui.json
│   │   ├── pranav_antal.json
│   │   ├── zachary_hudson.json
│   │   └── zemina_torval.json
│   └── __init__.py                 # Package initialization
├── assets/                         # Application resources
│   ├── explorer_icon.ico
│   └── explorer_icon.png
├── main.py                         # Primary entry point
├── run.py                          # Alternative entry point
├── setup.py                        # PyPI packaging
├── edmrn.spec                      # PyInstaller build spec
├── build_clean.bat                 # Windows build script
├── requirements.txt                # Python dependencies
├── LICENSE                         # AGPL-3.0 license
└── README.md                       # This file
```

---

## License

EDMRN is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---

## Developer

**CMDR Ninurta KALHU** - Lead Developer

- GitHub: [NinurtaKalhu](https://github.com/NinurtaKalhu)
- Email: ninurtakalhu@gmail.com

---

*Built with Python, CustomTkinter, and love for Elite Dangerous exploration.*

---

## Support Development

If EDMRN enhances your Elite Dangerous experience, consider supporting development:

- ☕ [Ko-fi](https://ko-fi.com/ninurtakalhu) - One-time tips
- 🎯 [Patreon](https://www.patreon.com/c/NinurtaKalhu) - Monthly support

**Your support helps:**

- Maintain and improve EDMRN
- Add new features and optimizations
- Provide faster support and updates
- Keep the project ad-free and open-source

---

## Security & Privacy

### ✅ What EDMRN Does:

- ✅ Reads Elite Dangerous journal files (local only, read-only access)
- ✅ Saves route data locally in `Documents/EDMRN_Route_Data/`
- ✅ Creates overlay window for in-game display
- ✅ Copies system names to clipboard (manual paste, user-initiated)
- ✅ Checks GitHub for updates (version comparison only)
- ✅ Makes API calls to EDSM/Spansh (system data, route calculations)

### ❌ What EDMRN Does NOT Do:

- ❌ No telemetry or analytics collection
- ❌ No personal information access or storage
- ❌ No game memory manipulation or injection
- ❌ No automated keyboard/mouse input
- ❌ No data sharing with third parties
- ❌ No online account required
- ❌ No background processes when closed

### 🔒 Data Storage

All data stored locally on your PC:

-  **Route Data**: `%USERPROFILE%\Documents\EDMRN_Route_Data\`
-  **Backups**: `EDMRN_Route_Data\backups\`
-  **Logs**: `EDMRN_Route_Data\logs\`
-  **Settings**: `EDMRN_Route_Data\settings.json`

**No cloud storage. No remote access. Your data stays yours.**

### Antivirus False Positives

PyInstaller-built executables sometimes trigger false positives:

**Why this happens:**

- PyInstaller bundles Python interpreter
- Some AV heuristics flag unknown executables
- EDMRN is new and not widely distributed yet

  

**Verification Steps:**

1. ✅ Download only from official [GitHub Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases)
2. ✅ Check file hash against release notes
3. ✅ Scan with [VirusTotal](https://www.virustotal.com/gui/file/0574687e50946876e88e695f7e67a447d6969a372014645b8e4b0205c90fc152)
4. ✅ Run from source if concerned (see installation)

**Safe Actions:**

- Add EDMRN folder to antivirus exceptions
- Use Windows Defender SmartScreen "Run anyway"
- Report false positive to your AV vendor

---

## License

**GNU Affero General Public License v3.0 (AGPL-3.0-only)**

### What This Means:

✅ **You CAN:**

- Use EDMRN freely for personal or commercial purposes
- Share EDMRN with others

❗ **You MUST:**

- Keep the same AGPL-3.0-only license for derivative works
- Provide source code if you distribute modified versions
- Provide source code if you run EDMRN as a network service
- Include copyright and license notices
  

❌ **You CANNOT:**

- Relicense under different terms
- Hold the developer liable for issues
- Use developer name for endorsements without permission

**Full License Text**: [LICENSE](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/LICENSE)

**Why AGPL?** It ensures EDMRN remains free and open-source, even if hosted as a service.

---

## Developer

**Ninurta Kalhu (S.C.)** - Solo Developer & Elite Dangerous CMDR

Passionate explorer building tools for the Elite Dangerous community.

### Connect:

### Connect:

- **Discord**: [EDMRN Community](https://discord.gg/DWvCEXH7ae)
- **Email**: ninurtakalhu@gmail.com
- **X (Twitter)**: [@NinurtaKalhu](https://twitter.com/NinurtaKalhu)
- **GitHub**: [NinurtaKalhu](https://github.com/NinurtaKalhu)

### Development Stats:

- Project started: 2025
- Lines of code: 20,000+
- Themes created: 11
- Modules: 35+
- Made with ❤️ for Elite Dangerous

---

## Screenshots

### Main Interface

![Route Optimization](screenshots/SS1.png)
*Route optimization with CSV import and TSP algorithm*
 ![Route Tracking with 3D Map](screenshots/SS2.png)
*Interactive 3D map with real-time journal tracking*

### Advanced Features

![Neutron Highway Router](screenshots/SS3.png)
*Neutron highway routing with autocomplete*
![Galaxy Plotter](screenshots/SS3a.png)
*Galaxy Plotter with autocomplete*
![Backup Management](screenshots/SS4.png)

### Settings & Customization

![Settings Panel](screenshots/SS5.png)
*Comprehensive settings and configuration*
 
### In-Game Experience

![Overlay Tracking](screenshots/SS6.png)
*New transparent overlay "3 TABS" showing real-time progress for "VR and "Geforce Now players"*

### About & Credits

![About Window](screenshots/SS8.png)
*Version info and credits*
![User Manual](screenshots/SS9.png)
*Comprehensive user manual and attributions*

---
## Version History Highlights

### v3.3.0 (June 2026) - Current Release

-  System Info tab: System details, statistics, exobiology, bodies, stations, notes
-  Log tab: Advanced journal viewing, filtering, column selection, detail panel
-  New table & detail panel: Auto-sizing, icons, note annotations, enhanced data formatting
-  New modules: system_info_section.py, table_widget.py, column_display_names.py, codex_translation.py, slef_store.py
-  Log performance improvements: Cache-based reading + tail updates
-  Freeze fixes: Background processing and main thread safety
-  Log stability: Blank screen protection and safe table updates
- Modernization, readability, and performance improvements across all themes and UI
- Bug fixes and performance optimizations

### v3.1.0 (2026)

- Visit History System with persistent tracking
- Smart Backup with atomic operations
- GeForce Now overlay controls
- Borderless mode (experimental)
- Enhanced autocomplete
- API optimizations
- Improved dropdown UX with window tracking
- EDSM & Spansh attribution
- Galaxy Plotter integration (Spansh Router)
- Precise fuel consumption calculations
- Ship build integration (Coriolis/EDSY)
- Smart system autocomplete (EDSM/Spansh)
- Real-time suggestions with caching
- Enhanced neutron routing

### v3.0.0 (November 2025) - Major Redesign

- Complete modular architecture (15+ modules)
- Revolutionary 11-theme system
- Backup system restructuring
- Overlay system redesign
- Thread-safe design throughout

---

## Quick Links

| Resource | URL |
|----------|-----|
| 🏠 **GitHub Repository** | [github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer) |
| 📥 **Latest Release** | [Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases) |
| 💬 **Discord Community** | [discord.gg/DWvCEXH7ae](https://discord.gg/DWvCEXH7ae) |
| 🐛 **Bug Reports** | [GitHub Issues](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues) |
| 📖 **Documentation** | [Wiki](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/wiki) (coming soon) |
| ☕ **Support Development** | [Ko-fi](https://ko-fi.com/ninurtakalhu) |

---

## Acknowledgments

### Special Thanks To:

**Data Providers:**

- [EDSM](https://www.edsm.net)
- [Spansh](https://spansh.co.uk)

**Elite Dangerous Community:**

- Frontier Developments - For creating Elite Dangerous
- Elite Dangerous Community Developers (EDCD)
- All commanders who provided feedback and testing
  
**Open Source Projects:**

- Python & CustomTkinter - UI framework
- Matplotlib - 3D visualization
- SciPy - TSP optimization algorithms
- Requests - HTTP library for APIs

**Beta Testers & Contributors:**

- Community members who tested and reported issues
- Discord members providing valuable feedback
- Everyone who shared EDMRN with others

---

**Fly safe, Commander! o7**

*"In the black, every lightyear counts."*

---

Made with ❤️ by [Ninurta Kalhu](https://github.com/NinurtaKalhu) for the Elite Dangerous community

**EDMRN v3.3.0** | June 2026 | [AGPL-3.0](LICENSE)



## 📸 Screenshots

![Route Optimization](screenshots/SS001.png)
*Route optimization with CSV import and TSP LK algorithm*

![Load Backup](screenshots/SS002.png)
*LSelect backup route*

![Visited System](screenshots/SS003.png)
*Previously visited systems*

![Route Tracking with 3D Map](screenshots/SS004.png)
*Interactive 3D map with real-time journal tracking*

### Advanced Features
![Neutron Highway Router](screenshots/SS005.png)
*Neutron highway routing*

![Galaxy Plotter](screenshots/SS006.png)
*Galaxy Plotter*

### System Info
![System info](screenshots/SS007.png)
*System info and Bioscan*

![Bodies](screenshots/SS008.png)
*Bodies info*

![Stations info](screenshots/SS009.png)
*Stations info*

![Galactic Notes](screenshots/SS010.png)
*Galactic Notes & Info*

### Log
![Log info](screenshots/SS011.png)
*Log info*

![Log Details](screenshots/SS012.png)
*Log Details*

![Log Details Select Columns](screenshots/SS013.png)
*Log Details Select Columns*

![Log Details Select Columns Advanced](screenshots/SS014.png)
*Log Details Select Columns Advanced*

### Settings & Customization
![Settings Panel](screenshots/SS015.png)
*Comprehensive settings and configuration*

### In-Game Experience
![Overlay Tracking](screenshots/SS000.png)
*New transparent overlay "3 TABS" showing real-time progress for "VR and "Geforce Now players"*

### About & User Manual

![User Manual](screenshots/SS016.png)
*Comprehensive user manual and attributions*

![About Window](screenshots/SS017.png)
*Version info and credits*
