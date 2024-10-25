import tkinter as tk
from tkinter import font
from datetime import datetime, timedelta
import threading
from helper import ZamanGetir, ZamanHesapla, Utility
from settings import SettingsWindow

class ClockApp:
    """Sonraki namaz vaktine kalan süreyi gösteren arayüz uygulaması."""

    COLORS = {
        "Oxford Blue": "#0a1932",
        "Rosewood": "#540000",
        "Fire Brick": "#c1121f",
        "Orange Peel": "#FFA340",
        "White": "#ffffff",
        "Dark": "#1F2633"
    }

    WINDOW_SIZES = {
        "horizontal": {"width": 80, "height": 32},
        "vertical": {"width": 32, "height": 72}
    }

    FONTS = {
        "default": {"family": "Roboto", "size": 11, "weight": "bold"},
        "fallback": {"family": "Arial", "size": 11, "weight": "bold"}
    }

    CONFIG = {
        "initial_position": {"x": 1453, "y_offset": 0},
        "snap_threshold": 20,
        "update_interval_ms": 1000
    }

    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.configure(bg=self.COLORS["Oxford Blue"])
        self.root.attributes("-alpha", 1.0)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        self.initialize_variables()
        self.configure_window()
        self.setup_fonts()
        self.setup_labels()
        self.setup_events()
        
        # Ayarları yükle ve kontrol et
        self.settings = Utility.load_json("ayarlar.json") or {}
        if not self.settings:
            self.show_settings_window()
        else:
            self.setup_prayer_manager()
            self.create_context_menu()
            self.update_vakitler()
            
        self.keep_on_top()
        self.root.mainloop()

    def initialize_variables(self):
        """Değişkenleri başlat ve ekran boyutlarını al."""
        self.offset_x = 0
        self.offset_y = 0
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.snap_threshold = self.CONFIG["snap_threshold"]
        self.display_vertical = False
        self.manager = ZamanGetir()
        self.vakitler = {}
        self.next_prayer_time = None

    def configure_window(self):
        """Pencere boyutunu ve konumunu ayarla."""
        self.window_sizes = self.WINDOW_SIZES
        self.set_window_geometry(initial=True)

    def set_window_geometry(self, initial=False):
        """Pencere geometrisini görüntüleme yönüne göre ayarla."""
        size = self.WINDOW_SIZES["vertical" if self.display_vertical else "horizontal"]
        width, height = size["width"], size["height"]

        if initial:
            x = self.CONFIG["initial_position"]["x"]
            y = self.screen_height - height - self.CONFIG["initial_position"]["y_offset"]
        else:
            x, y = self.get_current_position()

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_fonts(self):
        """Zaman etiketi için yazı tipini ayarla."""
        try:
            self.custom_font = font.Font(**self.FONTS["default"])
        except Exception:
            self.custom_font = font.Font(**self.FONTS["fallback"])

    def setup_labels(self):
        """Zaman etiketini oluştur ve yerleştir."""
        self.time_label = tk.Label(
            self.root,
            font=self.custom_font,
            fg=self.COLORS["White"],
            bg=self.COLORS["Oxford Blue"]
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
        if self.settings.get('ilce_id'):
            self.manager.URL = f"{self.manager.BASE_URL}{self.settings['ilce_id']}"

    def create_context_menu(self):
        """Sağ tık menüsünü oluştur."""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        
        # Bölge bilgisi
        location = f"{self.settings.get('ilce_adi', '?')}/{self.settings.get('il', '?')}"
        self.context_menu.add_command(label=location, state="disabled")
        
        # Bölge değiştirme
        self.context_menu.add_command(label="Bölge Değiştir", command=self.show_settings_window)
        
        # Vakitleri güncelle
        self.context_menu.add_command(label="Vakitleri Güncelle", command=self.update_vakitler_manual)
        
        # Saydamlık alt menüsü
        opacity_menu = tk.Menu(self.context_menu, tearoff=0)
        opacity_menu.add_command(label="50%", command=lambda: self.set_opacity(0.5))
        opacity_menu.add_command(label="75%", command=lambda: self.set_opacity(0.75))
        opacity_menu.add_command(label="100%", command=lambda: self.set_opacity(1.0))
        self.context_menu.add_cascade(label="Saydamlık", menu=opacity_menu)
        
        # Yön alt menüsü
        format_menu = tk.Menu(self.context_menu, tearoff=0)
        format_menu.add_command(label="Yatay", command=self.set_display_format_horizontal)
        format_menu.add_command(label="Dikey", command=self.set_display_format_vertical)
        self.context_menu.add_cascade(label="Yön", menu=format_menu)
        
        # Ayraç ve Çıkış
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Kapat", command=self.root.destroy)

    def show_settings_window(self):
        """Ayarlar penceresini göster."""
        def settings_callback(new_settings):
            self.settings = new_settings
            self.setup_prayer_manager()
            self.update_vakitler()
            self.create_context_menu()
            
        SettingsWindow(self.root, settings_callback)

    def update_vakitler_manual(self):
        """Vakitleri manuel olarak güncelle."""
        self.manager.update_times()
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
        except ValueError:
            return (self.CONFIG["initial_position"]["x"], 
                   self.screen_height - self.WINDOW_SIZES["horizontal"]["height"])

    def click_window(self, event):
        """Pencere tıklama olayını işle."""
        self.offset_x = event.x
        self.offset_y = event.y

    def drag_window(self, event):
        """Pencere sürükleme olayını işle."""
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y

        x = self.snap_to_edge(x, self.get_window_width(), self.screen_width)
        y = self.snap_to_edge(y, self.get_window_height(), self.screen_height)

        self.root.geometry(f"+{x}+{y}")

    def snap_to_edge(self, pos, window_size, screen_size):
        """Pencereyi ekran kenarlarına yapıştır."""
        if abs(pos) <= self.snap_threshold:
            return 0
        elif abs(screen_size - (pos + window_size)) <= self.snap_threshold:
            return screen_size - window_size
        return pos

    def get_window_width(self):
        """Pencere genişliğini al."""
        return self.WINDOW_SIZES["vertical" if self.display_vertical else "horizontal"]["width"]

    def get_window_height(self):
        """Pencere yüksekliğini al."""
        return self.WINDOW_SIZES["vertical" if self.display_vertical else "horizontal"]["height"]

    def keep_on_top(self):
        """Pencereyi en üstte tut."""
        self.root.attributes("-topmost", True)
        self.root.after(self.CONFIG["update_interval_ms"], self.keep_on_top)

    def update_vakitler(self):
        """Namaz vakitlerini güncelle."""
        threading.Thread(target=self.fetch_and_update_vakitler, daemon=True).start()

    def fetch_and_update_vakitler(self):
        """Namaz vakitlerini getir ve güncelle."""
        self.vakitler = self.manager.get_times()
        self.calculate_next_prayer()
        self.update_time()

    def calculate_next_prayer(self):
        """Bir sonraki namaz vaktini hesapla."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        today_vakitler = self.vakitler.get(today_str, [])
        tomorrow_vakitler = self.vakitler.get(tomorrow_str, [])

        self.next_prayer_time = ZamanHesapla.find_next_prayer_time(today_vakitler)

        if not self.next_prayer_time and tomorrow_vakitler:
            try:
                first_prayer = datetime.strptime(tomorrow_vakitler[0], "%H:%M").time()
                self.next_prayer_time = datetime.combine(now.date() + timedelta(days=1), first_prayer)
            except ValueError:
                self.next_prayer_time = None

    def update_time(self):
        """Geri sayım sayacını güncelle."""
        if self.next_prayer_time:
            hours, minutes, seconds = ZamanHesapla.get_countdown(self.next_prayer_time)
            
            bg_color, fg_color = self.get_colors(hours, minutes)
            self.apply_colors(bg_color, fg_color)

            formatted_time = self.format_time(hours, minutes, seconds)
            self.time_label.config(text=formatted_time)
        else:
            self.apply_colors(self.COLORS["Oxford Blue"], self.COLORS["White"])
            self.time_label.config(text="----")

        self.root.after(self.CONFIG["update_interval_ms"], self.update_time)

    def get_colors(self, hours, minutes):
        """Kalan süreye göre renkleri belirle."""
        if int(hours) >= 1:
            return self.COLORS["Oxford Blue"], self.COLORS["White"]
        elif 30 <= int(minutes) < 60:
            return self.COLORS["Rosewood"], self.COLORS["White"]
        elif 10 <= int(minutes) < 30:
            return self.COLORS["Fire Brick"], self.COLORS["White"]
        else:
            return self.COLORS["Orange Peel"], self.COLORS["Dark"]

    def apply_colors(self, bg_color, fg_color):
        """Arka plan ve yazı rengini uygula."""
        self.root.configure(bg=bg_color)
        self.time_label.configure(bg=bg_color, fg=fg_color)

    def format_time(self, hours, minutes, seconds):
        """Kalan süreyi biçimlendir."""
        if int(hours) > 0:
            formatted_time_H = f"{hours}:{minutes:02}:{seconds:02}"
            formatted_time_V = f"{hours}\n{minutes:02}\n{seconds:02}"
        else:
            formatted_time_H = f"{minutes:02}:{seconds:02}"
            formatted_time_V = f"{minutes:02}\n{seconds:02}"

        return formatted_time_V if self.display_vertical else formatted_time_H


if __name__ == "__main__":
    try:
        ClockApp()
    except KeyboardInterrupt:
        print("\nProgram kapatıldı.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
