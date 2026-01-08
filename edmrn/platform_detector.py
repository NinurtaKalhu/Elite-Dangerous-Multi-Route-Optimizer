import platform
import os
import sys
import socket
import psutil
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
    def _detect_linux_distro(self):
        self.linux_distro = None
        self.linux_version = None
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
        except Exception:
            self.linux_distro = 'unknown'
            self.linux_version = 'unknown'
    def _detect_macos_version(self):
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
    def _detect_windows_version(self):
        self.windows_edition = None
        self.windows_build = None
        if self.is_windows():
            try:
                if hasattr(platform, 'win32_ver'):
                    win_info = platform.win32_ver()
                    if len(win_info) > 2:
                        self.windows_build = win_info[2]
                self.windows_edition = 'unknown'
            except Exception:
                self.windows_edition = 'unknown'
                self.windows_build = 'unknown'
    def _get_cpu_cores(self):
        try:
            if hasattr(os, 'sched_getaffinity'):
                return len(os.sched_getaffinity(0))
            import multiprocessing
            return multiprocessing.cpu_count()
        except Exception:
            return 1
    def _get_total_memory(self):
        try:
            memory = psutil.virtual_memory()
            return memory.total // (1024 * 1024)
        except Exception:
            return None
    def is_windows(self):
        return self.system == "Windows"
    def is_macos(self):
        return self.system == "Darwin"
    def is_linux(self):
        return self.system == "Linux"
    def get_system_cores(self):
        return self.cpu_cores
    def format_platform_string(self):
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
    def get_temp_dir(self):
        if self.is_windows():
            return os.environ.get('TEMP', os.environ.get('TMP', 'C:\\Temp'))
        elif self.is_macos():
            return '/tmp'
        else:
            return '/tmp' if os.path.exists('/tmp') else '/var/tmp'
_platform_detector = None
def get_platform_detector():
    global _platform_detector
    if _platform_detector is None:
        _platform_detector = PlatformDetector()
    return _platform_detector
