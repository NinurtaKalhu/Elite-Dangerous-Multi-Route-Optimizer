

## 🎉 ED Multi Route Navigation (EDMRN) v2.3.0 - NOW AVAILABLE!

**The Ultimate Route Optimization & Tracking Tool for Elite Dangerous - Complete Modular Edition**

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://www.python.org/downloads/) [![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL%203.0%20only-red.svg)](LICENSE) [![Version](https://img.shields.io/badge/Version-2.3.0-e68e02)](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/tag/v2.3.0) [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-green)](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer) 

## ✨ **BRAND NEW IN v2.3.0 - COMPLETE REWRITE!**

### 🏗️ **Fully Modular Architecture**
- **Complete code reorganization** into 15+ independent modules
- **Thread-safe design** with proper locking mechanisms
- **Enhanced error handling** with debug system
- **Better performance** and memory management

### 🎯 **Advanced Debug System**
- **Real-time error tracking** with stack traces
- **Debug GUI console** (Ctrl+D or F12)
- **Error statistics** by category (GUI, Thread, I/O, Network)
- **Export capability** for technical support

### 🔧 **Professional Packaging**
- **Single-file executable** for Windows
- **Source distribution** for all platforms
- **Easy installation** with comprehensive documentation
- **Auto-update notification** system

### 📊 **Performance Optimizations**
- **Optimized distance matrix** calculations 
- **Memory-efficient 3D map** rendering
- **Faster CSV processing** with pandas optimizations
- **Reduced startup time**

## 🚀 **Key Features**

- **🎯 Smart Route Optimization**: TSP-based shortest path algorithm
- **📍 Interactive 3D Visualization**: Real-time 3D mini-map with zoom/rotate
- **🎮 In-Game Overlay**: Transparent overlay showing current progress (Ctrl+O)
- **📊 Auto Journal Monitoring**: Real-time tracking of your Elite Dangerous progress
- **🐛 Advanced Debug Console**: Professional error tracking and diagnostics
- **💾 Auto-Save & Backup**: Configurable auto-save intervals
- **👥 Multi-Commander Support**: Switch between commanders seamlessly
- **🎨 Customizable UI**: Dark/Light themes with multiple color schemes
- **🔧 Modular Design**: Easy to maintain and extend

## 📦 **Download & Installation**

### **🎯 Recommended: Pre-built Executable (Windows)**
[![Download EDMRN v2.3.0](https://img.shields.io/badge/Download-EDMRN_v2.3.0_Windows-00cc44?style=for-the-badge&logo=windows)](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/download/v2.3.0/EDMRN_v2.3.0_Windows.zip)

**Quick Start (Windows):**
1. Download `EDMRN_v2.3.0_Windows.zip` from [Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/tag/v2.3.0)
2. Extract to any folder
3. Run `EDMRN.exe`
4. No installation required - fully portable!

### **🔧 Run from Source (All Platforms)**

## Clone the repository
    git clone https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer.git
    cd Elite-Dangerous-Multi-Route-Optimizer
## Install dependencies
    pip install -r requirements.txt
## Run the application

    python run.py

**Requirements:**
- Python 3.13 or higher
- Elite Dangerous with Journal logging enabled
- CSV export from Spansh

## 📖 **Quick Start Guide**

### **Step 1: Export Your Route**
1. Use **EDDiscovery**, **EDMC**, or **Spansh.co.uk** to create your system list
2. Export as CSV with columns: `System Name`, `X`, `Y`, `Z`
3. Optional: Include `Body Name` for biological/geological signals

### **Step 2: Optimize Route**
1. **Tab 1: Route Optimization**
   - Select your CSV file (Browse button)
   - Enter ship jump range (e.g., 70.0 LY)
   - Optional: Set starting system
   - Click **"Optimize Route and Start Tracking"**

### **Step 3: Track Progress**
1. **Tab 2: Route Tracking**
   - 3D map automatically displays your route
   - Systems update automatically via journal monitoring
   - Click systems to manually update status
   - Use buttons: Copy Next, Data Folder, Open Excel, Load Backup

### **Step 4: Use In-Game Overlay**
1. **Tab 3: Settings → Overlay**
2. Click **"Start Overlay"**
3. In Elite Dangerous (Borderless Window mode):
   - Press **Ctrl+O** to toggle overlay
   - Drag overlay to reposition
   - View current system, next target, bodies to scan

## 🎮 **In-Game Overlay Features**

| Feature | Description |
|---------|-------------|
| **Current System** | Your current location with status indicator |
| **Next Target** | Next system in optimized route |
| **Bodies to Scan** | Biological/geological signals in current system |
| **Progress Tracker** | Systems visited/skipped/remaining |
| **Distance Stats** | Total and traveled distance |
| **Quick Controls** | Toggle with Ctrl+O, drag to move |

**Overlay Tips:**
- Works best in **Borderless Window** mode
- Adjust opacity in Settings (50-100%)
- Choose from Small/Medium/Large sizes
- Always stays on top of game window

## 🛠️ **Settings & Configuration**

### **⚙️ Overlay Settings**
- Start/Stop overlay
- Adjust opacity (50-100%)
- Change size (Small/Medium/Large)
- Toggle with Ctrl+O hotkey

### **💾 Auto-Save System**
- Configurable intervals: 1/5/10 minutes or Never
- Status indicator with next save time
- Manual save button
- Automatic backup system

### **📝 Journal Monitoring**
- Auto-detects Elite Dangerous journal path
- Multi-commander support
- Manual path configuration
- Test and apply settings

### **🎨 Appearance**
- Theme: Dark, Light, or System
- Color schemes: Green, Blue, Dark Blue
- Real-time theme switching

## 📁 **Project Structure**

```
EDMRN_v2.3.0/
├── edmrn/                 # Main application package
│   ├── app.py            # Main GUI application
│   ├── optimizer.py      # Route optimization engine
│   ├── tracker.py        # Route tracking system
│   ├── minimap.py        # 3D visualization module
│   ├── overlay.py        # In-game overlay system
│   ├── journal.py        # Journal monitoring
│   ├── debug.py          # Debug and error tracking
│   ├── debug_gui.py      # Debug console GUI
│   ├── config.py         # Configuration management
│   ├── logger.py         # Logging system
│   ├── backup.py         # Backup management
│   ├── autosave.py       # Auto-save functionality
│   ├── platform.py       # Platform detection
│   ├── exceptions.py     # Custom exceptions
│   ├── utils.py          # Utility functions
│   ├── gui.py            # GUI components
│   └── __init__.py       # Package initialization
├── assets/               # Application assets
│   ├── explorer_icon.ico
│   └── explorer_icon.png
├── requirements.txt      # Python dependencies
├── run.py               # Application entry point
├── main.py              # Main launcher
└── README.md            # This file
```

## 🎯 **Keyboard Shortcuts**

| Shortcut | Action | Where |
|----------|--------|-------|
| **Ctrl+D** or **F12** | Open Debug Console | Anywhere in EDMRN |
| **Ctrl+O** | Toggle In-Game Overlay | Elite Dangerous (with overlay active) |
| **Mouse Wheel** | Zoom 3D Map | Route Tracking tab |
| **Left Click + Drag** | Rotate 3D Map | Route Tracking tab |

## 🔧 **Troubleshooting**

### **Common Issues & Solutions**

| Issue | Solution |
|-------|----------|
| **CSV not loading** | Ensure columns: `System Name`, `X`, `Y`, `Z` |
| **Journal not detected** | Check Settings → Journal → Test Path |
| **Overlay not visible** | Press Ctrl+O, check Elite is Borderless Window |
| **3D map blank** | Install matplotlib: `pip install matplotlib` |
| **Performance issues** | Reduce 3D map detail, close other applications |

### **Debug Mode**
Press **Ctrl+D** or **F12** anytime to open the debug console:
- View real-time errors and warnings
- Check system performance
- Export debug data for support
- Monitor application health

## 🤝 **Community & Support**

### **📞 Get Help**
- **Discord**: [EDMRN Community](https://discord.gg/DWvCEXH7ae) - Live support and discussion
- **GitHub Issues**: [Report bugs](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues)
- **Email**: ninurtakalhu@gmail.com

### **🌟 Support Development**
If you find EDMRN useful, consider supporting its development:

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy_me_a_coffee-FF5E5B?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/ninurtakalhu) [![Patreon](https://img.shields.io/badge/Patreon-Support-FF424D?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/c/NinurtaKalhu)

## 🛡️ **Security & Privacy**

### **✅ What EDMRN Does:**
- Reads Elite Dangerous journal files for auto-tracking
- Saves route data locally (Documents/EDMRN_Route_Data/)
- Creates overlay window for in-game display
- Copies system names to clipboard (manual paste only)

### **❌ What EDMRN Does NOT Do:**
- No data collection or telemetry
- No network communication (except update checks)
- No personal information access
- No online requirements

### **⚠️ "Maybe!" Antivirus False Positives:**
Some antivirus software may flag the executable (false positive common with PyInstaller). You can:
1. Add exception to your antivirus
2. Run from source code
3. Check [VirusTotal Report](https://www.virustotal.com)

## 📄 **License**

**This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0-only)**

### What this means:
- You are free to use and share EDMRN
- If you modify it and run it as a network service, you must provide source code
- Derivative works must also be AGPL-3.0-only
- Full license: [/LICENSE](LICENSE)

## 👨‍💻 **Developer**

**Ninurta Kalhu (S.C.)** - Solo Developer & Elite Dangerous Explorer

- 📧 Email: ninurtakalhu@gmail.com
- 🐦 X (Twitter): [@NinurtaKalhu](https://twitter.com/NinurtaKalhu)
- 💻 GitHub: [@NinurtaKalhu](https://github.com/NinurtaKalhu)
- 💬 Discord: [EDMRN Community](https://discord.gg/DWvCEXH7ae)

---

## 📸 **Screenshots**

| Route Optimization | 3D Mini-Map | In-Game Overlay |
|-------------------|-------------|-----------------|
| ![Optimization](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS1.png) | ![MiniMap](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS2.png) | ![Overlay](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS3.png) |

| Debug Console | Settings | Route Tracking |
|---------------|----------|----------------|
| ![Debug](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS4.png) | ![Settings](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS5.png) | ![Tracking](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS6.png) |

---

<div align="center">

**Fly safe, Commander! o7**

*"In the black, every lightyear counts."*

</div>

---

# ⚠️ **Disclaimer**
**This project is not affiliated with, endorsed by, or connected to Frontier Developments plc. Elite Dangerous is a registered trademark of Frontier Developments plc.**
```
