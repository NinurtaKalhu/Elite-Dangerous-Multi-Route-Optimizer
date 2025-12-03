import platform
import os
import sys
import socket
import json
from typing import Optional, Dict, Any, List, Tuple


class PlatformDetector:
    def __init__(self):
        self.system = platform.system()
        self.release = platform.release()
        self.version = platform.version()
        self.machine = platform.machine()
        self.processor = platform.processor()
        self.architecture = platform.architecture()[0]
        self.node = platform.node()
        
        self._detect_linux_distro()
        self._detect_macos_version()
        self._detect_windows_version()
        
        self.cpu_cores = self._get_cpu_cores()
        self.total_memory = self._get_total_memory()
        self.disk_space = self._get_disk_space()
        
        self.features = self._detect_features()
    
    def _detect_linux_distro(self) -> None:
        self.linux_distro = None
        self.linux_version = None
        self.linux_codename = None
        self.linux_id_like = None
        
        if not self.is_linux():
            return
        
        try:
            if os.path.exists('/etc/os-release'):
                release_info = {}
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            release_info[key] = value.strip('"')
                
                self.linux_distro = release_info.get('ID', 'unknown')
                self.linux_version = release_info.get('VERSION_ID', 'unknown')
                self.linux_codename = release_info.get('VERSION_CODENAME', 'unknown')
                self.linux_id_like = release_info.get('ID_LIKE', 'unknown')
            
            try:
                import distro
                if not self.linux_distro or self.linux_distro == 'unknown':
                    self.linux_distro = distro.id()
                    self.linux_version = distro.version()
                    self.linux_codename = distro.codename()
            except ImportError:
                pass
                
        except Exception:
            self.linux_distro = 'unknown'
            self.linux_version = 'unknown'
            self.linux_codename = 'unknown'
            self.linux_id_like = 'unknown'
    
    def _detect_macos_version(self) -> None:
        self.macos_version = None
        self.macos_build = None
        
        if self.is_macos():
            try:
                version_info = platform.mac_ver()
                self.macos_version = version_info[0]
                self.macos_build = version_info[2]
            except Exception:
                self.macos_version = 'unknown'
                self.macos_build = 'unknown'
    
    def _detect_windows_version(self) -> None:
        self.windows_edition = None
        self.windows_build = None
        
        if self.is_windows():
            try:
                if hasattr(platform, 'win32_ver'):
                    win_info = platform.win32_ver()
                    if len(win_info) > 2:
                        self.windows_build = win_info[2]
                
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    
                    buf = ctypes.create_unicode_buffer(256)
                    size = ctypes.c_uint(len(buf))
                    kernel32.GetProductInfo(10, 0, 0, 0, ctypes.byref(buf), ctypes.byref(size))
                    self.windows_edition = buf.value if buf.value else 'unknown'
                except Exception:
                    self.windows_edition = 'unknown'
                    
            except Exception:
                self.windows_edition = 'unknown'
                self.windows_build = 'unknown'
    
    def _get_cpu_cores(self) -> int:
        try:
            if hasattr(os, 'sched_getaffinity'):
                return len(os.sched_getaffinity(0))
            
            import multiprocessing
            return multiprocessing.cpu_count()
            
        except Exception:
            return 1
    
    def _get_total_memory(self) -> Optional[int]:
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.total // (1024 * 1024)
        except ImportError:
            try:
                if self.is_windows():
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory
                    mem = ctypes.c_ulonglong()
                    kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(mem))
                    return mem.value // (1024 * 1024)
                elif self.is_linux():
                    with open('/proc/meminfo', 'r') as f:
                        for line in f:
                            if line.startswith('MemTotal:'):
                                mem_kb = int(line.split()[1])
                                return mem_kb // 1024
            except Exception:
                pass
        return None
    
    def _get_disk_space(self) -> Optional[Dict[str, Any]]:
        try:
            import psutil
            partitions = psutil.disk_partitions()
            disk_info = {}
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info[partition.mountpoint] = {
                        'total_gb': usage.total // (1024**3),
                        'used_gb': usage.used // (1024**3),
                        'free_gb': usage.free // (1024**3),
                        'percent': usage.percent
                    }
                except Exception:
                    continue
            
            return disk_info
        except ImportError:
            return None
    
    def _detect_features(self) -> Dict[str, Any]:
        features = {
            'transparency': self.can_use_transparency(),
            'parallel_processing': self.supports_parallel_processing(),
            'hardware_acceleration': self.has_hardware_acceleration(),
            'network_available': self.is_network_available(),
            'display_server': self.get_display_server() or 'unknown',
            'python_version': sys.version_info
        }
        return features
    
    def is_windows(self) -> bool:
        return self.system == "Windows"
    
    def is_macos(self) -> bool:
        return self.system == "Darwin"
    
    def is_linux(self) -> bool:
        return self.system == "Linux"
    
    def get_platform_info(self) -> Dict[str, Any]:
        info = {
            'system': self.system,
            'release': self.release,
            'version': self.version,
            'machine': self.machine,
            'processor': self.processor,
            'architecture': self.architecture,
            'node': self.node,
            'python_version': sys.version,
            'python_implementation': platform.python_implementation(),
            'cpu_cores': self.cpu_cores,
            'total_memory_mb': self.total_memory,
            'disk_space': self.disk_space,
            'features': self.features
        }
        
        if self.is_linux():
            info.update({
                'linux_distro': self.linux_distro,
                'linux_version': self.linux_version,
                'linux_codename': self.linux_codename,
                'linux_id_like': self.linux_id_like,
            })
        elif self.is_macos():
            info.update({
                'macos_version': self.macos_version,
                'macos_build': self.macos_build
            })
        elif self.is_windows():
            info.update({
                'windows_edition': self.windows_edition,
                'windows_build': self.windows_build
            })
        
        return info
    
    def get_elite_journal_path(self) -> Optional[str]:
        paths = []
        
        if self.is_windows():
            paths = [
                os.path.join(
                    os.path.expanduser('~'),
                    'Saved Games',
                    'Frontier Developments',
                    'Elite Dangerous'
                ),
                os.path.join(
                    os.environ.get('LOCALAPPDATA', ''),
                    'Frontier Developments',
                    'Elite Dangerous'
                )
            ]
        
        elif self.is_macos():
            paths = [
                os.path.join(
                    os.path.expanduser('~'),
                    'Library',
                    'Application Support',
                    'Frontier Developments',
                    'Elite Dangerous'
                ),
                os.path.join(
                    os.path.expanduser('~'),
                    'Library',
                    'Containers',
                    'com.frontier.EliteDangerous',
                    'Data',
                    'Library',
                    'Application Support',
                    'Frontier Developments',
                    'Elite Dangerous'
                )
            ]
        
        elif self.is_linux():
            paths = [
                os.path.join(
                    os.path.expanduser('~'),
                    '.local',
                    'share',
                    'Frontier Developments',
                    'Elite Dangerous'
                ),
                os.path.join(
                    os.path.expanduser('~'),
                    '.var',
                    'app',
                    'com.frontier.EliteDangerous',
                    'data',
                    'Frontier Developments',
                    'Elite Dangerous'
                ),
                os.path.join(
                    os.path.expanduser('~'),
                    '.steam',
                    'steam',
                    'steamapps',
                    'compatdata',
                    '359320',
                    'pfx',
                    'drive_c',
                    'users',
                    'steamuser',
                    'Saved Games',
                    'Frontier Developments',
                    'Elite Dangerous'
                ),
                os.path.join(
                    os.path.expanduser('~'),
                    'snap',
                    'elite-dangerous',
                    'current',
                    '.local',
                    'share',
                    'Frontier Developments',
                    'Elite Dangerous'
                )
            ]
        
        else:
            return None
        
        for path in paths:
            if path and os.path.exists(path):
                return path
        
        return None
    
    def can_use_transparency(self) -> bool:
        if self.is_macos():
            try:
                mac_version = tuple(map(int, self.macos_version.split('.')[:2]))
                return mac_version >= (10, 14)
            except Exception:
                return False
        
        return True
    
    def get_temp_dir(self) -> str:
        if self.is_windows():
            return os.environ.get('TEMP', os.environ.get('TMP', 'C:\\Temp'))
        elif self.is_macos():
            return '/tmp'
        else:
            return '/tmp' if os.path.exists('/tmp') else '/var/tmp'
    
    def get_system_cores(self) -> int:
        return self.cpu_cores
    
    def format_platform_string(self) -> str:
        if self.is_windows():
            edition = f" {self.windows_edition}" if self.windows_edition and self.windows_edition != 'unknown' else ""
            return f"Windows {self.release}{edition} ({self.architecture})"
        
        elif self.is_macos():
            version = f" {self.macos_version}" if self.macos_version else ""
            return f"macOS{version} ({self.architecture})"
        
        elif self.is_linux():
            if self.linux_distro and self.linux_distro != 'unknown':
                distro_str = self.linux_distro.capitalize()
                if self.linux_version and self.linux_version != 'unknown':
                    return f"{distro_str} {self.linux_version} ({self.architecture})"
                return f"{distro_str} ({self.architecture})"
            return f"Linux {self.release} ({self.architecture})"
        
        else:
            return f"{self.system} {self.release} ({self.architecture})"
    
    def get_optimization_methods(self) -> List[str]:
        if self.is_windows():
            methods = ["Fast (Windows)", "Standard", "Thorough"]
            if self.cpu_cores > 4:
                methods.append("Parallel")
            return methods
        elif self.is_macos():
            return ["Fast (macOS)", "Standard", "Thorough"]
        else:
            methods = ["Fast (Linux)", "Standard", "Thorough"]
            if self.cpu_cores > 2:
                methods.append("Parallel")
            return methods
    
    def supports_parallel_processing(self) -> bool:
        return self.cpu_cores > 1 and (self.is_windows() or self.is_linux())
    
    def get_display_server(self) -> Optional[str]:
        if not self.is_linux():
            return None
        
        try:
            if 'WAYLAND_DISPLAY' in os.environ:
                return 'wayland'
            
            if 'DISPLAY' in os.environ:
                return 'x11'
            
            if 'XDG_SESSION_TYPE' in os.environ:
                return os.environ.get('XDG_SESSION_TYPE')
            
            return 'unknown'
            
        except Exception:
            return None
    
    def has_hardware_acceleration(self) -> bool:
        try:
            if self.is_windows():
                try:
                    import ctypes
                    ctypes.windll.dxgi
                    return True
                except Exception:
                    return False
            elif self.is_linux():
                return os.path.exists('/usr/lib/x86_64-linux-gnu/libGL.so') or \
                       os.path.exists('/usr/lib/libGL.so')
            elif self.is_macos():
                return os.path.exists('/System/Library/Frameworks/Metal.framework')
            return False
        except Exception:
            return False
    
    def is_network_available(self) -> bool:
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=3)
            return True
        except OSError:
            return False
    
    def get_recommended_settings(self) -> Dict[str, Any]:
        settings = {
            'overlay_opacity': 0.8,
            'update_check': True,
            'backup_frequency': 'daily',
            'autosave_interval': 5,
            'use_hardware_acceleration': self.has_hardware_acceleration()
        }
        
        if self.is_macos():
            settings['overlay_opacity'] = 0.9
            settings['use_transparency'] = self.can_use_transparency()
        
        elif self.is_linux():
            display_server = self.get_display_server()
            if display_server == 'wayland':
                settings['overlay_opacity'] = 0.85
        
        return settings
    
    def get_compatibility_warnings(self) -> List[str]:
        warnings = []
        
        if self.is_macos() and not self.can_use_transparency():
            warnings.append("macOS version may have limited overlay transparency support")
        
        if self.is_linux() and self.get_display_server() == 'wayland':
            warnings.append("Wayland display server may have compatibility issues with some features")
        
        if self.total_memory and self.total_memory < 2048:
            warnings.append("Low system memory may affect performance")
        
        if self.disk_space:
            for mount, info in self.disk_space.items():
                if info['free_gb'] < 1:
                    warnings.append(f"Low disk space on {mount} ({info['free_gb']}GB free)")
        
        return warnings


_platform_detector = None

def get_platform_detector() -> PlatformDetector:
    global _platform_detector
    if _platform_detector is None:
        _platform_detector = PlatformDetector()
    return _platform_detector
