
import json
import logging as logger
from pathlib import Path
from datetime import datetime, timedelta


class Tools:
    BASE_DIR = Path(__file__).parent
    LOG_FILE = BASE_DIR / 'app.log'
    SETTINGS = BASE_DIR / 'ayarlar.json'
    PRAYER_TIMES = BASE_DIR / 'vakitler.json'

    _settings = None
    _prayer_times = None
    _cities = [
        {"plaka": "06", "il": "Ankara", "id": "506"},
        {"plaka": "21", "il": "Diyarbakır", "id": "525"},
        {"plaka": "34", "il": "İstanbul", "id": "539"},
    ]

    _default_settings = {
        "LOCATION": {"city": {"name": "İstanbul", "id": "539"}, "district": {"name": "İSTANBUL", "id": "9541"}},
        "COLORS": {"standard": {"background": "#0a1932", "text": "#ffffff"},
                    "warning": {"background": "#540000", "text": "#ffffff", "trigger": 45},
                    "critical": {"background": "#c1121f", "text": "#ffffff", "trigger": 15}},
        "FONTS": {"clock": {"family": "IBM Plex Mono", "size": 14, "weight": "normal"}},
        "DISPLAY": {"position": {"x": 1453, "y": 1050},
                    "always_on_top": True,
                    "snap_distance": 20,
                    "orientation": "horizontal", 
                    "show_seconds": True}
    }

    @staticmethod
    def configure_logging(log_level="INFO"):
        # log_format = "%(asctime)s [%(levelname)s] [%(filename)s:%(funcName)s] - %(message)s"
        log_format = "%(asctime)s [%(levelname)s] [%(filename)-15s:%(funcName)-30s] - %(message)s"
        logger.basicConfig(filename=Tools.LOG_FILE, level=log_level, format=log_format, force=True)

    @classmethod
    def get_settings(cls):
        if cls._settings is None:
            cls._settings = cls.load_json(cls.SETTINGS) or cls.create_default_settings()
        return cls._settings

    @classmethod
    def get_cities(cls):
        return cls._cities

    @classmethod
    def get_prayer_times(cls):
        if cls._prayer_times is None:
            cls._prayer_times = cls.load_json(cls.PRAYER_TIMES) or {}
        return cls._prayer_times

    @classmethod
    def load_json(cls, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                logger.info(f"{file_path.name} dosyası başarıyla yüklendi.")
                return data
        except FileNotFoundError:
            logger.error(f"{file_path.name} dosyası bulunamadı.")
        except json.JSONDecodeError:
            logger.error(f"{file_path.name} dosyasında JSON okuma hatası.")
        return None

    @staticmethod
    def save_json(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, separators=(',', ':'))
            logger.info(f"{file_path} dosyası kaydedildi.")

    @classmethod
    def update_prayer_times(cls, new_times):
        cls.save_json(cls.PRAYER_TIMES, new_times)
        cls._prayer_times = new_times

    @classmethod
    def update_settings(cls, new_settings):
        cls.save_json(cls.SETTINGS, new_settings)
        cls._settings = new_settings

    @staticmethod
    def find_next_prayer_time(prayer_times):
        now = datetime.now()
        today_str = now.date().isoformat() # "2021-08-01"
        tomorrow_str = (now + timedelta(days=1)).date().isoformat() # "2021-08-02"

        for time_str in prayer_times.get(today_str, []):
            prayer_dt = datetime.strptime(f"{today_str} {time_str}", "%Y-%m-%d %H:%M")
            if prayer_dt > now:
                return prayer_dt

        if prayer_times.get(tomorrow_str):
            return datetime.strptime(f"{tomorrow_str} {prayer_times.get(tomorrow_str)[0]}", "%Y-%m-%d %H:%M")

        return None

    @staticmethod
    def remaining_time(target_time: datetime):
        delta = target_time - datetime.now()
        total_minutes, seconds = divmod(delta.seconds, 60)
        hours, minutes = divmod(total_minutes, 60)
        # return f"{hours}:{minutes:02}:{seconds:02}".split(":")
        return hours, minutes, seconds

    @staticmethod
    def create_default_settings(cls):
        cls.save_json(cls.SETTINGS, cls._default_settings)
        return cls._default_settings

    @staticmethod
    def _fill_missing_settings(defaults, current):
        """Yalnızca eksik ayarları varsayılanlarla doldurur, mevcut ayarları değiştirmez."""
        for key, value in defaults.items():
            if isinstance(value, dict):
                # İç içe geçmiş sözlükler için derinlemesine kontrol
                current.setdefault(key, {})
                Tools._fill_missing_settings(value, current[key])
            else:
                # Eğer mevcut bir ayar yoksa varsayılanı ekler
                current.setdefault(key, value)


    def validate_and_fix_settings(self):
        logger.info("Ayarlar kontrol ediliyor...")
        current_settings = self.get_settings() or {}
        self._fill_missing_settings(self._default_settings, current_settings)
        self.update_settings(current_settings)
        return current_settings



    def validate_and_fix_settings(self):
        logger.info("Ayarlar kontrol ediliyor...")
        current_settings = self.get_settings() or {}
        modified_settings = current_settings.copy()  # Elle değiştirilmiş ayarları koruyacak kopya

        # Sadece eksik anahtarları doldur
        self._fill_missing_settings(self._default_settings, modified_settings)
        
        if modified_settings != current_settings:
            # Sadece gerekli olduğunda dosyayı güncelle
            self.update_settings(modified_settings)

        return modified_settings
