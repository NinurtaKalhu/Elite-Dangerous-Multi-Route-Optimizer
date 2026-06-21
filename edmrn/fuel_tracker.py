"""
Fuel Tracker Module for EDMRN
Tracks ship fuel level from Elite Dangerous Status.json
"""

import json
import os
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Callable
from dataclasses import dataclass
from edmrn.logger import get_logger
from edmrn.utils import get_ed_status_path

logger = get_logger('FuelTracker')


@dataclass
class FuelConfig:
    """Fuel tracker configuration."""
    warning_level: int = 15  # Uyarı seviyesi (%)
    critical_level: int = 5  # Kritik seviye (%)
    sound_enabled: bool = True
    sound_volume: int = 100
    check_interval: float = 1.0  # saniye


class FuelTracker:
    """Elite Dangerous yakıt takip sistemi."""
    
    def __init__(self, app):
        self.app = app
        self.config = FuelConfig()
        self._load_settings()
        self.status_file = self._get_status_file_path()
        self.fuel_capacity = None
        self.current_fuel = 0
        self.fuel_percentage = 0
        self.is_tracking = False
        self._callback = None
        self._last_warning_time = 0
        self._warning_cooldown = 60
    
    def _load_settings(self):
        """Config'den ayarları yükle."""
        try:
            if hasattr(self.app, 'config'):
                self.config.warning_level = self.app.config.fuel_warning_level
                self.config.critical_level = self.app.config.fuel_critical_level
                self.config.sound_enabled = self.app.config.fuel_sound_enabled
                self.config.sound_volume = self.app.config.fuel_sound_volume
                logger.info(f"Fuel settings loaded: warning={self.config.warning_level}%, sound={'on' if self.config.sound_enabled else 'off'}")
        except Exception as e:
            logger.debug(f"Could not load fuel settings: {e}")
        
    def _get_status_file_path(self) -> str:
        """Elite Dangerous Status.json yolunu bul."""
        path = get_ed_status_path()
        if path:
            return path
        return str(Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous" / "Status.json")
    
    def set_callback(self, callback: Callable):
        """Yakıt değişikliğinde çağrılacak callback."""
        self._callback = callback
    
    def start_tracking(self):
        """Yakıt takibini başlat."""
        if self.is_tracking:
            return
        self.is_tracking = True
        thread = threading.Thread(target=self._tracking_loop, daemon=True)
        thread.start()
        logger.info("Fuel tracking started")
    
    def stop_tracking(self):
        """Yakıt takibini durdur."""
        self.is_tracking = False
        logger.info("Fuel tracking stopped")
    
    def _tracking_loop(self):
        """Ana takip döngüsü."""
        while self.is_tracking:
            try:
                status = self._read_status()
                if status:
                    self._update_fuel(status)
                else:
                    # Status.json yoksa (on-foot) yakıtı sıfırla
                    if self.current_fuel > 0:
                        self.reset_fuel()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Fuel tracking error: {e}")
                time.sleep(1)
    
    def _read_status(self) -> Optional[Dict]:
        """Status.json dosyasını oku."""
        if not os.path.exists(self.status_file):
            return None
        try:
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _update_fuel(self, status: Dict):
        """Yakıt bilgilerini güncelle."""
        flags = status.get('Flags', 0)
        is_landed = (flags & 2) != 0  # LANDED flag
        
        fuel_data = status.get('Fuel', {})
        fuel_main = fuel_data.get('FuelMain', 0)
        
        # On-foot durumu: Fuel boş veya FuelMain yok
        is_on_foot = (not fuel_data) or (fuel_main == 0 and 'FuelMain' not in fuel_data)
        
        if is_on_foot or is_landed:
            # On-foot veya landed - yakıtı sıfırla, uyarıyı durdur
            if self.current_fuel > 0 or self.fuel_percentage > 0:
                self.current_fuel = 0
                self.fuel_percentage = 0
                self._last_warning_time = 0  # Uyarı blokajını sıfırla
                if self._callback:
                    fuel_data = self.get_fuel_data()
                    fuel_data['is_on_foot'] = True
                    self._callback(fuel_data)
                logger.debug("On-foot/landed detected - fuel reset")
            return
        
        # Yakıt kapasitesini SADECE ILK DEFA belirle
        # Journal'dan gelen FuelCapacity tercih edilir
        if self.fuel_capacity is None:
            if fuel_main > 0:
                # İlk okumada kapasiteyi belirle
                self.fuel_capacity = fuel_main
                logger.info(f"Fuel capacity set from status: {self.fuel_capacity:.2f}t")
            else:
                # Yakıt yoksa bekle - Journal'dan gelecek
                logger.debug("No fuel data - waiting for Loadout event")
                return
        
        # Yakıt yüzdesini hesapla
        if self.fuel_capacity and self.fuel_capacity > 0:
            self.current_fuel = fuel_main
            self.fuel_percentage = (fuel_main / self.fuel_capacity) * 100
            
            if self._callback:
                self._callback(self.get_fuel_data())
            
            self._check_warning()
        else:
            self.current_fuel = 0
            self.fuel_percentage = 0
            if self._callback:
                self._callback(self.get_fuel_data())
    
    def _check_warning(self):
        """Yakıt uyarısı kontrolü."""
        if self.fuel_percentage <= self.config.warning_level:
            if self.current_fuel == 0 and self.fuel_percentage == 0:
                return
            current_time = time.time()
            if current_time - self._last_warning_time > self._warning_cooldown:
                self._last_warning_time = current_time
                self._play_warning_sound()
    
    def _play_warning_sound(self):
        """Yakıt uyarı sesini çal."""
        if not self.config.sound_enabled:
            return
        if self.config.sound_volume <= 0:
            return
        
        try:
            import winsound
            sound_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sounds', 'fuel-low.wav')
            if os.path.exists(sound_file):
                # WAV dosyasını çal
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                logger.info(f"Fuel warning sound played: {sound_file} (level: {self.fuel_percentage:.1f}%, volume: {self.config.sound_volume}%)")
            else:
                # Fallback: beep - volume'a göre süre ve frekans ayarla
                freq = int(800 + (self.config.sound_volume * 4))  # 800-1200 Hz
                duration = int(100 + (self.config.sound_volume * 2))  # 100-300 ms
                winsound.Beep(freq, duration)
                logger.info(f"Fuel warning beep played (level: {self.fuel_percentage:.1f}%, volume: {self.config.sound_volume}%)")
        except Exception as e:
            logger.error(f"Sound playback error: {e}")
    
    def get_fuel_data(self) -> Dict:
        """Mevcut yakıt bilgilerini döndür."""
        return {
            'current_fuel': self.current_fuel,
            'capacity': self.fuel_capacity,
            'percentage': self.fuel_percentage,
            'is_warning': self.fuel_percentage <= self.config.warning_level and self.current_fuel > 0,
            'is_critical': self.fuel_percentage <= self.config.critical_level and self.current_fuel > 0,
            'is_on_foot': self.current_fuel == 0 and self.fuel_percentage == 0,
            'status': self._get_fuel_status()
        }
    
    def reset_fuel(self):
        """Yakıt bilgisini sıfırla (gemi değişikliği veya on-foot durumunda)."""
        self.current_fuel = 0
        self.fuel_percentage = 0
        # fuel_capacity'i SIFIRLAMAYIN - gemi kapasitesi değişmez!
        if self._callback:
            self._callback(self.get_fuel_data())
        logger.info("Fuel data reset (capacity preserved)")
    
    def update_fuel_capacity(self, capacity: float):
        """Yakıt kapasitesini güncelle (Journal'dan okunan değer)."""
        if capacity > 0 and capacity != self.fuel_capacity:
            old_capacity = self.fuel_capacity
            self.fuel_capacity = capacity
            logger.info(f"Fuel capacity updated: {old_capacity}t -> {capacity}t")
            # Kapasite değiştiyse yüzdesi yeniden hesapla
            if self.current_fuel > 0:
                self.fuel_percentage = (self.current_fuel / self.fuel_capacity) * 100
                if self._callback:
                    self._callback(self.get_fuel_data())
    
    def _get_fuel_status(self) -> str:
        """Yakıt durumunu metin olarak döndür."""
        if self.fuel_percentage > 50:
            return "OK"
        elif self.fuel_percentage > 25:
            return "CAUTION"
        elif self.fuel_percentage > self.config.warning_level:
            return "WARNING"
        else:
            return "CRITICAL"
    
    def get_fuel_color(self) -> str:
        """Yakıt yüzdesine göre renk döndür."""
        if self.fuel_percentage > 50:
            return "#4CAF50"  # Yeşil
        elif self.fuel_percentage > 25:
            return "#FFC107"  # Sarı
        elif self.fuel_percentage > self.config.warning_level:
            return "#FF9800"  # Turuncu
        else:
            return "#F44336"  # Kırmızı
    
    def set_fuel_capacity(self, capacity: float):
        """Yakıt kapasitesini ayarla."""
        self.fuel_capacity = capacity
        logger.info(f"Fuel capacity set to: {capacity:.2f}t")
    
    def set_warning_level(self, level: int):
        """Uyarı seviyesini ayarla."""
        self.config.warning_level = max(0, min(100, level))
        logger.info(f"Warning level set to: {self.config.warning_level}%")
