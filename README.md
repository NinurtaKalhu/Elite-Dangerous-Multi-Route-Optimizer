## 📜 License

**This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0-only)**

![License](https://img.shields.io/badge/License-AGPL%203.0%20only-red?style=for-the-badge&logo=gnu&logoColor=white)

### What this means in plain language:
- You are free to use, study, modify, and share EDRMN
- If you modify it and run it as a network service (web tool, server, etc.), you **must** provide the full source code to users
- Any derivative work or fork **must** also be licensed under AGPL-3.0-only
- The copyright notice and this license must remain in all copies

Full license text: [/LICENSE](LICENSE)

## ☕ Support EDMRN 

*> If you find this tool useful, consider supporting development: Support > its development with a coffee! ☕ > # [Buy me a coffee on Ko-fi](https://ko-fi.com/ninurtakalhu) or [Patreon](https://www.patreon.com/c/NinurtaKalhu) ☕*

[![KOFI](https://img.shields.io/badge/Ko--fi-Buy_me_a_coffee-FF5E5B?logo=kofi)](https://ko-fi.com/ninurtakalhu) [![patreon](https://img.shields.io/badge/Patreon-Support-FF424D?logo=patreon)](https://www.patreon.com/c/NinurtaKalhu)

**[Virus Total Scan Report](https://www.virustotal.com/gui/file-analysis/Y2I1NTYwZThlNDZiNjgzMGY1MGIwZDRhOTZlYmM4ZmU6MTc2NDM3NjYzMg==)**

# ED Multi Route Navigation (EDMRN) v2.2
**Optimize Your Elite Dangerous Exploration Routes with Advanced TSP Algorithms - Now Cross-Platform!**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org) [![License](https://img.shields.io/badge/License-AGPL%203.0%20only-red?style=flat-square&logo=gnu&logoColor=white)](LICENSE) [![Version](https://img.shields.io/badge/Version-2.2.0-orange)](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases) [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer)

## 🆕 WHAT'S NEW IN v2.2

### ✨ Cross-Platform Support
- **Full Linux & macOS compatibility**
- **Auto-detection** of journal paths on all platforms
- **Manual journal path** configuration in Settings
- **Path testing** and real-time monitor restart

### 🐛 Bug Fixes & Improvements
- **Stable 3D Map** - Fixed zoom and click issues
- **Enhanced error handling** - No more crashes on invalid paths
- **Optimized performance** - Better handling of large routes (200+ systems)
- **Improved user experience** - Better feedback and controls

## 🚀 Features

- **Advanced Route Optimization**: Uses Lin-Kernighan TSP algorithm for shortest paths
- **Real-time Journal Monitoring**: Auto-tracks your in-game progress (Cross-Platform)
- **3D Interactive Map**: Visualize your route in 3D space with smooth zoom/pan
- **Smart Body Tracking**: Track multiple signals per system
- **Modern GUI**: Built sleek dark/light themes
- **Find "USER MANUAL" in to "About page"**

## 📦 Download

### Latest Release: v2.2.0

📥 **Download**: [EDMRN_v2.2_Windows](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/latest)

**System Requirements**:
- Windows: .NET Framework 4.8+ (for .exe)
- Linux/macOS: Python 3.8+ (run from source)
- Elite Dangerous with Journal logging enabled

## 🛠️ Installation

### For End Users (Windows):
1. Download the latest `.exe` from [Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases)
2. Run `ED Multi Route Navigation v2.2.exe`
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
- Customize appearance (Dark/Light mode)
- Change color themes
- Configure journal path (Cross-Platform)

### 🎮 CMDR Features

- Auto CMDR Detection: Reads your commander name and credits from journal
- Real-time Tracking: Monitors FSDJump events automatically on all platforms
- Multi-body Support: Track multiple biological/geological signals per system
- Backup System: Automatic route status backups

## 🐛 Reporting Issues

Found a bug? Please [create an issue](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues) with:

- Elite Dangerous version
- Your operating system (Windows/Linux/macOS)
- Steps to reproduce
- Error message (if any)
- Journal file excerpt (if relevant)

## 👨‍💻 Developer
Ninurta Kalhu - Solo Developer & Elite Dangerous Exobiologist/Explorer

📧 Email: ninurtakalhu@gmail.com

🌐 X (twitter):  @NinurtaKalhu

🌐 GitHub: @NinurtaKalhu

💬 Discord: [Join our EDMRN community](https://discord.gg/jxVTyev8)

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

### What This Application Does NOT Do:
- ❌ No data collection or telemetry
- ❌ No network communication beyond update checks
- ❌ No personal information access
- ❌ No online requirements
- ❌ No hidden mining or malware

### File Access Summary:
| File Type | Access Reason | Data Usage |
|-----------|---------------|------------|
| `.log` files | Game journal reading | Auto-tracking |
| `.csv` files | Route data import/export | Route optimization |
| `.json` files | Settings and progress | Local configuration |

## 🌐 Cross-Platform Support

### Windows
- ✅ Full support - standalone .exe available
- ✅ Auto journal detection
- ✅ All features available

### Linux
- ✅ Full support - run from source
- ✅ Auto journal detection
- ✅ All features available
- ✅ Tested on Ubuntu, Fedora, Arch

### macOS
- ✅ Full support - run from source  
- ✅ Auto journal detection
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

###The CSV file must contain the following columns: system name, celestial body name, x, y, and z coordinates.

![SS1](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS1.png)

![SS2](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS2.png)

![SS3](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS3.png)

![SS4](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS4.png)

![SS5](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS5.png)

![SS6](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS6.png)
