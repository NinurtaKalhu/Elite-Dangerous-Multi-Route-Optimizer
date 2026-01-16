# 🚀 ED Multi Route Navigation (EDMRN) v3.1

**The Ultimate Route Optimization & Tracking Tool for Elite Dangerous**

Complete modular architecture with professional theme system, advanced route planning, and real-time tracking.

![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue) ![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-green) ![Version 3.1.0](https://img.shields.io/badge/Version-3.1.0-brightgreen) ![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D4) ![Status: Active](https://img.shields.io/badge/Status-Active-success)

---

## 📑 Table of Contents

- [What's New in v3.1](#-whats-new-in-v31)
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

## ✨ What's New in v3.1

### 🎯 Enhanced User Experience (v3.1.0 - January 2026)

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

### 🏗️ v3.0 Foundation - Complete Architecture Redesign

**Fully Modular Architecture**
- 15+ independent, maintainable modules
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
## 🚀 Key Features

### Core Functionality
- 🎯 **Smart Route Optimization** - TSP-based shortest path algorithm with configurable starting points
- 📍 **Interactive 3D Visualization** - Real-time 3D mini-map with zoom, rotate, and pan controls
- 🎮 **In-Game Overlay** - Transparent overlay with live progress tracking (Ctrl+O toggle)
- 📊 **Auto Journal Monitoring** - Real-time Elite Dangerous journal tracking with multi-commander support
- 💾 **Intelligent Auto-Save** - Configurable intervals (1/5/10 min) with atomic operations
- 🔄 **Visit History Tracking** - Persistent exploration history survives app restarts

### Advanced Features
- 🛣️ **Neutron Highway Router** - Advanced neutron jump routing with range optimization
- 🌌 **Galaxy Plotter** - Spansh Exact Router integration with fuel calculations
- 🔍 **Smart System Autocomplete** - Real-time Spansh (70M+ systems) API suggestions with EDSM fallback and 300ms debouncing
- 🎨 **11 PowerPlay Themes** - Elite Dangerous faction color schemes with automatic restart
- 📦 **Smart Backup System** - Atomic writes, automatic backups, integrity verification
- 🖥️ **GeForce Now Support** - Cloud gaming optimized with borderless mode detection

### Technical Excellence
- 🔧 **Modular Architecture** - 35+ independent modules for maintainability
- 🔒 **Thread-Safe Design** - Proper locking mechanisms throughout
- ⚡ **Optimized Performance** - Smart caching, debouncing, efficient memory usage
- 🛡️ **Robust Error Handling** - Comprehensive error recovery and logging

---

## 📦 Download & Installation

### 🎯 Recommended: Pre-built Executable (Windows)

**Latest Release: v3.1.0**

[📥 DOWNLOAD EDMRN v3.1.0](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/download/v3.1.0/EDMRN.v3.1.0.exe)

**Quick Start (Windows):**
1. Download `EDMRN_v3.1.0.exe` from [Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases)
2. Run the executable - no installation required!
3. Fully portable - runs from any location
4. All dependencies included

### 🔧 Run from Source (All Platforms)

**Requirements:**
- Python 3.13 or higher
- pip package manager
- Git (for cloning)

**Installation Steps:**

```bash
# Clone the repository
git clone https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer.git
cd Elite-Dangerous-Multi-Route-Optimizer

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

**Building Executable (Windows):**
```bash
# Install PyInstaller
pip install pyinstaller

# Run build script
build_edmrn.bat
```

---

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.13+ (for source installation)
- **RAM**: 4 GB
- **Storage**: 100 MB free space
- **Elite Dangerous**: Journal logging enabled

### Recommended Requirements
- **OS**: Windows 11 (64-bit)
- **RAM**: 8 GB
- **Monitor**: 1920x1080 or higher
- **Elite Dangerous**: Borderless Window mode (for overlay)

### Required Elite Dangerous Settings
1. Enable Journal logging (default: enabled)
2. Use Borderless Window mode for overlay functionality
3. Journal path: `%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous\`

---

## 📖 Quick Start Guide

### Step 1: Export Your Route
1. Use Spansh.co.uk to create your system list
2. Export as CSV with **required** columns: `System Name`, `X`, `Y`, `Z`
3. **Optional**: Include `Body Name` for biological/geological signals

**Note**: Only 4 columns are required (System Name, X, Y, Z). Body Name is optional but recommended for exploration routes.

### Step 2: Optimize Route
1. **Tab 1: Route Optimization**
   - Click "Browse" to select your CSV file
   - Enter ship jump range (e.g., 75.23 LY)
   - Optional: Set starting system for optimized pathing
   - Click "Optimize Route and Start Tracking"
   - Wait for TSP optimization to complete

### Step 3: Track Progress
1. **Tab 3: Route Tracking**
   - Interactive 3D map displays your optimized route
   - Systems update automatically via journal monitoring
   - Click systems to manually mark visited/skipped
   - Use quick actions:
     - **Copy Next**: Copy next system to clipboard
     - **Data Folder**: Open EDMRN data directory
     - **Open Excel**: View route in spreadsheet
     - **Load Backup**: Restore previous route state

### Step 4: Neutron Highway (Optional)
1. **Tab 2: Neutron Highway**
   - Enter source and destination systems (with autocomplete)
   - Set ship jump range and fuel tank capacity
   - Select neutron mode and efficiency
   - Click "Calculate Route" for optimized neutron routing
   - Export route or copy to clipboard

### Step 5: Galaxy Plotter (Optional)
1. **Tab 4: Galaxy Plotter**
   - Use Spansh Exact Router integration
   - Enter ship build from Coriolis.io or EDSY.org
   - Configure route preferences (neutron, boosts, etc.)
   - Get precise fuel consumption calculations
   - Export route for navigation

### Step 4: Use In-Game Overlay
1. **Tab 3: Settings → Overlay**
2. Click "Start Overlay" button
3. Configure overlay settings:
   - **Opacity**: 50-100% transparency
   - **Size**: Small/Medium/Large
   - **Position**: Drag overlay to preferred location
4. In Elite Dangerous (Borderless Window mode):
   - Press **Ctrl+O** to toggle overlay visibility
   - Overlay shows current system, next target, and bodies to scan
   - Real-time progress tracking with distance stats

### Step 5: Choose Your Theme
1. **Tab 3: Settings → Appearance**
2. Select from 11 PowerPlay faction themes:
   - Elite Dangerous (default)
   - Aisling Duval, Archon Delaine, Arissa Lavigny-Duval
   - Denton Patreus, Edmund Mahon, Felicia Winters
   - Li Yong-Rui, Pranav Antal, Zachary Hudson, Zemina Torval
3. App automatically restarts to apply theme
4. Enjoy your faction-themed EDMRN experience!

---

## 🎮 In-Game Overlay Features

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

- **Toggle**: Press **Ctrl+O** to show/hide overlay
- **Reposition**: Click and drag overlay to any screen position
- **Resize**: Choose Small/Medium/Large in settings
- **Opacity**: Adjust 50-100% transparency in settings
- **Always On Top**: Overlay stays visible over Elite Dangerous

### Overlay Tips

✅ **Best Performance:**
- Use Borderless Window mode in Elite Dangerous
- Disable VSync for better overlay responsiveness
- Place overlay in non-critical screen areas

✅ **GeForce Now Users:**
- Enable "Auto-Launch Overlay" in settings
- Borderless mode automatically detected
- Optimized for cloud gaming latency

⚠️ **Troubleshooting:**
- If overlay doesn't appear: Check Borderless Window mode
- If overlay won't drag: Restart overlay from settings
- If data not updating: Verify journal path in settings

---

## 🛠️ Settings & Configuration

### ⚙️ Overlay Settings
- **Start/Stop Overlay**: Toggle overlay visibility
- **Opacity Control**: 50-100% (default: 90%)
- **Size Selection**: Small/Medium/Large
- **Hotkey**: Ctrl+O (customizable in future versions)
- **Auto-Launch**: Start overlay with route optimization
- **Position Memory**: Remembers last overlay position

### 💾 Auto-Save System
- **Intervals**: 1/5/10 minutes or Never
- **Status Indicator**: Shows next save countdown
- **Manual Save**: Force save anytime with Ctrl+S
- **Atomic Operations**: Prevents data corruption
- **Auto-Backup**: Creates backup before each save
- **Recovery**: Automatic recovery on corrupt data detection

### 📝 Journal Monitoring
- **Auto-Detection**: Automatically finds Elite Dangerous journal
- **Multi-Commander**: Supports multiple CMDR profiles
- **Manual Path**: Custom journal location support
- **Real-Time Updates**: Instant system change detection
- **Status Display**: Shows current CMDR and location
- **Test Function**: Verify journal connection

### 🎨 Appearance & Themes
- **11 Faction Themes**: PowerPlay-inspired color schemes
- **Automatic Restart**: Seamless theme application
- **Color Consistency**: Professional dark UI throughout
- **Custom Fonts**: Elite Dangerous-style typography
- **High Contrast**: Optimized for long exploration sessions

### 🔧 Advanced Settings
- **Starting System**: Override for route optimization
- **Jump Range**: Precise to 0.01 LY
- **Backup Management**: Manual backup creation/restoration
- **Data Export**: CSV export with customizable columns
- **Log Level**: Adjust logging verbosity for troubleshooting

---

## 🌐 API Credits & Attribution

EDMRN relies on these excellent community services:

### Spansh - Elite Dangerous Tools
- **Usage**: 
  - Neutron highway route calculation
  - Galaxy plotter / exact router
  - System autocomplete (primary source)
- **API**: Route planning and system data
- **Website**: [spansh.co.uk](https://spansh.co.uk)
- **Attribution**: Required under Spansh terms of use
- **Optimizations**: 
  - 300ms debouncing for autocomplete
  - 1-hour caching to reduce server load
  - Minimum 3-character requirement

### EDSM - Elite Dangerous Star Map
- **Usage**: System name autocomplete (fallback source)
- **API**: System search and coordinate data
- **Website**: [edsm.net](https://www.edsm.net)
- **Attribution**: Required under EDSM terms of use
- **Rate Limiting**: Respectful API usage with caching


### API Usage Optimization

EDMRN implements responsible API usage:
- ✅ Smart caching reduces redundant requests
- ✅ Debouncing prevents request flooding
- ✅ Proper User-Agent headers for tracking
- ✅ Fallback mechanisms for reliability
- ✅ Rate limiting respects server resources

**Note**: EDMRN is not affiliated with EDSM or Spansh. We're grateful for their services!

---

### Performance Tips

- 🚀 Close other applications during route optimization
- 🚀 Use SSD for better file I/O performance
- 🚀 Disable antivirus real-time scanning for EDMRN folder
- 🚀 Keep only necessary tabs open
- 🚀 Clear old backups periodically to save space

### Antivirus False Positives

Some antivirus software may flag EDMRN.exe (common with PyInstaller-built apps):

✅ **Safe Options:**
1. Add EDMRN folder to antivirus exceptions
2. Run from source code instead of executable
3. Check [VirusTotal Report](https://www.virustotal.com/) for verification
4. Download only from official GitHub releases

### Getting More Help

- 💬 **Discord**: [EDMRN Community](https://discord.gg/DWvCEXH7ae) - fastest support
- 🐛 **GitHub Issues**: [Report bugs](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues)
- 📧 **Email**: ninurtakalhu@gmail.com
- 📖 **Wiki**: Detailed guides and tutorials (coming soon)

---

## 📁 Project Structure

```
EDMRN_v3.1/
├── edmrn/                      # Main application package
│   ├── app.py                 # Main GUI application & window management
│   ├── optimizer.py           # TSP route optimization engine
│   ├── tracker.py             # Route tracking & visit history system
│   ├── minimap.py             # 3D visualization with matplotlib
│   ├── overlay.py             # In-game overlay window system
│   ├── journal.py             # Journal file monitoring & parsing
│   ├── journal_operations.py  # Journal file operations & detection
│   ├── logger.py              # Centralized logging system
│   ├── backup.py              # Backup management & restoration
│   ├── autosave.py            # Auto-save functionality with atomics
│   ├── platform_detector.py   # Platform & GeForce Now detection
│   ├── exceptions.py          # Custom exception definitions
│   ├── utils.py               # Utility functions & helpers
│   ├── config.py              # Configuration management
│   ├── gui.py                 # GUI dialogs & components
│   ├── ui_components.py       # Reusable UI widgets
│   ├── theme_manager.py       # Theme switching & color management
│   ├── theme_editor.py        # Theme editor for customization
│   ├── route_management.py    # Route handling & CSV operations
│   ├── route_manager.py       # Route state management
│   ├── settings_manager.py    # Settings UI & persistence
│   ├── neutron_manager.py     # Neutron highway UI & controls
│   ├── neutron.py             # Neutron routing engine & Spansh API
│   ├── file_operations.py     # File I/O operations
│   ├── system_autocomplete.py # EDSM/Spansh autocomplete system
│   ├── autocomplete_entry.py  # Custom autocomplete widget
│   ├── themes/                # JSON theme definitions
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
│   └── __init__.py            # Package initialization & version
│
├── assets/                     # Application resources
│   ├── explorer_icon.ico      # Windows icon
│   └── explorer_icon.png      # Application icon
│
├── screenshots/                # Documentation screenshots
├── requirements.txt           # Python dependencies
├── version_info.txt           # Version metadata for builds
├── run.py                     # Application entry point
├── main.py                    # Alternative launcher
├── build_edmrn.bat           # Windows executable build script
├── edmrn.spec                # PyInstaller specification
├── CHANGELOG.md              # Version history & changes
├── LICENSE                    # AGPL-3.0 license
└── README.md                  # This file
```

### Key Modules Explained

**Core Application:**
- `app.py` - Main window, tab management, application lifecycle
- `optimizer.py` - Traveling Salesman Problem solver using scipy
- `tracker.py` - Visit tracking, system status management

**User Interface:**
- `gui.py` - Dialogs (About, Credits, Help)
- `ui_components.py` - Tab creation, reusable widgets
- `theme_manager.py` - Theme loading, color generation
- `settings_manager.py` - Settings tab UI

**Route Planning:**
- `neutron_manager.py` + `neutron.py` - Neutron highway routing
- `route_management.py` + `route_manager.py` - Route state & CSV
- `SpanshRouter/` - Galaxy plotter integration

**Data Management:**
- `backup.py` + `autosave.py` - Backup system with atomic writes
- `journal.py` + `journal_operations.py` - Journal monitoring
- `file_operations.py` - File I/O utilities

**Overlay System:**
- `overlay.py` - Transparent window overlay
- `platform_detector.py` - GeForce Now & borderless detection

---

### 📞 Get Help & Connect

| Platform | Purpose | Link |
|----------|---------|------|
| 💬 **Discord** | Live chat, support, discussion | [Join Server](https://discord.gg/DWvCEXH7ae) |
| 🐛 **GitHub Issues** | Bug reports, feature requests | [Open Issue](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues) |
| 📧 **Email** | Direct developer contact | ninurtakalhu@gmail.com |
| 🐦 **X (Twitter)** | Updates and announcements | [@NinurtaKalhu](https://twitter.com/NinurtaKalhu) |

### 🌟 Support Development

If EDMRN enhances your Elite Dangerous experience, consider supporting development:

- ☕ [Ko-fi](https://ko-fi.com/ninurtakalhu) - One-time tips
- 🎯 [Patreon](https://www.patreon.com/c/NinurtaKalhu) - Monthly support

**Your support helps:**
- ✅ Maintain and improve EDMRN
- ✅ Add new features and optimizations
- ✅ Provide faster support and updates
- ✅ Keep the project ad-free and open-source

---

## 🛡️ Security & Privacy

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
- **Route Data**: `%USERPROFILE%\Documents\EDMRN_Route_Data\`
- **Backups**: `EDMRN_Route_Data\backups\`
- **Logs**: `EDMRN_Route_Data\logs\`
- **Settings**: `EDMRN_Route_Data\settings.json`

**No cloud storage. No remote access. Your data stays yours.**

### ⚠️ Antivirus False Positives

PyInstaller-built executables sometimes trigger false positives:

**Why this happens:**
- PyInstaller bundles Python interpreter
- Some AV heuristics flag unknown executables
- EDMRN is new and not widely distributed yet

**Verification Steps:**
1. ✅ Download only from official [GitHub Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases)
2. ✅ Check file hash against release notes
3. ✅ Scan with [VirusTotal](https://www.virustotal.com/)
4. ✅ Run from source if concerned (see installation)

**Safe Actions:**
- Add EDMRN folder to antivirus exceptions
- Use Windows Defender SmartScreen "Run anyway"
- Report false positive to your AV vendor

---

## 📄 License

**GNU Affero General Public License v3.0 (AGPL-3.0-only)**

### What This Means:

✅ **You CAN:**
- Use EDMRN freely for personal or commercial purposes
- Modify and customize EDMRN to your needs
- Share EDMRN with others
- Run EDMRN as part of your workflow

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

## 👨‍💻 Developer

**Ninurta Kalhu (S.C.)** - Solo Developer & Elite Dangerous CMDR

Passionate explorer building tools for the Elite Dangerous community.

### Connect:
- 💬 **Discord**: [EDMRN Community](https://discord.gg/DWvCEXH7ae)
- 📧 **Email**: ninurtakalhu@gmail.com
- 🐦 **X (Twitter)**: [@NinurtaKalhu](https://twitter.com/NinurtaKalhu)
- 🐙 **GitHub**: [NinurtaKalhu](https://github.com/NinurtaKalhu)

### Development Stats:
- 📅 Project started: 2025
- 💻 Lines of code: 20,000+
- 🎨 Themes created: 11
- 📦 Modules: 35+
- ⭐ Made with ❤️ for Elite Dangerous

---

## 📸 Screenshots

### Main Interface
![Route Optimization](screenshots/SS1.png)
*Route optimization with CSV import and TSP algorithm*

![Route Tracking with 3D Map](screenshots/SS2.png)
*Interactive 3D map with real-time journal tracking*

### Advanced Features
![Neutron Highway Router](screenshots/SS3.png)
*Neutron highway routing with autocomplete*

![Backup Management](screenshots/SS4.png)
*Smart backup system with restore functionality*

### Settings & Customization
![Settings Panel](screenshots/SS5.png)
*Comprehensive settings and configuration*

### In-Game Experience
![Overlay Tracking](screenshots/SS6.png) ![Overlay Neutron](screenshots/SS7.png)
*Transparent overlay with real-time progress (Ctrl+O toggle)*

### About & Credits
![About Window](screenshots/SS8.png)
*Version info and credits*

![User Manual](screenshots/SS9.png)
*Comprehensive user manual and attributions*

---

## 🚀 Version History Highlights

### v3.1.0 (January 2026) - Current Release
- ✅ Visit History System with persistent tracking
- ✅ Smart Backup with atomic operations
- ✅ GeForce Now overlay controls
- ✅ Borderless mode (experimental)
- ✅ Enhanced autocomplete
- ✅ API optimizations
- ✅ Improved dropdown UX with window tracking
- ✅ EDSM & Spansh attribution
- ✅ Galaxy Plotter integration (Spansh Router)
- ✅ Precise fuel consumption calculations
- ✅ Ship build integration (Coriolis/EDSY)
- ✅ Smart system autocomplete (EDSM/Spansh)
- ✅ Real-time suggestions with caching
- ✅ Enhanced neutron routing

### v3.0.0 (November 2025) - Major Redesign
- ✅ Complete modular architecture (15+ modules)
- ✅ Revolutionary 11-theme system
- ✅ Backup system restructuring
- ✅ Overlay system redesign
- ✅ Thread-safe design throughout

---


## 🙏 Acknowledgments

### Special Thanks To:

**Data Providers:**
- [EDSM](https://www.edsm.net) - System data and autocomplete
- [Spansh](https://spansh.co.uk) - Route calculations and tools

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

## 📞 Quick Links

| Resource | URL |
|----------|-----|
| 🏠 **GitHub Repository** | [github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer) |
| 📥 **Latest Release** | [Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases) |
| 💬 **Discord Community** | [discord.gg/DWvCEXH7ae](https://discord.gg/DWvCEXH7ae) |
| 🐛 **Bug Reports** | [GitHub Issues](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues) |
| 📖 **Documentation** | [Wiki](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/wiki) (coming soon) |
| ☕ **Support Development** | [Ko-fi](https://ko-fi.com/ninurtakalhu) |

---

<div align="center">

**Fly safe, Commander! o7**

*"In the black, every lightyear counts."*

---

Made with ❤️ by [Ninurta Kalhu](https://github.com/NinurtaKalhu) for the Elite Dangerous community

**EDMRN v3.1.0** | January 2026 | [AGPL-3.0](LICENSE)

</div>
