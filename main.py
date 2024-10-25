import tkinter as tk
from tkinter import font
from datetime import datetime, timedelta
import threading
import logging
from pathlib import Path
from helper import ZamanGetir, ZamanHesapla, Utility
from settings import SettingsWindow
from config import ConfigManager

class ClockApp:
    """Sonraki namaz vaktine kalan süreyi gösteren arayüz uygulaması."""

    def __init__(self, root=None):
        """
        ClockApp sınıfını başlat.
        
        Args:
            root: Tkinter pencere örneği. None ise yeni pencere oluşturulur.
        """
        self.root = root or tk.Tk()
        self.config = ConfigManager()
        # self.settings = self.load_settings()
        self.settings = self.config._config
        
        # Ayarlardan renkleri al
        self.color_thresholds = self.config.get_config("COLORS")
        
        # Ayarlardan pencere boyutlarını al
        self.window_sizes = self.config.get_config("WINDOW_SIZES")
        
        # Ayarlardan pencere konumunu al
        window_config = self.config.get_config("WINDOW")
        self.snap_threshold = window_config["magnet"]
        
        # Ayarlardan yazı tiplerini al
        self.fonts = self.config.get_config("FONTS")

        # Pencere ayarları
        self.root.configure(bg=self.color_thresholds["60"][0])  # Varsayılan renk
        self.root.attributes("-alpha", 1.0)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.resizable(False, False)

        self.initialize_variables()
        self.configure_window()
        self.setup_fonts()
        self.setup_labels()
        self.setup_events()

        # Ayarları yükle ve kontrol et
        if not self.settings:
            self.show_settings_window()
        else:
            self.setup_prayer_manager()
            self.create_context_menu()
            self.update_vakitler()
            
        self.keep_on_top()

    def initialize_variables(self):
        """Değişkenleri başlat ve ekran boyutlarını al."""
        self.offset_x = 0
        self.offset_y = 0
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.display_vertical = False
        self.manager = ZamanGetir()
        self.vakitler = {}
        self.next_prayer_time = None

    def configure_window(self):
        """Pencere boyutunu ve konumunu ayarla."""
        self.set_window_geometry(initial=True)

    def set_window_geometry(self, initial=False):
        """Pencere geometrisini görüntüleme yönüne göre ayarla."""
        sizes = self.window_sizes["vertical" if self.display_vertical else "horizontal"]
        logging.info(f"Pencere boyutları: {sizes}")
        width, height = sizes["width"], sizes["height"]

        if initial:
            window_config = self.config.get_config("WINDOW")
            x = window_config["position"]["x"]
            y = self.screen_height - height - window_config["position"]["y"]
        else:
            x, y = self.get_current_position()

        # Ekran sınırları içinde kal
        x = max(0, min(x, self.screen_width - width))
        y = max(0, min(y, self.screen_height - height))
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_fonts(self):
        """Zaman etiketi için yazı tipini ayarla."""
        try:
            self.custom_font = font.Font(**self.fonts["default"])
        except Exception:
            logging.warning("Varsayılan yazı tipi yüklenemedi. Yedek yazı tipi kullanılıyor.")
            self.custom_font = font.Font(**self.fonts["fallback"])

    def setup_labels(self):
        """Zaman etiketini oluştur ve yerleştir."""
        initial_colors = self.color_thresholds["60"]  # Varsayılan renk
        self.time_label = tk.Label(
            self.root,
            font=self.custom_font,
            fg=initial_colors[1],
            bg=initial_colors[0]
        )
        self.time_label.pack(expand=True, fill='both')

    def setup_events(self):
        """Pencere olaylarını bağla."""
        self.time_label.bind("<ButtonPress-1>", self.click_window)
        self.time_label.bind("<B1-Motion>", self.drag_window)
        self.time_label.bind("<Button-3>", self.show_context_menu)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def setup_prayer_manager(self):
        """Namaz vakitleri yöneticisini ayarla."""
        ilce_id = self.settings.get("LOCATION").get('ilce_id')
        if ilce_id:
            self.manager.URL = f"{self.manager.BASE_URL}{ilce_id}"

    def create_context_menu(self):
        """Sağ tık menüsünü oluştur."""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        
        # Bölge bilgisi
        il = self.settings.get('LOCATION', '?').get('il_adi', '?')
        ilce = self.settings.get('LOCATION', '?').get('ilce_adi', '?')
        self.context_menu.add_command(label=f"{il}/{ilce}", state="disabled")
        
        # Bölge değiştirme
        self.context_menu.add_command(label="Bölge Değiştir", command=self.show_settings_window)
        
        # Vakitleri güncelle
        self.context_menu.add_command(label="Vakitleri Güncelle", command=self.update_vakitler_manual)
        
        # Saydamlık alt menüsü
        opacity_menu = tk.Menu(self.context_menu, tearoff=0)
        for opacity in [("50%", 0.5), ("75%", 0.75), ("100%", 1.0)]:
            opacity_menu.add_command(
                label=opacity[0], 
                command=lambda x=opacity[1]: self.set_opacity(x)
            )
        self.context_menu.add_cascade(label="Saydamlık", menu=opacity_menu)
        
        # Yön alt menüsü
        format_menu = tk.Menu(self.context_menu, tearoff=0)
        format_menu.add_command(label="Yatay", command=self.set_display_format_horizontal)
        format_menu.add_command(label="Dikey", command=self.set_display_format_vertical)
        self.context_menu.add_cascade(label="Yön", menu=format_menu)
        
        # Ayarları sıfırla
        self.context_menu.add_command(label="Ayarları Sıfırla", command=self.reset_settings)
        
        # Ayraç ve Çıkış
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Kapat", command=self.root.destroy)

    def show_settings_window(self):
        """Ayarlar penceresini göster."""
        def settings_callback(location_settings):
            self.setup_prayer_manager()
            self.update_vakitler()
            self.create_context_menu()

        SettingsWindow(self.root, settings_callback)

    def reset_settings(self):
        """Ayarları sıfırla ve yeniden yükle."""
        self.config.reset_config()
        self.setup_prayer_manager()
        self.update_vakitler()
        self.create_context_menu()

    def update_vakitler_manual(self):
        """Vakitleri manuel olarak güncelle."""
        threading.Thread(target=self.fetch_and_update_vakitler, daemon=True).start()

    def show_context_menu(self, event):
        """Sağ tık menüsünü göster."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def set_opacity(self, opacity_value):
        """Pencere saydamlığını ayarla."""
        self.root.attributes("-alpha", opacity_value)

    def set_display_format_horizontal(self):
        """Yatay görüntüleme moduna geç."""
        if self.display_vertical:
            self.display_vertical = False
            self.set_window_geometry()

    def set_display_format_vertical(self):
        """Dikey görüntüleme moduna geç."""
        if not self.display_vertical:
            self.display_vertical = True
            self.set_window_geometry()

    def get_current_position(self):
        """Mevcut pencere konumunu al."""
        try:
            geometry = self.root.geometry()
            _, x, y = geometry.split('+')
            return int(x), int(y)
        except (ValueError, IndexError):
            window_config = self.config.get_config("WINDOW")
            return (window_config["position"]["x"], 
                   self.screen_height - self.window_sizes["horizontal"]["height"])

    def click_window(self, event):
        """Pencere tıklama olayını işle."""
        self.offset_x = event.x
        self.offset_y = event.y

    def drag_window(self, event):
        """Pencere sürükleme olayını işle."""
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        
        sizes = self.window_sizes["vertical" if self.display_vertical else "horizontal"]
        width, height = sizes["width"], sizes["height"]

        x = self.snap_to_edge(x, width, self.screen_width)
        y = self.snap_to_edge(y, height, self.screen_height)

        self.root.geometry(f"+{x}+{y}")

    def snap_to_edge(self, pos, size, screen_size):
        """Pencereyi ekran kenarlarına yapıştır."""
        if abs(pos) <= self.snap_threshold:
            return 0
        elif abs(screen_size - (pos + size)) <= self.snap_threshold:
            return screen_size - size
        return pos

    def keep_on_top(self):
        """Pencereyi en üstte tut."""
        self.root.lift()
        self.root.after(1000, self.keep_on_top)

    def update_vakitler(self):
        """Namaz vakitlerini güncelle."""
        threading.Thread(target=self.fetch_and_update_vakitler, daemon=True).start()

    def fetch_and_update_vakitler(self):
        """Namaz vakitlerini getir ve güncelle."""
        try:
            self.vakitler = self.manager.get_times()
            if self.vakitler:
                self.calculate_next_prayer()
            self.update_time()
        except Exception as e:
            logging.error(f"Vakit güncelleme hatası: {e}")

    def calculate_next_prayer(self):
        """Bir sonraki namaz vaktini hesapla."""
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

            today_vakitler = self.vakitler.get(today_str, [])
            tomorrow_vakitler = self.vakitler.get(tomorrow_str, [])

            self.next_prayer_time = ZamanHesapla.find_next_prayer_time(today_vakitler)

            if not self.next_prayer_time and tomorrow_vakitler:
                first_prayer = datetime.strptime(tomorrow_vakitler[0], "%H:%M").time()
                self.next_prayer_time = datetime.combine(now.date() + timedelta(days=1), first_prayer)
        except Exception as e:
            logging.error(f"Sonraki vakit hesaplama hatası: {e}")
            self.next_prayer_time = None

    def update_time(self):
        """Geri sayım sayacını güncelle."""
        try:
            if not self.next_prayer_time:
                default_colors = self.color_thresholds["60"]
                self.apply_colors(default_colors[0], default_colors[1])
                self.time_label.config(text="--:--")
                self.root.after(1000, self.update_time)
                return

            hours, minutes, seconds = ZamanHesapla.get_countdown(self.next_prayer_time)
            bg_color, fg_color = self.get_colors(hours, minutes)
            self.apply_colors(bg_color, fg_color)

            formatted_time = self.format_time(hours, minutes, seconds)
            self.time_label.config(text=formatted_time)

        except Exception as e:
            logging.error(f"Zaman güncelleme hatası: {e}")
            self.time_label.config(text="--:--")
            
        finally:
            self.root.after(1000, self.update_time)

    def get_colors(self, hours, minutes):
        """Kalan süreye göre renkleri belirle."""
        minutes_total = hours * 60 + minutes
        
        if minutes_total >= 60:
            return self.color_thresholds["60"]
        elif minutes_total >= 30:
            return self.color_thresholds["30"]
        elif minutes_total >= 10:
            return self.color_thresholds["10"]
        else:
            return self.color_thresholds["0"]

    def apply_colors(self, bg_color, fg_color):
        """Arka plan ve yazı rengini uygula."""
        try:
            self.root.configure(bg=bg_color)
            self.time_label.configure(bg=bg_color, fg=fg_color)
        except Exception as e:
            logging.error(f"Renk uygulama hatası: {e}")
            # Hata durumunda varsayılan renkleri kullan
            default_colors = self.color_thresholds["60"]
            self.root.configure(bg=default_colors[0])
            self.time_label.configure(bg=default_colors[0], fg=default_colors[1])

    def format_time(self, hours, minutes, seconds):
        """Kalan süreyi biçimlendir."""
        if self.display_vertical:
            if hours > 0:
                return f"{hours}\n{minutes:02d}\n{seconds:02d}"
            return f"{minutes:02d}\n{seconds:02d}"
        else:
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            return f"{minutes:02d}:{seconds:02d}"

    def run(self):
        """Uygulamayı başlat."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.destroy()
        except Exception as e:
            logging.error(f"Uygulama hatası: {e}")
            self.root.destroy()


def main():
    """Ana uygulama fonksiyonu."""
    try:
        # Log yapılandırması
        Utility.configure_logging("debug.log")
        
        # Uygulama klasörünü oluştur
        app_dir = Utility.get_working_directory() 
        app_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Uygulama klasörü: {app_dir}")

        # Uygulamayı başlat
        logging.info("Uygulama başlatılıyor...")
        app = ClockApp()
        app.run()
        
    except KeyboardInterrupt:
        logging.info("Uygulama kullanıcı tarafından sonlandırıldı.")
        print("\nProgram kapatıldı.")
    except Exception as e:
        logging.error("Beklenmeyen hata:", exc_info=True)
        print(f"Kritik hata oluştu: {e}")
    finally:
        logging.shutdown()


if __name__ == "__main__":
    main()
