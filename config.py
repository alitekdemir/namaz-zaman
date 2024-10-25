import json
import logging
from pathlib import Path
from helper import Utility


class ConfigManager:
    """Uygulama ayarlarını yöneten sınıf."""

    # Varsayılan ayarlar
    DEFAULT_CONFIG = {
        "LOCATION": {
            "il_adi": "İstanbul",
            "il_id": "539",
            "ilce_adi": "İSTANBUL",
            "ilce_id": "9541"
        },
        "COLORS": {
            "60": ["#0a1932", "#ffffff"],  # Koyu mavi, beyaz
            "30": ["#540000", "#ffffff"],  # Koyu kırmızı, beyaz  
            "10": ["#c1121f", "#ffffff"],  # Parlak kırmızı, beyaz
            "0": ["#FFA340", "#1F2633"]    # Turuncu, koyu gri
        },
        "WINDOW_SIZES": {
            "horizontal": {"width": 80, "height": 32},
            "vertical": {"width": 32, "height": 72}
        },
        "WINDOW": {
            "position": {"x": 1453, "y": 0},
            "magnet": 20
        },
        "FONTS": {
            "default": {"family": "Roboto", "size": 11, "weight": "bold"},
            "fallback": {"family": "Arial", "size": 11, "weight": "bold"}
        }
    }

    def __init__(self, config_file = "ayarlar.json"):
        """
        ConfigManager sınıfını başlat.
        
        Args:
            config_file: Ayar dosyasının yolu
        """
        self.config_file = Path(config_file)
        self._config = self.load_config()

    def load_config(self) -> dict:
        """
        Ayar dosyasını yükle, yoksa varsayılan ayarları kullan.
        
        Returns:
            dict: Yüklenen ayarlar
        """
        try:
            # Ayar dosyası yoksa varsayılan ayarları kullan
            if not self.config_file.exists():
                logging.info(f"'{self.config_file}' bulunamadı. Varsayılan ayarlar kullanılacak.")
                self.save_config(self.DEFAULT_CONFIG)
                return self.DEFAULT_CONFIG.copy()
            
            # Ayarları yükle
            config = Utility.load_json(self.config_file)
            # Ayarlar boş veya geçersizse varsayılan ayarları kullan
            if not config:
                logging.warning(f"'{self.config_file}' boş veya geçersiz. Varsayılan ayarlar kullanılacak.")
                self.save_config(self.DEFAULT_CONFIG)
                return self.DEFAULT_CONFIG.copy()
                
            # Eksik ayarları varsayılan değerlerle tamamla
            updated = self._merge_config(config, self.DEFAULT_CONFIG)
                
            if updated:
                logging.info("Eksik ayarlar varsayılan değerlerle tamamlandı.")
                self.save_config(config)
                
            return config
            
        except Exception as e:
            logging.error(f"Ayarlar yüklenirken hata oluştu: {e}")
            return self.DEFAULT_CONFIG.copy()

    def _merge_config(self, current: dict, default: dict) -> bool:
        """
        Mevcut ayarları varsayılan ayarlarla birleştirir.
        
        Args:
            current: Mevcut ayarlar
            default: Varsayılan ayarlar
            
        Returns:
            bool: Güncelleme yapıldıysa True
        """
        updated = False
        
        for key, default_value in default.items():
            if key not in current:
                current[key] = default_value
                updated = True
            # İç içe dictionary'leri birleştir
            elif isinstance(default_value, dict) and isinstance(current[key], dict):
                if self._merge_config(current[key], default_value):
                    updated = True
                    
        return updated

    def save_config(self, config = None) -> None:
        """
        Ayarları dosyaya kaydet.
        
        Args:
            config: Kaydedilecek ayarlar. None ise mevcut ayarlar kullanılır.
        """
        try:
            config_to_save = config if config is not None else self._config
            Utility.save_json(self.config_file, config_to_save)
            self._config = config_to_save
        except Exception as e:
            logging.error(f"Ayarlar kaydedilirken hata oluştu: {e}")

    def get_config(self, key: str = None) -> dict:
        """
        Belirtilen anahtara ait ayarı veya tüm ayarları döndür.
        
        Args:
            key: İstenen ayarın anahtarı
            
        Returns:
            Belirtilen ayar değeri veya tüm ayarlar
        """
        if key is None:
            logging.debug("Tüm ayarlar döndürülüyor.")
            return self._config
        logging.debug(f"'{key}' ayarı döndürülüyor. {self._config.get(key)}")
        return self._config.get(key)

    def update_config(self, key: str, value: any) -> None:
        """
        Belirtilen ayarı güncelle ve kaydet.
        
        Args:
            key: Güncellenecek ayarın anahtarı
            value: Yeni değer
        """
        if key in self._config:
            self._config[key] = value
            self.save_config()
            logging.info(f"'{key}' ayarı güncellendi.")
        else:
            logging.warning(f"'{key}' ayarı bulunamadı.")

    def reset_config(self) -> None:
        """Tüm ayarları varsayılan değerlere sıfırla."""
        self.save_config(self.DEFAULT_CONFIG.copy())
        logging.info("Ayarlar varsayılan değerlere sıfırlandı.")