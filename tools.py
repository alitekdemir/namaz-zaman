
import json
import logging as logger
from pathlib import Path
from datetime import datetime, timedelta


class Tools:
    # BASE_DIR = Path(__file__).parent
    BASE_DIR = Path.cwd()
    LOG_FILE = BASE_DIR / 'app.log'
    SETTINGS = BASE_DIR / 'ayarlar.json'
    PRAYER_TIMES = BASE_DIR / 'vakitler.json'

    _settings = None
    _prayer_times = None
    _cities = [
        {"plaka": "01", "il": "Adana", "id": "500"},
        {"plaka": "02", "il": "Adıyaman", "id": "501"},
        {"plaka": "03", "il": "Afyon", "id": "502"},
        {"plaka": "04", "il": "Ağrı", "id": "503"},
        {"plaka": "05", "il": "Amasya", "id": "505"},
        {"plaka": "06", "il": "Ankara", "id": "506"},
        {"plaka": "07", "il": "Antalya", "id": "507"},
        {"plaka": "08", "il": "Artvin", "id": "509"},
        {"plaka": "09", "il": "Aydın", "id": "510"},
        {"plaka": "10", "il": "Balıkesir", "id": "511"},
        {"plaka": "11", "il": "Bilecik", "id": "515"},
        {"plaka": "12", "il": "Bingöl", "id": "516"},
        {"plaka": "13", "il": "Bitlis", "id": "517"},
        {"plaka": "14", "il": "Bolu", "id": "518"},
        {"plaka": "15", "il": "Burdur", "id": "519"},
        {"plaka": "16", "il": "Bursa", "id": "520"},
        {"plaka": "17", "il": "Çanakkale", "id": "521"},
        {"plaka": "18", "il": "Çankırı", "id": "522"},
        {"plaka": "19", "il": "Çorum", "id": "523"},
        {"plaka": "20", "il": "Denizli", "id": "524"},
        {"plaka": "21", "il": "Diyarbakır", "id": "525"},
        {"plaka": "22", "il": "Edirne", "id": "527"},
        {"plaka": "23", "il": "Elazığ", "id": "528"},
        {"plaka": "24", "il": "Erzincan", "id": "529"},
        {"plaka": "25", "il": "Erzurum", "id": "530"},
        {"plaka": "26", "il": "Eskişehir", "id": "531"},
        {"plaka": "27", "il": "Gaziantep", "id": "532"},
        {"plaka": "28", "il": "Giresun", "id": "533"},
        {"plaka": "29", "il": "Gümüşhane", "id": "534"},
        {"plaka": "30", "il": "Hakkari", "id": "535"},
        {"plaka": "31", "il": "Hatay", "id": "536"},
        {"plaka": "32", "il": "Isparta", "id": "538"},
        {"plaka": "33", "il": "Mersin", "id": "557"},
        {"plaka": "34", "il": "İstanbul", "id": "539"},
        {"plaka": "35", "il": "İzmir", "id": "540"},
        {"plaka": "36", "il": "Kars", "id": "544"},
        {"plaka": "37", "il": "Kastamonu", "id": "545"},
        {"plaka": "38", "il": "Kayseri", "id": "546"},
        {"plaka": "39", "il": "Kırklareli", "id": "549"},
        {"plaka": "40", "il": "Kırşehir", "id": "550"},
        {"plaka": "41", "il": "Kocaeli", "id": "551"},
        {"plaka": "42", "il": "Konya", "id": "552"},
        {"plaka": "43", "il": "Kütahya", "id": "553"},
        {"plaka": "44", "il": "Malatya", "id": "554"},
        {"plaka": "45", "il": "Manisa", "id": "555"},
        {"plaka": "46", "il": "K.Maraş", "id": "541"},
        {"plaka": "47", "il": "Mardin", "id": "556"},
        {"plaka": "48", "il": "Muğla", "id": "558"},
        {"plaka": "49", "il": "Muş", "id": "559"},
        {"plaka": "50", "il": "Nevşehir", "id": "560"},
        {"plaka": "51", "il": "Niğde", "id": "561"},
        {"plaka": "52", "il": "Ordu", "id": "562"},
        {"plaka": "53", "il": "Rize", "id": "564"},
        {"plaka": "54", "il": "Sakarya", "id": "565"},
        {"plaka": "55", "il": "Samsun", "id": "566"},
        {"plaka": "56", "il": "Siirt", "id": "568"},
        {"plaka": "57", "il": "Sinop", "id": "569"},
        {"plaka": "58", "il": "Sivas", "id": "571"},
        {"plaka": "59", "il": "Tekirdağ", "id": "572"},
        {"plaka": "60", "il": "Tokat", "id": "573"},
        {"plaka": "61", "il": "Trabzon", "id": "574"},
        {"plaka": "62", "il": "Tunceli", "id": "575"},
        {"plaka": "63", "il": "Şanlıurfa", "id": "567"},
        {"plaka": "64", "il": "Uşak", "id": "576"},
        {"plaka": "65", "il": "Van", "id": "577"},
        {"plaka": "66", "il": "Yozgat", "id": "579"},
        {"plaka": "67", "il": "Zonguldak", "id": "580"},
        {"plaka": "68", "il": "Aksaray", "id": "504"},
        {"plaka": "69", "il": "Bayburt", "id": "514"},
        {"plaka": "70", "il": "Karaman", "id": "543"},
        {"plaka": "71", "il": "Kırıkkale", "id": "548"},
        {"plaka": "72", "il": "Batman", "id": "513"},
        {"plaka": "73", "il": "Şırnak", "id": "570"},
        {"plaka": "74", "il": "Bartın", "id": "512"},
        {"plaka": "75", "il": "Ardahan", "id": "508"},
        {"plaka": "76", "il": "Iğdır", "id": "537"},
        {"plaka": "77", "il": "Yalova", "id": "578"},
        {"plaka": "78", "il": "Karabük", "id": "542"},
        {"plaka": "79", "il": "Kilis", "id": "547"},
        {"plaka": "80", "il": "Osmaniye", "id": "563"},
        {"plaka": "81", "il": "Düzce", "id": "526"}
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
    def update_prayer_times(cls, new_times):
        cls.save_json(cls.PRAYER_TIMES, new_times)
        cls._prayer_times = new_times

    @classmethod
    def update_settings(cls, new_settings):
        cls.save_json(cls.SETTINGS, new_settings)
        cls._settings = new_settings

    @classmethod
    def create_default_settings(cls):
        cls.save_json(cls.SETTINGS, cls._default_settings)
        return cls._default_settings

    @staticmethod
    def load_json(file_path):
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



    @staticmethod
    def find_next_prayer_time2(prayer_times):
        now = datetime.now()
        for day, times in prayer_times.items(): # {"2021-08-01": ["05:00", "13:00", ...]}
            for time_str in times: # "05:00"
                prayer_dt = datetime.strptime(f"{day} {time_str}", "%Y-%m-%d %H:%M")
                if prayer_dt > now: # Eğer bulunan vakit şu andan ileriyse
                    return prayer_dt
        return None  # Eğer uygun vakit bulunamazsa None döner

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
        modified_settings = current_settings.copy()  # Elle değiştirilmiş ayarları koruyacak kopya

        # Sadece eksik anahtarları doldur
        self._fill_missing_settings(self._default_settings, modified_settings)
        
        if modified_settings != current_settings:
            # Sadece gerekli olduğunda dosyayı güncelle
            self.update_settings(modified_settings)

        return modified_settings
