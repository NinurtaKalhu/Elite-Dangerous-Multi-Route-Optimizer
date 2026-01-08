# EDMRN Changelog

## [3.0] - 2026-01-06

### 🏗️ Major Changes
- **Modular Architecture**: Extracted 7 independent modules from monolithic app.py
  - `theme_manager.py` - Theme switching and management
  - `route_management.py` - Route handling and UI
  - `settings_manager.py` - Settings and configuration
  - `neutron_manager.py` - Neutron highway routing
  - `journal_operations.py` - Journal file operations
  - `file_operations.py` - File I/O operations
  - `backup.py` - Backup management
  
- **Complete Theme System Overhaul**
  - JSON-based CustomTkinter native theme system
  - 11 Elite Dangerous PowerPlay faction-themed color schemes:
    - Elite Dangerous (Orange)
    - Aisling Duval (Blue)
    - Archon Delaine (Green)
    - Arissa Lavigny Duval (Purple)
    - Denton Patreus (Gold)
    - Edmund Mahon (Cyan)
    - Felicia Winters (Light Blue)
    - Li Yong Rui (Red)
    - Pranav Antal (Gold)
    - Zachary Hudson (Lime Green)
    - Zemina Torval (Indigo)
  
- **Smart Restart System**
  - Automatic application restart on theme change
  - Window geometry persistence
  - Development mode support (os.execl)
  - Frozen EXE mode support (subprocess.Popen)
  
- **Backup System Restructuring**
  - Improved backup file organization
  - Better error handling for corrupted backups
  - Enhanced coordinate parsing with validation
  
- **Overlay System Redesign**
  - Improved transparency and positioning
  - Better in-game detection
  - More reliable window management
  
- **Neutron Highway Integration**
  - Advanced neutron jump routing
  - Improved route optimization with neutron networks

### ✨ New Features
- Real-time theme switching with 11 faction-based color schemes
- Color tone generation algorithm (darken/lighten functions)
- Smart restart mechanism for seamless theme application
- Improved backup loading with error recovery
- Enhanced error messages and logging

### 🐛 Bug Fixes
- Fixed 200+ unterminated string literals across codebase
- Fixed backup loading coordinate parsing errors
- Fixed map frame refresh NoneType error
- Fixed label color configuration (tuple index out of range)
- Fixed settings manager CTkOptionMenu text_color issues
- Improved error handling throughout application

### 📊 UI/UX Improvements
- Eliminated all gray areas - everything now uses theme-specific colors
- Consistent color schemes across all UI elements
- Better visual hierarchy with themed backgrounds
- Improved readability with proper color contrast
- Professional dark theme aesthetics

### ⚠️ Breaking Changes
- Backup system restructure - may require migration from v2.x backups
- Module architecture changes - any custom extensions need updating
- Theme system change - old theme settings not compatible

### 🔧 Technical Improvements
- Thread-safe design with proper locking mechanisms
- Enhanced error handling with stack traces
- Better memory management
- Improved performance with modular design
- Code organization following separation of concerns

### 📦 Build Updates
- Updated version_info.txt to 3.0
- PyInstaller spec updated for new module structure
- Build script verified for Windows EXE generation

### 🙏 Contributors
- Ninurta Kalhu (S.C.) - Main Developer
- Ozgur KARATAS - Contributor
- Aydin AKYUZ - Contributor / Beta Tester https://www.youtube.com/@drizzydnt
---

## [2.3.1] - 2025-12-XX

### 🐛 Bug Fixes
- Optimizer stability improvements
- Minor UI fixes

---

## [2.3.0] - 2025-12-XX

### ✨ Major Features
- Complete modular rewrite
- Advanced debug system
- Professional packaging
- Performance optimizations

### 🚀 Key Features
- Smart Route Optimization (TSP-based)
- Interactive 3D Visualization
- In-Game Overlay
- Auto Journal Monitoring
- Advanced Debug Console
- Auto-Save & Backup
- Multi-Commander Support
- Customizable UI Themes
- Modular Design
