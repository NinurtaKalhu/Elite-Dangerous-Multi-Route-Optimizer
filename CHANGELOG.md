# EDMRN Changelog

## [3.1.0] - 2026-01-13

### ✨ New Features
- **🌌 Galaxy Plotter Tab**: Spansh Exact Plotter integration for precise route planning
  - Calculate exact routes with fuel consumption, neutron boosts, and FSD injections
  - Full integration with Spansh Exact Plotter API
  - Support for Coriolis.io ship builds (JSON) and EDSY.org (SLEF format)
  - Comprehensive options: cargo, reserve fuel, neutron supercharge, FSD injection, secondary star exclusion
  - Real-time progress updates during route calculation
  - Detailed route display with jump-by-jump information
  - CSV export functionality for route data
  - System name autocomplete in source/destination fields
  - Reverse route button for quick direction swap
  - Automatic handling of long route calculations (up to 5 minutes)

- **⌨️ Smart System Name Autocomplete**: Real-time system suggestions
  - Integrated Spansh API (primary, 70M+ systems) with EDSM v1 fallback
  - Available in Neutron Highway and Galaxy Plotter tabs
  - Dropdown suggestions appear as you type (minimum 3 characters)
  - Keyboard navigation support (Up/Down arrows, Enter to select, Escape to close)
  - Smart prioritization: exact matches > starts-with > contains query
  - 1-hour intelligent caching for faster responses and reduced API load
  - Thread-safe async implementation to prevent UI blocking

- **🧠 Visit History System**: Global visit tracking across all routes
  - Remembers previously visited systems
  - Prompts to remove duplicate systems during route optimization
  - User choice: keep all, remove selected, or cancel
  - Filtered routes persist across restarts

- **💾 Smart Backup System**: Enhanced route state persistence
  - Saves filtered routes (after removing visited systems)
  - Prioritizes user-modified routes on restore
  - Backward compatible with older backups
  - Preserves progress for all route types (Route Tracker, Neutron Plotter, Galaxy Plotter)

- **🎮 GeForce Now Enhanced Overlay Controls**:
  - Quick navigation buttons: [<] [System Name] [>]
  - Mark systems as visited directly from overlay
  - Copy next/previous system to clipboard
  - Tab switching buttons for Route Tracker, Neutron, Galaxy
  - Seamless in-game navigation experience

- **🖥️ Borderless Window Mode**:
  - Toggle borderless mode in Settings → Theme
  - Cleaner, modern window appearance
  - Custom window controls and resize handles

- **📂 Auto-Overlay Launch**:
  - Overlay automatically opens after route optimization
  - Optional: disable in Settings

- **🎯 Nearest System Finder (Starting System)**:
  - Auto-detects current CMDR location from Elite Dangerous journal
  - Calculates nearest CSV system to current coordinates
  - Intelligent distance calculation using Euclidean formula (3D space)
  - Dropdown selector for manual system choice
  - One-click "🎯 Find Nearest" button for recalculation
  - Separated from Neutron tab coordinate-based finder

### 🔧 Technical Improvements
- Added `galaxy_plotter.py` module with Spansh API integration
- Added `system_autocomplete.py` module with EDSM API v1 (primary) + Spansh (fallback)
- Created `autocomplete_entry.py` custom widget for CTkinter with improved UX
- Async route calculation to prevent UI blocking
- Progress callback system for real-time status updates
- Enhanced route state management
- Improved backup/restore reliability
- Visual refinements: fonts, text, buttons

### 🐛 Bug Fixes
- Fixed overlay resize issues
- Fixed dropdown not closing when clicking on a suggestion
- Fixed dropdown persisting after selection
- Improved focus handling to prevent dropdown reopening unexpectedly
- Improved idempotent manager initialization
- Journal path detection made more robust
- **Fixed CSV import error**: Body Name column is now truly optional
- **Fixed optimization button**: Now activates with only System Name, X, Y, Z columns (Body Name optional)
- **Fixed autocomplete dropdown positioning**: Dropdown now follows main window when moved
- **Enhanced API optimization**: 300ms debouncing reduces API calls by ~92%

---

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
