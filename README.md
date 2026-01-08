# 🎉 ED Multi Route Navigation (EDMRN) v3.0 - Major Redesign!

The Ultimate Route Optimization & Tracking Tool for Elite Dangerous - Complete Modular Edition with Professional Theme System

![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue) ![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-green) ![Version 3.0](https://img.shields.io/badge/Version-3.0-brightgreen) ![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D4)

---

## ✨ BRAND NEW IN v3.0 - COMPLETE ARCHITECTURE REDESIGN!

### 🏗️ Fully Modular Architecture
• Complete refactoring into 15+ independent modules
• Separated concerns for maintainability
• Thread-safe design with proper locking mechanisms
• Better performance and memory management

### 🎨 Revolutionary Theme System
• 11 Elite Dangerous PowerPlay faction-themed color schemes
• JSON-based CustomTkinter native themes
• Color tone generation algorithm
• Faction themes: Elite Dangerous, Aisling Duval, Archon Delaine, Arissa Lavigny Duval, Denton Patreus, Edmund Mahon, Felicia Winters, Li Yong Rui, Pranav Antal, Zachary Hudson, Zemina Torval

### ⚡ Backup System Restructuring
• Complete backup system rewrite
• Improved error handling and recovery
• Better coordinate parsing and validation
• Enhanced backup file organization

### 🚀 Overlay System Redesign
• Improved transparency and positioning
• Better in-game detection
• More reliable window management

### 🛣️ Neutron Highway Integration
• Advanced neutron jump routing
• Optimized route planning with neutron networks

---

## 🚀 Key Features

• 🎯 **Smart Route Optimization**: TSP-based shortest path algorithm
• 📍 **Interactive 3D Visualization**: Real-time 3D mini-map with zoom/rotate
• 🎮 **In-Game Overlay**: Transparent overlay showing current progress
• 📊 **Auto Journal Monitoring**: Real-time tracking of your Elite Dangerous progress
• 💾 **Auto-Save & Backup**: Configurable auto-save intervals
• 👥 **Multi-Commander Support**: Switch between commanders seamlessly
• 🎨 **11 Themed UIs**: Elite Dangerous PowerPlay faction color schemes with smart restart
• 🔧 **Modular Design**: Easy to maintain and extend
• 🛣️ **Neutron Highway Support**: Advanced neutron routing capabilities

---

## 📦 Download & Installation

### 🎯 Recommended: Pre-built Executable (Windows)

[Download EDMRN v3.0](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/download/v3.0/EDMRN_v3.0_Windows.zip)

**Quick Start (Windows):**
1. Download `EDMRN_v3.0_Windows.zip` from [Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/tag/v3.0)
2. Extract to any folder
3. Run `EDMRN.exe`
4. No installation required - fully portable!

### 🔧 Run from Source (All Platforms)

#### Clone the repository
```bash
git clone https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer.git
cd Elite-Dangerous-Multi-Route-Optimizer
```

#### Install dependencies
```bash
pip install -r requirements.txt
```

#### Run the application
```bash
python run.py
```

**Requirements:**
• Python 3.13 or higher
• Elite Dangerous with Journal logging enabled
• CSV export from Spansh, EDDiscovery, or EDMC

---

## 📖 Quick Start Guide

### Step 1: Export Your Route
1. Use EDDiscovery, EDMC, or Spansh.co.uk to create your system list
2. Export as CSV with columns: `System Name`, `X`, `Y`, `Z`
3. Optional: Include `Body Name` for biological/geological signals

### Step 2: Optimize Route
1. **Tab 1: Route Optimization**
   - Select your CSV file (Browse button)
   - Enter ship jump range (e.g., 70.0 LY)
   - Optional: Set starting system
   - Click "Optimize Route and Start Tracking"

### Step 3: Track Progress
1. **Tab 2: Route Tracking**
   - 3D map automatically displays your route
   - Systems update automatically via journal monitoring
   - Click systems to manually update status
   - Use buttons: Copy Next, Data Folder, Open Excel, Load Backup

### Step 4: Use In-Game Overlay
1. **Tab 3: Settings → Overlay**
2. Click "Start Overlay"
3. In Elite Dangerous (Borderless Window mode):
   - Press Ctrl+O to toggle overlay
   - Drag overlay to reposition
   - View current system, next target, bodies to scan

### Step 5: Choose Your Theme
1. **Tab 3: Settings → Appearance**
2. Select from 11 PowerPlay faction themes
3. App will automatically restart to apply theme
4. Enjoy your faction-themed EDMRN!

---

## 🎮 In-Game Overlay Features

| Feature | Description | Usage |
|---------|-------------|-------|
| Current System | Your current location with status indicator | Real-time tracking |
| Next Target | Next system in optimized route | Navigation |
| Bodies to Scan | Biological/geological signals in current system | Exploration |
| Progress Tracker | Systems visited/skipped/remaining | Route management |
| Distance Stats | Total and traveled distance | Planning |
| Quick Controls | Toggle with Ctrl+O, drag to move | Accessibility |

**Overlay Tips:**
• Works best in Borderless Window mode
• Adjust opacity in Settings (50-100%)
• Choose from Small/Medium/Large sizes
• Always stays on top of game window

---

## 🛠️ Settings & Configuration

### ⚙️ Overlay Settings
• Start/Stop overlay
• Adjust opacity (50-100%)
• Change size (Small/Medium/Large)
• Toggle with Ctrl+O hotkey

### 💾 Auto-Save System
• Configurable intervals: 1/5/10 minutes or Never
• Status indicator with next save time
• Manual save button
• Automatic backup system

### 📝 Journal Monitoring
• Auto-detects Elite Dangerous journal path
• Multi-commander support
• Manual path configuration
• Test and apply settings

### 🎨 Appearance
• 11 Themes: Elite Dangerous PowerPlay faction colors
• Real-time theme switching with automatic restart
• Color tone generation from faction colors
• Professional dark UI aesthetics

---

## 📁 Project Structure

```
EDMRN_v3.0/
├── edmrn/                      # Main application package
│   ├── app.py                 # Main GUI application
│   ├── optimizer.py           # Route optimization engine (TSP)
│   ├── tracker.py             # Route tracking system
│   ├── minimap.py             # 3D visualization module
│   ├── overlay.py             # In-game overlay system
│   ├── journal.py             # Journal monitoring
│   ├── debug.py               # Debug and error tracking
│   ├── debug_gui.py           # Debug console GUI
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging system
│   ├── backup.py              # Backup management (RESTRUCTURED)
│   ├── autosave.py            # Auto-save functionality
│   ├── platform_detector.py   # Platform detection
│   ├── exceptions.py          # Custom exceptions
│   ├── utils.py               # Utility functions
│   ├── gui.py                 # GUI components
│   ├── theme_manager.py       # Theme switching and management (NEW)
│   ├── route_management.py    # Route handling and UI (NEW)
│   ├── settings_manager.py    # Settings and configuration (NEW)
│   ├── neutron_manager.py     # Neutron highway routing (NEW)
│   ├── journal_operations.py  # Journal file operations (NEW)
│   ├── file_operations.py     # File I/O operations (NEW)
│   ├── neutron.py             # Neutron routing engine (NEW)
│   ├── themes/                # JSON-based theme definitions (NEW)
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
│   ├── backgrounds/           # Background assets
│   └── __init__.py            # Package initialization
├── assets/                     # Application assets
│   ├── explorer_icon.ico
│   └── explorer_icon.png
├── CHANGELOG.md               # Detailed changelog (NEW)
├── requirements.txt           # Python dependencies
├── version_info.txt           # Version information
├── run.py                     # Application entry point
├── main.py                    # Main launcher
├── build.bat                  # Build Windows .exe
└── README.md                  # This file
```

---

## 🎯 Keyboard Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| Ctrl+D or F12 | Open Debug Console | Anywhere in EDMRN |
| Ctrl+O | Toggle In-Game Overlay | Elite Dangerous (with overlay active) |
| Mouse Wheel | Zoom 3D Map | Route Tracking tab |
| Left Click + Drag | Rotate 3D Map | Route Tracking tab |

---

## 🔧 Troubleshooting

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| CSV not loading | Ensure columns: System Name, X, Y, Z |
| Journal not detected | Check Settings → Journal → Test Path |
| Overlay not visible | Press Ctrl+O, check Elite is Borderless Window |
| 3D map blank | Install matplotlib: `pip install matplotlib` |
| Performance issues | Reduce 3D map detail, close other applications |
| Theme not applying | Check if app restarted automatically |
| Old backups not loading | May need migration due to v3.0 restructuring |

### Debug Mode
Press Ctrl+D or F12 anytime to open the debug console:
• View real-time errors and warnings
• Check system performance
• Export debug data for support
• Monitor application health

---

## 🤝 Community & Support

### 📞 Get Help
• **Discord**: [EDMRN Community](https://discord.gg/DWvCEXH7ae) - Live support and discussion
• **GitHub Issues**: [Report bugs](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues)
• **Email**: [ninurtakalhu@gmail.com](mailto:ninurtakalhu@gmail.com)

### 🌟 Support Development
If you find EDMRN useful, consider supporting its development:
• [Ko-fi](https://ko-fi.com/ninurtakalhu)
• [Patreon](https://www.patreon.com/c/NinurtaKalhu)

---

## 🛡️ Security & Privacy

### ✅ What EDMRN Does:
• Reads Elite Dangerous journal files for auto-tracking
• Saves route data locally (Documents/EDMRN_Route_Data/)
• Creates overlay window for in-game display
• Copies system names to clipboard (manual paste only)

### ❌ What EDMRN Does NOT Do:
• No data collection or telemetry
• No network communication (except update checks)
• No personal information access
• No online requirements

### ⚠️ "Maybe!" Antivirus False Positives:
Some antivirus software may flag the executable (false positive common with PyInstaller). You can:
1. Add exception to your antivirus
2. Run from source code
3. Check [VirusTotal Report](https://www.virustotal.com/)

---

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0-only)

**What this means:**
• You are free to use and share EDMRN
• If you modify it and run it as a network service, you must provide source code
• Derivative works must also be AGPL-3.0-only
• Full license: [/LICENSE](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/LICENSE)

---

## 👨‍💻 Developer

**Ninurta Kalhu (S.C.)** - Solo Developer & Elite Dangerous Explorer

• 📧 Email: [ninurtakalhu@gmail.com](mailto:ninurtakalhu@gmail.com)
• 🐦 X (Twitter): [@NinurtaKalhu](https://twitter.com/NinurtaKalhu)
• 💻 GitHub: [@NinurtaKalhu](https://github.com/NinurtaKalhu)
• 💬 Discord: [EDMRN Community](https://discord.gg/DWvCEXH7ae)

---

## 📸 Screenshots

### Route Optimization Tab
*Optimizing 490-system exploration route*

### Route Tracking with 3D Map
*Interactive 3D visualization with theme colors*

### In-Game Overlay
*Transparent overlay with current system and progress tracking*

### Theme System
*11 PowerPlay faction themes with automatic restart*

### Debug Console
*Real-time error tracking and diagnostics*

### Settings Tab
*Configuration and overlay management*

---

## 🚀 Recent Changes (v3.0)

### Major Architecture Redesign
- ✅ Modular architecture with 7 extracted modules
- ✅ Complete backup system restructuring
- ✅ Revolutionary 11-theme PowerPlay faction system
- ✅ Smart restart mechanism for theme switching
- ✅ Neutron highway integration
- ✅ Overlay system redesign
- ✅ Load backup system rewrite
- ✅ 200+ syntax error fixes
- ✅ Comprehensive error handling improvements

**See [CHANGELOG.md](CHANGELOG.md) for complete v3.0 details!**

---

Fly safe, Commander! o7

*"In the black, every lightyear counts."*
