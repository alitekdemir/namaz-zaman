import json, requests
from datetime import datetime, timedelta
import logging as logger
from pathlib import Path
from bs4 import BeautifulSoup
import tkinter as tk
import customtkinter as ctk


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

    @staticmethod
    def configure_logging(log_level="INFO"):
        log_format = "%(asctime)s [%(levelname)s] [%(filename)s.%(funcName)-30s] - %(message)s"
        logger.basicConfig(filename=Tools.LOG_FILE, level=log_level, format=log_format, force=True)

    @classmethod
    def get_settings(cls):
        if cls._settings is None:
            cls._settings = cls.load_json(Tools.SETTINGS) or cls.create_default_settings()
        return cls._settings

    @classmethod
    def get_settings(cls):
        """Ayarları getirir ve doğrular"""
        if cls._settings is None:
            cls._settings = cls.load_json(Tools.SETTINGS)
            if cls._settings is None:
                cls._settings = cls.get_default_settings()
                cls.update_settings(cls._settings)
        return cls._settings

    @classmethod
    def get_cities(cls):
        return cls._cities

    @classmethod
    def get_prayer_times(cls):
        if cls._prayer_times is None:
            cls._prayer_times = cls.load_json(Tools.PRAYER_TIMES) or {}
        return cls._prayer_times

    @staticmethod
    def load_json(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                logger.info(f"{file_path} dosyası yüklendi.")
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.error(f"{file_path} dosyası yüklenemedi.")
            return None

    @staticmethod
    def save_json(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, separators=(',', ':'))
            logger.info(f"{file_path} dosyası kaydedildi.")

    @classmethod
    def update_prayer_times(cls, new_times):
        """Namaz vakitlerini güncelle ve cache'i temizle"""
        cls.save_json(Tools.PRAYER_TIMES, new_times)
        cls._prayer_times = new_times  # Cache'i güncelle

    @classmethod
    def update_settings(cls, new_settings):
        """Ayarları günceller ve cache'i temizler"""
        cls.save_json(Tools.SETTINGS, new_settings)
        cls._settings = new_settings

    @staticmethod
    def find_next_prayer_time(prayer_times):
        now = datetime.now()
        today_str = now.date().isoformat()
        tomorrow_str = (now + timedelta(days=1)).date().isoformat()

        for time_str in prayer_times.get(today_str, []):
            prayer_dt = datetime.strptime(f"{today_str} {time_str}", "%Y-%m-%d %H:%M")
            if prayer_dt > now:
                return prayer_dt

        if tomorrow_str in prayer_times and prayer_times[tomorrow_str]:
            return datetime.strptime(f"{tomorrow_str} {prayer_times[tomorrow_str][0]}", "%Y-%m-%d %H:%M")

        return None

    @staticmethod
    def time_until_next_prayer(target_time, now=None):
        now = now or datetime.now()
        delta = target_time - now
        total_minutes = int(delta.total_seconds() / 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours:02}:{minutes:02}"

    @staticmethod
    def create_default_settings():
        default_settings = Tools.get_default_settings()
        Tools.save_json(Tools.SETTINGS, default_settings)
        return default_settings

    @staticmethod
    def get_default_settings():
        """Varsayılan ayarları döndürür"""
        return {
            "LOCATION": {
                "city": {"name": "İstanbul", "id": "539"},
                "district": {"name": "İSTANBUL", "id": "9541"},
            },
            "COLORS": {
                "standard": {"background": "#0a1932", "text": "#ffffff", "trigger": 60},
                "warning": {"background": "#540000", "text": "#ffffff", "trigger": 30},
                "critical": {"background": "#c1121f", "text": "#ffffff", "trigger": 10},
            },
            "FONTS": {
                "clock": {"family": "IBM Plex Mono", "size": 14, "weight": "bold"}
            },
            "Display": {
                "position": {"x": 1453, "y": 1050},
                "always_on_top": True,
                "snap_distance": 20,
                "orientation": "horizontal"
            },
        }

    @staticmethod
    def _fill_missing_settings(defaults, current):
        """Varsayılan ayarları mevcut ayarlara ekler."""
        for key, value in defaults.items():
            if isinstance(value, dict):
                current.setdefault(key, {})
                Tools._fill_missing_settings(value, current[key])
            else:
                current.setdefault(key, value)

    def validate_and_fix_settings(self):
        """Ayarları kontrol eder ve eksikleri tamamlar."""
        logger.info("Ayarlar kontrol ediliyor...")
        default_settings = self.get_default_settings()
        current_settings = self.get_settings() or {}
        
        # Varsayılan ayarları eksik olanlara uygula
        self._fill_missing_settings(default_settings, current_settings)
        
        # Güncellenen ayarları kaydet
        self.update_settings(current_settings)
        return current_settings


class ClockWidget:
    def __init__(self, root):
        self.root = root
        # Ayarları doğrula ve düzelt
        self._settings = Tools().validate_and_fix_settings()
        
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        
        # Debug log
        logger.debug(f"Ayarlardaki konum: {self._settings['Display']['position']}")
        
        colors = self._settings["COLORS"]["standard"]
        font_settings = self._settings["FONTS"]["clock"]
        
        # Window yapılandırması
        self.window.configure(bg=colors["background"])
        self.window.attributes('-topmost', self._settings["Display"]["always_on_top"])

        # Label oluşturma
        self.label = tk.Label(
            self.window,
            text="00:00",
            font=(font_settings["family"], font_settings["size"], font_settings["weight"]),
            fg=colors["text"],
            bg=colors["background"]
        )
        self.label.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # İlk geometri ayarı
        self.initial_geometry_set = False
        self.window.update_idletasks()  # Widget'ın boyutlarının hesaplanmasını sağla
        
        # Konumu ayarla
        self.set_window_geometry()
        
        self.is_dragging = False
        self.setup_bindings()
        self.create_context_menu()
        
        # Vakitler.json kontrolü ve ayarlar penceresini açma
        if not Path(Tools.PRAYER_TIMES).exists():
            logger.info("Vakitler dosyası bulunamadı. Ayarlar penceresi açılıyor...")
            self.root.after(1000, lambda: self.open_settings(None))  # Event parametresini None olarak gönder
        
        # İlk güncellemeyi başlat
        self.update_clock()
        self.keep_on_top()


    def set_window_geometry(self):
        """Pencere geometrisini hesapla ve ayarla"""
        try:
            # Pencereyi güncelle
            self.window.update_idletasks()
            
            # Yönlendirmeye göre boyutları belirle
            is_horizontal = self._settings["Display"]["orientation"] == "horizontal"
            
            # Label'ın boyutlarını al
            base_width = self.label.winfo_reqwidth()
            base_height = self.label.winfo_reqheight()
            
            # Debug log
            logger.debug(f"Base dimensions: width={base_width}, height={base_height}")
            
            # Yönlendirmeye göre boyutları ayarla
            if is_horizontal:
                width = int(base_width * 1.1)
                height = int(base_height * 1.02)
            else:
                width = int(base_height * 1.1)
                height = int(base_width * 1.05)
            
            # Konum bilgisini al
            x, y = self._settings["Display"]["position"].values()
            
            # Ekran sınırlarını kontrol et
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # Debug log
            logger.debug(f"Screen dimensions: width={screen_width}, height={screen_height}")
            
            # Pencere ekranın dışına taşmasın
            x = max(0, min(x, screen_width - width))
            y = max(0, min(y, screen_height - height))
            geometry = f"{width}x{height}+{x}+{y}"
            logger.debug(f"Setting geometry: {geometry}")
            
            # Geometriyi ayarla
            self.window.geometry(geometry)
            
            # Pencereyi güncelle
            self.window.update_idletasks()
            
            # Doğrulama logu
            actual_x = self.window.winfo_x()
            actual_y = self.window.winfo_y()
            actual_width = self.window.winfo_width()
            actual_height = self.window.winfo_height()
            
            logger.info(
                f"Pencere konumu ayarlandı: "
                f"Hedef(x={x}, y={y}, w={width}, h={height}), "
                f"Gerçek(x={actual_x}, y={actual_y}, w={actual_width}, h={actual_height})"
            )
            
            return width, height
            
        except Exception as e:
            logger.error(f"Pencere geometrisi ayarlanırken hata: {e}")
            return None, None

    def update_orientation(self):
        """Yönlendirme değiştiğinde pencereyi güncelle"""
        current_width = self.window.winfo_width()
        current_height = self.window.winfo_height()
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        
        # Boyutları yer değiştir
        self.window.geometry(f"{current_height}x{current_width}+{x}+{y}")
        
        # Saati güncelle
        self.update_clock()

    def update_window_geometry(self):
        """Pencere geometrisini günceller"""
        self.window.update_idletasks()
        width = f"{self.label.winfo_reqwidth() * 1.1 :.0f}"
        height = f"{self.label.winfo_reqheight() * 1.02:.0f}"
        x = self._settings["Display"]["position"]["x"]
        y = self._settings["Display"]["position"]["y"]
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def setup_bindings(self):
        """Pencere bağlantılarını ayarlar"""
        self.window.bind("<Button-1>", self.start_move)
        self.window.bind("<B1-Motion>", self.do_move)
        self.window.bind("<ButtonRelease-1>", self.stop_move)
        self.window.bind("<Double-Button-1>", self.open_settings)
        self.window.bind("<Button-3>", self.show_context_menu)

    def create_context_menu(self):
        """Sağ tık menüsünü oluşturur"""
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Ayarları Aç", command=lambda: self.open_settings(None))
        self.context_menu.add_command(label="Programı Kapat", command=self.close_program)

    def start_move(self, event):
        """Sürükleme başlangıcı"""
        self.is_dragging = True
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        """Sürükleme sırasında"""
        if not self.is_dragging:
            return
            
        x = self.window.winfo_x() + (event.x - self.x)
        y = self.window.winfo_y() + (event.y - self.y)
        x, y = self.snap_to_edges(x, y)
        self.window.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        """Sürükleme bittiğinde"""
        if not self.is_dragging: return
        self.is_dragging = False
        try:
            # Son pozisyonu al
            x, y = self.window.winfo_x(), self.window.winfo_y()
            # Debug log
            logger.debug(f"Sürükleme sonrası konum: x={x}, y={y}")
            
            # Ayarları güncelle
            settings = Tools.get_settings()
            if (settings["Display"]["position"]["x"] != x or settings["Display"]["position"]["y"] != y):
                settings["Display"]["position"].update({"x": x, "y": y})
                logger.debug(f"Yeni konum ayarlara kaydediliyor: x={x}, y={y}")
                
                Tools.update_settings(settings)
                self._settings = settings  # Yerel ayarları da güncelle
                logger.info(f"Pozisyon güncellendi: x={x}, y={y}")
        except Exception as e:
            logger.error(f"Pozisyon kaydedilirken hata oluştu: {e}")

    def snap_to_edges(self, x, y):
        """Kenarlara yapışma kontrolü"""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        snap_distance = self._settings["Display"]["snap_distance"]

        if abs(x) < snap_distance:
            x = 0
        elif abs(x + self.window.winfo_width() - screen_width) < snap_distance:
            x = screen_width - self.window.winfo_width()

        if abs(y) < snap_distance:
            y = 0
        elif abs(y + self.window.winfo_height() - screen_height) < snap_distance:
            y = screen_height - self.window.winfo_height()

        return x, y

    def open_settings(self, event=None):
        """Ayarlar penceresini aç. Event parametresi opsiyonel."""
        if (not hasattr(self.root, 'settings_window')
                or not (self.root.settings_window
                        and self.root.settings_window.window.winfo_exists())):
            self.root.settings_window = SettingsWindow(self.root)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def close_program(self):
        self.root.quit()

    def keep_on_top(self):
        self.window.attributes('-topmost', 1)  # Önce en üste al
        self.window.after(5000, self.keep_on_top)  # 5 saniye sonra tekrar çalıştır

    def update_clock(self):
        prayer_times = Tools.get_prayer_times()
        next_prayer_time = Tools.find_next_prayer_time(prayer_times)
        if next_prayer_time:
            time_until = Tools.time_until_next_prayer(next_prayer_time)
            hours, minutes = time_until.split(":")
            hours = str(int(hours))  # Başındaki 0'ı kaldır
            minutes = minutes.zfill(2)  # Dakikaları iki haneli yap
            total_minutes = int(hours) * 60 + int(minutes)
            
            # Renkleri güncelleme
            self.update_color_by_time(total_minutes)
            
            # Yöne göre formatı belirle
            if self._settings["Display"]["orientation"] == "vertical":
                self.label.config(text=f"{hours}\n{minutes}")
            else:
                self.label.config(text=f"{hours}:{minutes}")
        else:
            if self._settings["Display"]["orientation"] == "vertical":
                self.label.config(text="0\n00")
            else:
                self.label.config(text="0:00")
                
        self.root.after(1000, self.update_clock)

    
    def update_color_by_time(self, minutes):
        if minutes < self._settings["COLORS"]["critical"]["trigger"]:
            self.change_color(self._settings["COLORS"]["critical"])
        elif minutes < self._settings["COLORS"]["warning"]["trigger"]:
            self.change_color(self._settings["COLORS"]["warning"])
        else:
            self.change_color(self._settings["COLORS"]["standard"])
    
    def change_color(self, color_settings):
        self.label.config(bg=color_settings["background"], fg=color_settings["text"])
        self.window.config(bg=color_settings["background"])


class SettingsWindow:
    def __init__(self, root):
        self.root = root
        self._settings = Tools.get_settings()
        
        # Main window setup
        self.window = ctk.CTkToplevel(root)
        self.window.title("Ayarlar")
        self.window.geometry("500x300")
        
        # Initialize core attributes
        self.current_row = 0
        self.district_mapping = {}
        
        # Create main frames
        self.active_city_frame = self._create_active_city_frame()
        self.settings_container = self._create_settings_container()
        
        # Pack frames
        self.active_city_frame.pack(pady=10, padx=20, fill="x")
        self.settings_container.pack(pady=10, padx=20, fill="both", expand=True)
        
        self._set_initial_values()
        self._center_window()
    
    def _create_active_city_frame(self):
        """Create frame showing current active city"""
        frame = ctk.CTkFrame(self.window)
        
        location = (f"Aktif Konum: {self._settings['LOCATION']['district']['name']} / "
                   f"{self._settings['LOCATION']['city']['name']}")
        
        self.current_location_label = ctk.CTkLabel(
            frame,
            text=location,
            font=("Arial", 14, "bold")
        )
        self.current_location_label.pack(pady=10)
        
        return frame
    
    def _create_settings_container(self):
        """Create main settings container"""
        container = ctk.CTkFrame(self.window)
        
        # City selection row
        plaka_row = self._create_settings_row(container)
        plaka_label = ctk.CTkLabel(
            plaka_row,
            text="Plaka No",
            anchor="w",
            width=100
        )
        self.city_entry = ctk.CTkEntry(plaka_row, width=200)
        fetch_button = ctk.CTkButton(
            plaka_row,
            text="İlçeleri Getir",
            width=120,
            command=self._fetch_districts
        )
        
        plaka_label.pack(side="left", padx=10)
        self.city_entry.pack(side="left", padx=10)
        fetch_button.pack(side="right", padx=10)
        plaka_row.pack(fill="x", pady=5)
        
        # District selection row
        district_row = self._create_settings_row(container)
        district_label = ctk.CTkLabel(
            district_row,
            text="İlçe Seçiniz",
            anchor="w",
            width=100
        )
        self.district_combobox = ctk.CTkComboBox(
            district_row,
            width=200,
            values=[]
        )
        save_button = ctk.CTkButton(
            district_row,
            text="Kaydet",
            width=120,
            command=self._save_settings
        )
        
        district_label.pack(side="left", padx=10)
        self.district_combobox.pack(side="left", padx=10)
        save_button.pack(side="right", padx=10)
        district_row.pack(fill="x", pady=5)
        
        # Update times row
        update_row = self._create_settings_row(container)
        self.info_label = ctk.CTkLabel(
            update_row,
            text="",
            wraplength=350
        )
        update_button = ctk.CTkButton(
            update_row,
            text="Vakitleri Güncelle",
            width=160,
            command=self._update_prayer_times
        )
        
        self.info_label.pack(side="left", padx=10, fill="x", expand=True)
        update_button.pack(side="right", padx=10)
        update_row.pack(fill="x", pady=5)
        
        # Orientation selection row (moved below update button)
        direction_row = self._create_settings_row(container)
        direction_label = ctk.CTkLabel(
            direction_row,
            text="Saat Görünümü",
            font=("Arial", 12, "bold"),
            anchor="w",
            width=100
        )
        
        # Radio buttons frame
        radio_frame = ctk.CTkFrame(direction_row)
        self.direction_var = ctk.StringVar(
            value="horizontal" if self._settings["Display"]["orientation"] == "horizontal"
            else "vertical"
        )
        
        horizontal_radio = ctk.CTkRadioButton(
            radio_frame,
            text="Yatay",
            variable=self.direction_var,
            value="horizontal",
            command=self._on_orientation_change
        )
        vertical_radio = ctk.CTkRadioButton(
            radio_frame,
            text="Dikey",
            variable=self.direction_var,
            value="vertical",
            command=self._on_orientation_change
        )
        
        direction_label.pack(side="left", padx=10)
        radio_frame.pack(side="left", fill="x", expand=True)
        horizontal_radio.pack(side="left", padx=10)
        vertical_radio.pack(side="left", padx=10)
        direction_row.pack(fill="x", pady=5)
        
        return container
    
    def _center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = 500
        height = 300  # Updated height
        
        x = (self.window.winfo_screenwidth() - width) // 2
        y = (self.window.winfo_screenheight() - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    # Rest of the methods remain the same...
    def _create_settings_row(self, parent):
        """Create a row frame for settings"""
        return ctk.CTkFrame(parent)
    
    def _set_initial_values(self):
        """Set initial values for widgets"""
        current_city = next(
            (city for city in Tools.get_cities()
            if city["id"] == self._settings["LOCATION"]["city"]["id"]),
            None
        )
        if current_city:
            self.city_entry.insert(0, current_city["plaka"])
        
        if "district" in self._settings["LOCATION"] and self._settings["LOCATION"]["district"]:
            current_district = self._settings["LOCATION"]["district"]["name"]
            self.district_combobox.set(current_district)
    
    def _show_info(self, message, level="info"):
        """Display info message"""
        colors = {
            "info": "gray",
            "success": "green",
            "error": "red"
        }
        self.info_label.configure(
            text=message,
            text_color=colors.get(level, "gray")
        )
    
    def _update_prayer_times(self):
        """Update prayer times for selected district"""
        district_id = self._settings["LOCATION"]["district"]["id"]
        
        fetcher = DiyanetApi()
        prayer_times = fetcher.fetch_prayer_times(district_id)
        
        if prayer_times:
            Tools.update_prayer_times(prayer_times)
            self._show_info("Namaz vakitleri başarıyla güncellendi!", "success")
            if hasattr(self.root, 'clock_widget'):
                self.root.after(1000, self.root.clock_widget.update_clock)
        else:
            self._show_info("Namaz vakitleri güncellenirken hata oluştu!", "error")
    
    def _fetch_districts(self):
        """Fetch districts for selected city"""
        city_code = self.city_entry.get()
        city_data = Tools.get_cities()
        
        if not city_data:
            self._show_info("Şehir verileri yüklenemedi!", "error")
            return
        
        city_info = next(
            (city for city in city_data if city["plaka"] == city_code),
            None
        )
        if not city_info:
            self._show_info("Geçersiz plaka kodu!", "error")
            return
        
        fetcher = DiyanetApi()
        districts = fetcher.get_districts(city_info["id"])
        
        if districts:
            district_names = list(districts.keys())
            self.district_combobox.configure(values=district_names)
            if district_names:
                self.district_combobox.set(district_names[0])
            self.district_mapping = districts
            
            self._settings["LOCATION"].update({
                "city": {"name": city_info["il"], "id": city_info["id"]},
                "district": {
                    "name": district_names[0],
                    "id": districts[district_names[0]]
                }
            })
            
            self._show_info(
                f"{city_info['il']} ili için {len(districts)} ilçe başarıyla getirildi.",
                "success"
            )
        else:
            self._show_info("İlçeler getirilemedi!", "error")
    
    def _on_orientation_change(self):
        """Handle orientation change"""
        orientation = (
            "horizontal" if self.direction_var.get() == "horizontal"
            else "vertical"
        )
        
        if self._settings["Display"]["orientation"] != orientation:
            self._settings["Display"]["orientation"] = orientation
            Tools.update_settings(self._settings)
            
            if hasattr(self.root, 'clock_widget'):
                self.root.clock_widget.update_orientation()
    
    def _save_settings(self):
        """Save all settings"""
        city_code = self.city_entry.get()
        district_name = self.district_combobox.get()
        
        if not (city_code and district_name):
            self._show_info("Lütfen il ve ilçe seçiniz!", "error")
            return
        
        city_data = Tools.get_cities()
        if not city_data:
            self._show_info("Şehir verileri yüklenemedi!", "error")
            return
        
        city_info = next(
            (city for city in city_data if city["plaka"] == city_code),
            None
        )
        if not city_info:
            self._show_info("Geçersiz plaka kodu!", "error")
            return
        
        district_id = self.district_mapping.get(district_name)
        self._settings["LOCATION"].update({
            "city": {"name": city_info["il"], "id": city_info["id"]},
            "district": {"name": district_name, "id": district_id}
        })
        
        Tools.update_settings(self._settings)
        
        self.current_location_label.configure(
            text=f"Aktif Konum: {district_name} / {city_info['il']}"
        )
        
        self._show_info("Ayarlar başarıyla kaydedildi!", "success")
        
        if hasattr(self.root, 'clock_widget'):
            self.root.clock_widget.update_clock()


class DiyanetApi:
    BASE_URL = "https://namazvakitleri.diyanet.gov.tr/tr-TR/"

    def _make_request(self, url, params=None):
        try:
            logger.info(f"API isteği yapılıyor: {url}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"API isteği başarısız oldu: {e}")
        except json.JSONDecodeError:
            logger.error("API yanıtı geçerli bir JSON değil.")

    def get_districts(self, city_id):
        url = f"{self.BASE_URL}home/GetRegList"
        params = {'ChangeType': 'state', 'CountryId': '2', 'Culture': 'tr-TR', 'StateId': city_id}
        districts = self._make_request(url, params).json().get('StateRegionList', [])
        return {d.get("IlceAdi"): d.get("IlceID") for d in districts}

    def fetch_prayer_times(self, district_id):
        url = f"{self.BASE_URL}{district_id}"
        response = self._make_request(url)
        return self.parse_times(response.text)

    def parse_times(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        logger.info(f"Soup: {soup.title.string}")
        table = soup.select_one("#tab-1 .vakit-table tbody")

        if not table:
            logger.error("Vakit tablosu bulunamadı")
            return None

        data = {}
        for row in table.find_all("tr"):
            cells = [td.text.strip() for td in row.find_all("td")]
            tarih = cells[0].split()[:3]
            tarih_iso = f"{tarih[2]}-{self.month_to_number(tarih[1])}-{tarih[0]}"
            vakitler = cells[2:]
            data[tarih_iso] = vakitler
        return data

    @staticmethod
    def month_to_number(month_name):
        months = {
            "Ocak": "01", "Şubat": "02", "Mart": "03", "Nisan": "04",
            "Mayıs": "05", "Haziran": "06", "Temmuz": "07", "Ağustos": "08",
            "Eylül": "09", "Ekim": "10", "Kasım": "11", "Aralık": "12"
        }
        return months.get(month_name, None)

# Ana pencere oluştur
if __name__ == "__main__":
    try:
        Tools.configure_logging("INFO")
        logger.info("-------Program başlatıldı-------")
        
        # Ayarları kontrol et ve düzelt
        Tools().validate_and_fix_settings()
        
        root = tk.Tk()
        root.withdraw()  # Ana pencereyi gizle
        
        clock_widget = ClockWidget(root)
        root.clock_widget = clock_widget  # ClockWidget'a referans ekle
        
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Program kapatıldı")
    except Exception as e:
        logger.error(f"Program başlatılırken hata oluştu: {e}")
        raise

# ptinstaller -w -i "icon.ico" -n "NamazVakitleri" -p "main.py" -o "dist" --onefile
# pyinstaller --onefile --noconsole --icon=icon.ico main.py

