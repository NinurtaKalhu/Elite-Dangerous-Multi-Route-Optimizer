## ☕ Support EDMRN 

*> If you find this tool useful, consider supporting development: Support > its development with a coffee! ☕ > # [Buy me a coffee on Ko-fi](https://ko-fi.com/ninurtakalhu) or [Patreon](https://www.patreon.com/c/NinurtaKalhu) ☕*

[![KOFI](https://img.shields.io/badge/Ko--fi-Buy_me_a_coffee-FF5E5B?logo=kofi)](https://ko-fi.com/ninurtakalhu) [![patreon](https://img.shields.io/badge/Patreon-Support-FF424D?logo=patreon)](https://www.patreon.com/c/NinurtaKalhu)

**[Virus Total Scan Report](https://www.virustotal.com/gui/file/193214e4eefff07f7b89f758bb5f716faeca546ca8e8bc8486dc667cbd12170d?nocache=1)**

# ED Multi Route Navigation (EDMRN) v2.0
**Optimize Your Elite Dangerous Exploration Routes with Advanced TSP Algorithms**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org) [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) [![Version](https://img.shields.io/badge/Version-2.1.0-orange)](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases)

## 🚀 Features

- **Advanced Route Optimization**: Uses Lin-Kernighan TSP algorithm for shortest paths
- **Real-time Journal Monitoring**: Auto-tracks your in-game progress
- **3D Interactive Map**: Visualize your route in 3D space
- **Smart Body Tracking**: Track multiple signals per system
- **Modern GUI**: Built sleek dark/light themes
- **Find "USER MANUAL" in to "About page"**

## 📦 Download

### Latest Release: v2.0.0

📥 **Download**: [EDMRN_v2.0_Windows](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases/latest)

**System Requirements**:
- .NET Framework 4.8+
- Elite Dangerous with Journal logging enabled

## 🛠 Installation

### For End Users:
1. Download the latest `.exe` from [Releases](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/releases)
2. Run `ED Multi Route Navigation v2.0.exe`
3. No installation required - portable application

---------------------------------------------------------------------------------------------------------

### 📋 Usage

**Route Optimization Tab:**

- Select your CSV file with X,Y,Z Columns (from Spansh or anothers)
- Set ship jump range
- Choose output columns
- Click "Optimize Route"

**Route Tracking Tab:**

- View 3D map of your route and zoom in/out with mouse scroll-lock
- Auto-tracking via Elite Dangerous journal
- Auto status updates
- Auto Copy next system to clipboard

**Settings Tab:**

- Customize appearance (Dark/Light mode)
- Change color themes

### 🎮 CMDR Features

- Auto CMDR Detection: Reads your commander name and credits from journal
- Real-time Tracking: Monitors FSDJump events automatically
- Multi-body Support: Track multiple biological/geological signals per system
- Backup System: Automatic route status backups


### **🐛 Reporting Issues**

Found a bug? Please [create an issue](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/issues) with:

- Elite Dangerous version
- Steps to reproduce
- Error message (if any)
- Journal file excerpt (if relevant)



👨‍💻 Developer
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


## 📦 Download & Installation

### 🟢 Recommended: Standalone Executable  
**`ED_Multi_Route_Navigation.exe`** - Single file executable
- May trigger antivirus false positives
- Add to exclusions if needed

### 🔧 Advanced: Source Code
**Compile from source** for maximum security verification

    pip install -r requirements.txt
    python edmrn_gui.py

![SS1](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS1.png)

![SS2](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS2.png)

![SS3](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS3.png)

![SS4](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS4.png)

![SS5](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS5.png)

![SS6](https://github.com/NinurtaKalhu/Elite-Dangerous-Multi-Route-Optimizer/blob/main/screenshots/SS6.png)
