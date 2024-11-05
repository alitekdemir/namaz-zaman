import tkinter as tk
from datetime import datetime
import logging as logger
from tools import Tools


class ClockWidget:
    def __init__(self, root):
        self.root = root
        self._settings = Tools.get_settings()  # Ayarları doğrudan Tools'dan al
        self._prayer_times = Tools.get_prayer_times() # {date: [time1, time2, ...]}
        self._next_prayer_time = Tools.find_next_prayer_time(self._prayer_times) # datetime object "%Y-%m-%d %H:%M"

        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)

        logger.debug(f"Ayarlardaki konum: {self._settings['DISPLAY']['position']}")

        colors = self._settings["COLORS"]["standard"]
        font_settings = self._settings["FONTS"]["clock"]

        self.window.configure(bg=colors["background"])
        self.window.attributes('-topmost', self._settings["DISPLAY"]["always_on_top"])

        self.label = tk.Label(
            self.window,
            text="00:00",
            font=(font_settings["family"], font_settings["size"], font_settings["weight"]),
            fg=colors["text"],
            bg=colors["background"]
        )
        self.label.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.initial_geometry_set = False
        self.window.update_idletasks()
        self.set_window_geometry()

        self.is_dragging = False
        self.setup_bindings()
        self.create_context_menu()

        if not Tools.PRAYER_TIMES.exists() or not self._prayer_times:
            logger.info("Vakitler dosyası bulunamadı. Ayarlar penceresi açılıyor...")
            self.root.after(1000, lambda: self.open_settings(None))

        self.update_clock()
        self.keep_on_top()

    def set_window_geometry(self):
        try:
            self.window.update_idletasks()
            is_horizontal = self._settings["DISPLAY"]["orientation"] == "horizontal"

            base_width = self.label.winfo_reqwidth()
            base_height = self.label.winfo_reqheight()

            if is_horizontal:
                width = int(base_width * 1.1)
                height = int(base_height * 1.02)
            else:
                width = int(base_height * 1.1)
                height = int(base_width * 1.05)

            x, y = self._settings["DISPLAY"]["position"].values()

            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()

            x = max(0, min(x, screen_width - width))
            y = max(0, min(y, screen_height - height))
            geometry = f"{width}x{height}+{x}+{y}"

            self.window.geometry(geometry)
            self.window.update_idletasks()
            return width, height

        except Exception as e:
            logger.error(f"Pencere geometrisi ayarlanırken hata: {e}")
            return None, None

    def update_orientation(self):
        current_width = self.window.winfo_width()
        current_height = self.window.winfo_height()
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        self.window.geometry(f"{current_height}x{current_width}+{x}+{y}")
        self.update_clock()

    def update_window_geometry(self):
        """Dinamik boyutlandırma ve konumlandırma"""
        # Dinamik boyutlandırma
        self.window.update_idletasks()  # Label'ın yeni boyutunu hesaplaması için
        width = f"{self.label.winfo_reqwidth() * 1.1 :.0f}"
        height = f"{self.label.winfo_reqheight() * 1.02:.0f}"
        x = self._settings["DISPLAY"]["position"]["x"]
        y = self._settings["DISPLAY"]["position"]["y"]
        self.window.geometry(f"{width}x{height}+{x}+{y}")


    def setup_bindings(self):
        self.window.bind("<Button-1>", self.start_move)
        self.window.bind("<B1-Motion>", self.do_move)
        self.window.bind("<ButtonRelease-1>", self.stop_move)
        self.window.bind("<Double-Button-1>", self.open_settings)
        self.window.bind("<Button-3>", self.show_context_menu)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="Ayarları Aç", command=lambda: self.open_settings(None))
        self.context_menu.add_command(label="Programı Kapat", command=self.close_program)

    def start_move(self, event):
        self.is_dragging = True
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        if not self.is_dragging:
            return

        # Yeni konumu hesapla ve geçici olarak pencereye uygula
        x = self.window.winfo_x() + (event.x - self.x)
        y = self.window.winfo_y() + (event.y - self.y)
        x, y = self.snap_to_edges(x, y)
        self.window.geometry(f"+{x}+{y}")


    def stop_move(self, event):
        if not self.is_dragging:
            return
        self.is_dragging = False

        # Yeni pencere konumunu ayarlara kaydet
        try:
            x, y = self.window.winfo_x(), self.window.winfo_y()
            settings = Tools.get_settings()
            settings["DISPLAY"]["position"].update({"x": x, "y": y})
            Tools.update_settings(settings)
            self._settings = settings
        except Exception as e:
            logger.error(f"Pozisyon kaydedilirken hata oluştu: {e}")


    def snap_to_edges(self, x, y):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        snap_distance = self._settings["DISPLAY"]["snap_distance"]

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
        if (not hasattr(self.root, 'settings_window')
                or not (self.root.settings_window
                        and self.root.settings_window.window.winfo_exists())):
            from settings import SettingsWindow
            self.root.settings_window = SettingsWindow(self.root)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def close_program(self):
        self.root.quit()

    def keep_on_top(self):
        self.window.attributes('-topmost', 1)
        self.window.after(5000, self.keep_on_top)


    def update_clock(self):
        if self._next_prayer_time:
            self.update_remaining_time_display()
        else:
            self.label.config(text="00")

        if not self.is_dragging:  # Sürükleme yapılmıyorsa pencere boyutunu güncelle
            self.update_window_geometry()

        # Güncelleme sıklığını kontrol et
        interval = 1000 if self._settings["DISPLAY"]["show_seconds"] else 60000
        self.root.after(interval, self.update_clock)

    # Kalan süreyi güncelle ve göster
    def update_remaining_time_display(self):
        now = datetime.now()
        if now >= self._next_prayer_time: # Eğer vakit geçtiyse
            # Bir sonraki vakti bul ve güncelle
            self._next_prayer_time = Tools.find_next_prayer_time(self._prayer_times)

        hours, minutes, seconds = Tools.remaining_time(self._next_prayer_time)
        self.update_color_by_time(hours * 60 + minutes) # Renk güncelle
        self.label.config(text=self.format_time(hours, minutes, seconds))

    def format_time(self, hours, minutes, seconds) -> str:
        """Saat metnini ayarlardaki formatlara göre döndür"""
        display = self._settings["DISPLAY"]
        time_parts = []
        separator = "\n" if display["orientation"] == "vertical" else ":"
        
        if hours > 0:
            time_parts.append(str(hours))
            time_parts.append(f"{minutes:02}")
        else:
            time_parts.append(str(minutes))
        
        if display["show_seconds"]:
            time_parts.append(f"{seconds:02}")
            
        return separator.join(time_parts)


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
