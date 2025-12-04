###🚧🚧🚧Attention! Repo is currently under development for the new version; please use the v2.2 exe file.🚧🚧🚧

## 📜 License

**This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0-only)**

![License](https://img.shields.io/badge/License-AGPL%203.0%20only-red?style=for-the-badge&logo=gnu&logoColor=white)

### What this means in plain language:
- You are free to use, study and share EDMRN
- If you modify it and run it as a network service (web tool, server, etc.), you **must** provide the full source code to users
- Any derivative work or fork **must** also be licensed under AGPL-3.0-only
- The copyright notice and this license must remain in all copies

Full license text: [/LICENSE](LICENSE)

## ☕ Support EDMRN 

*> If you find this tool useful, consider supporting development: Support > its development with a coffee! ☕ > # [Buy me a coffee on Ko-fi](https://ko-fi.com/ninurtakalhu) or [Patreon](https://www.patreon.com/c/NinurtaKalhu) ☕*

[![KOFI](https://img.shields.io/badge/Ko--fi-Buy_me_a_coffee-FF5E5B?logo=kofi)](https://ko-fi.com/ninurtakalhu) [![patreon](https://img.shields.io/badge/Patreon-Support-FF424D?logo=patreon)](https://www.patreon.com/c/NinurtaKalhu)

**[Virus Total Scan Report](https://www.virustotal.com/gui/file/193214e4eefff07f7b89f758bb5f716faeca546ca8e8bc8486dc667cbd12170d?nocache=1)**

# ED Multi Route Navigation (EDMRN) v2.3.0
**Optimize Your Elite Dangerous Exploration Routes with Advanced TSP Algorithms - Now with In-Game Overlay!**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org) [![License](https://img.shields.io/badge/License-AGPL%203.0%20only-red?style=flat-square&logo=gnu&logoColor=white)](LICENSE) [![Version](https://img.shields.io/badge/Version-2.3.0-orange)](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases) [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer)

## 🆕 WHAT'S NEW IN v2.3.0

### ✨ In-Game Overlay System
- **Real-time overlay** showing current system, next target, and bodies to scan
- **Adjustable opacity** (50-100%) and size options (Small/Medium/Large)
- **Cross-platform overlay** compatible with Windows, Linux, and macOS
- **Always on top** while playing in Borderless Window mode
- **Draggable interface** - move anywhere on screen

### 🎮 Enhanced Auto-Tracking Features
- **Multi-Commander Support** - Switch between different commanders
- **Auto CMDR Detection** with activity timestamps
- **Improved journal monitoring** with better error recovery
- **Refresh commanders list** on demand

### 🔧 New Settings & Configuration
- **Auto-save System** - Configurable intervals (1/5/10 minutes)
- **Manual save trigger** with status indicator
- **Improved appearance controls** - smoother theme switching
- **Better error handling** and user feedback

### 📊 Performance Improvements
- **Optimized 3D map rendering** for large routes
- **Reduced memory usage** with better garbage collection
- **Faster CSV column validation**
- **Improved startup time**

## 🚀 Features

- **Advanced Route Optimization**: Uses Lin-Kernighan TSP algorithm for shortest paths
- **Real-time Journal Monitoring**: Auto-tracks your in-game progress (Cross-Platform)
- **3D Interactive Map**: Visualize your route in 3D space with smooth zoom/pan
- **In-Game Overlay**: See current progress while playing (Borderless Window required)
- **Smart Body Tracking**: Track multiple signals per system
- **Multi-Commander Support**: Switch between different commanders seamlessly
- **Modern GUI**: Built with sleek dark/light themes and color schemes
- **Auto-save System**: Automatic backup of route progress
- **Find "USER MANUAL" in the "About" page**

## 📦 Download

### Latest Release: v2.3.0

📥 **Download**: [EDMRN_v2.3_Windows](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/latest)

**System Requirements**:
- Windows: .NET Framework 4.8+ (for .exe version)
- Linux/macOS: Python 3.8+ (run from source)
- Elite Dangerous with Journal logging enabled
- For overlay: Elite Dangerous in Borderless Window mode

## 🛠️ Installation

### For End Users (Windows):
1. Download the latest `.exe` from [Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases)
2. Run `ED Multi Route Navigation v2.3.exe`
3. No installation required - portable application

### For Linux/macOS Users:
```bash
# Clone the repository
git clone https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer.git
cd Elite-Dangerous-Multi-Route-Optimizer

# Install dependencies
pip install -r requirements.txt

# Run the application
python edmrn_gui.py
```

## 🎮 Using the In-Game Overlay

### Setup:
1. Set Elite Dangerous to **Borderless Window** mode in graphics settings
2. In EDMRN Settings tab, click **"Start Overlay"**
3. Adjust opacity and size to your preference
4. Drag overlay anywhere on screen by its title bar

### Overlay Features:
- **Current System**: Your current location
- **Next System**: Next target in your route
- **Bodies to Scan**: List of biological/geological signals
- **Progress Tracker**: How many systems visited vs total
- **Distance Stats**: Total and traveled distance

## 🎮 Cross-Platform Journal Setup

### Automatic Detection:
EDMRN automatically detects Elite Dangerous journal paths on:
- **Windows**: `~/Saved Games/Frontier Developments/Elite Dangerous`
- **macOS**: `~/Library/Application Support/Frontier Developments/Elite Dangerous`
- **Linux**: `~/.local/share/Frontier Developments/Elite Dangerous`

### Manual Configuration:
1. Go to **Settings** tab
2. Set your **Manual Journal Path**
3. Click **"Test Journal Path"** to verify
4. Click **"Apply & Restart Monitor"** to activate

## 📋 Usage

**Route Optimization Tab:**
- Select your CSV file with X,Y,Z Columns (from Spansh or others)
- Set ship jump range
- Choose output columns
- Click "Optimize Route"

**Route Tracking Tab:**
- View 3D map of your route - zoom with mouse wheel, rotate with click+drag
- Auto-tracking via Elite Dangerous journal
- Auto status updates
- Auto copy next system to clipboard

**Settings Tab:**
- **Overlay Controls**: Start/stop overlay, adjust settings
- **Journal Settings**: Configure multi-commander support
- **Auto-save**: Set backup intervals
- **Appearance**: Customize themes and colors

### 🎮 CMDR Features

- **Auto CMDR Detection**: Reads your commander name and credits from journal
- **Multi-Commander Support**: Switch between different commanders
- **Real-time Tracking**: Monitors FSDJump events automatically on all platforms
- **Multi-body Support**: Track multiple biological/geological signals per system
- **Backup System**: Automatic route status backups with configurable intervals

## 🐛 Reporting Issues

Found a bug? Please [create an issue](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues) with:

- EDMRN version (v2.3.0)
- Your operating system (Windows/Linux/macOS version)
- Steps to reproduce
- Error message (if any)
- Journal file excerpt (if relevant)

## 👨‍💻 Developer
Ninurta Kalhu - Solo Developer & Elite Dangerous Exobiologist/Explorer

📧 Email: ninurtakalhu@gmail.com

🌐 X (twitter):  @NinurtaKalhu

🌐 GitHub: @NinurtaKalhu

💬 Discord: [Join our EDMRN community](https://discord.gg/DWvCEXH7ae)

Fly safe, Commander! 🚀✨

#Attention! This project is not affiliated with Frontier Developments plc.

## 🛡️ Security Notice: False Positive Warnings

### ⚠️ Why Antivirus Software May Flag This Application

Some antivirus programs may incorrectly identify ED Multi Route Navigation as potentially harmful. This is known as a **false positive** and is a common issue with PyInstaller-compiled Python applications.

#### 🔍 Technical Reasons for False Positives:

1. **PyInstaller Packaging Method**
   - The executable bundles Python interpreter + source code + libraries into a single file
   - This "packaging" behavior can appear suspicious to heuristic antivirus scanners

2. **Application Behavior Patterns**
   - **Journal File Monitoring**: Reads Elite Dangerous journal files for auto-tracking
   - **Clipboard Access**: Copies system names to clipboard for easy pasting in-game
   - **Background Threads**: Monitors game journal files in real-time
   - **File System Operations**: Creates and manages route data files
   - **Overlay System**: Creates transparent overlay windows

3. **Lack of Digital Signature**
   - As an open-source project, we don't use commercial code signing certificates
   - Unsigned executables often receive more scrutiny from security software

#### ✅ Safety Verification:

- **Full Source Code Transparency**: All code is publicly available for review
- **VirusTotal Reports**: Typically shows 75+/80 clean scans
- **No Malicious Code**: You can compile from source yourself
- **Open Source Community**: Code reviewed by multiple developers

#### 🛠️ If Your Antivirus Flags This Software:

1. **Add Exclusion**: Add the application to your antivirus exclusion list
2. **Verify Source**: Review the code and compile yourself if concerned
3. **Report False Positive**: Help improve detection by reporting to your antivirus vendor

**We take security seriously and guarantee this software contains no malicious code. The source is completely transparent for community verification.**

## 🔒 Privacy & Data Security

### What This Application Does:
- 📁 Reads Elite Dangerous journal files (game data only)
- 📋 Copies system names to clipboard (manual paste only)
- 💾 Saves route data locally (your computer only)
- 🌐 Checks for updates (GitHub API only)
- 🪟 Creates overlay window (game display only)

### What This Application Does NOT Do:
- ❌ No data collection or telemetry
- ❌ No network communication beyond update checks
- ❌ No personal information access
- ❌ No online requirements
- ❌ No hidden mining or malware
- ❌ No screen capturing or recording

### File Access Summary:
| File Type | Access Reason | Data Usage |
|-----------|---------------|------------|
| `.log` files | Game journal reading | Auto-tracking |
| `.csv` files | Route data import/export | Route optimization |
| `.json` files | Settings and progress | Local configuration |
| `.ico/.png` | Application icons | GUI display |

## 🌐 Cross-Platform Support

### Windows
- ✅ Full support - standalone .exe available
- ✅ Auto journal detection
- ✅ In-game overlay support
- ✅ All features available

### Linux
- ✅ Full support - run from source
- ✅ Auto journal detection (including Steam/Flatpak)
- ✅ In-game overlay support (X11/Wayland)
- ✅ All features available
- ✅ Tested on Ubuntu, Fedora, Arch

### macOS
- ✅ Full support - run from source  
- ✅ Auto journal detection
- ✅ In-game overlay support (Borderless Window)
- ✅ All features available
- ✅ Tested on macOS 12+

## 📦 Download & Installation

### 🟢 Recommended: Standalone Executable (Windows)  
**`ED_Multi_Route_Navigation.exe`** - Single file executable
- May trigger antivirus false positives
- Add to exclusions if needed

### 🔧 Advanced: Source Code (All Platforms)
**Compile from source** for maximum security verification

    pip install -r requirements.txt
    python edmrn_gui.py

## 🗺️ 3D Map Controls

- **Zoom**: Mouse wheel
- **Rotate**: Left click + drag
- **Pan**: Right click + drag
- **Select System**: Click on any star
- **Reset View**: Re-plot route

## 🎮 Overlay Controls

- **Move**: Drag title bar
- **Toggle Visibility**: Close button (reopen from EDMRN Settings)
- **Adjust Opacity**: Settings slider
- **Change Size**: Small/Medium/Large options

![SS1](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS1.png)

![SS2](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS2.png)

![SS3](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS3.png)

![SS4](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS4.png)

![SS5](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS5.png)

![SS6](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS6.png)
