import tkinter as tk
from tkinter import font
from datetime import datetime, timedelta
import threading
from helper import ZamanGetir, ZamanHesapla

class ClockApp:
    """Tkinter tabanlı GUI uygulaması. Namaz vakitlerine göre geri sayım gösterir."""
    # Renkler sözlüğü
    COLORS = {
        "Oxford Blue": "#0a1932",
        "Rosewood": "#540000",
        "Fire Brick": "#c1121f",
        "Orange Peel": "#FFA340",
        "White": "#ffffff",
        "Dark": "#333333"
    }

    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)           # Başlık çubuğunu kaldırır
        self.root.geometry("88x34")                # Pencere boyutunu ayarlar
        self.root.configure(bg=self.COLORS["Oxford Blue"])  # Başlangıç arkaplan rengini ayarlar
        self.root.attributes("-alpha", 1.0)        # Başlangıç opaklığı (1.0 = tamamen opak)

        # Roboto fontunu yükleme
        try:
            self.custom_font = font.Font(family="Roboto", size=11, weight="bold")
        except:
            # Roboto yüklü değilse, Arial fontunu kullan
            self.custom_font = font.Font(family="Arial", size=11, weight="bold")

        # Saat etiketi (Geri sayım için kullanılacak)
        self.time_label = tk.Label(self.root, font=self.custom_font, fg=self.COLORS["White"], bg=self.COLORS["Oxford Blue"])
        self.time_label.pack(expand=True)

        # Pencereyi taşıma özelliği
        self.offset_x = 0
        self.offset_y = 0
        self.time_label.bind("<ButtonPress-1>", self.click_window)
        self.time_label.bind("<B1-Motion>", self.drag_window)

        # Sağ tıklama menüsü oluşturma
        self.create_context_menu()
        self.time_label.bind("<Button-3>", self.show_context_menu)  # Sağ tıklama için bağlama

        # Klavye kısayolu (Escape tuşu ile kapatma)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        # Ekran boyutlarını al
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Pencere boyutları
        self.window_width_horizontal = 88
        self.window_height_horizontal = 34

        self.window_width_vertical = 34
        self.window_height_vertical = 88

        # Başlangıç konumunu ayarla (Yatay)
        initial_x = 1300
        initial_y = self.screen_height - self.window_height_horizontal
        self.root.geometry(f"{self.window_width_horizontal}x{self.window_height_horizontal}+{initial_x}+{initial_y}")

        # Snapping threshold in pixels
        self.snap_threshold = 20

        # Namaz vakti yöneticisi ve yardımcısı
        self.manager = ZamanGetir()
        self.vakitler = {}
        self.next_prayer_time = None

        # Display format durumu (False = Yatay, True = Dikey)
        self.display_vertical = False

        # Veri güncellemeyi başlat
        self.update_vakitler()

        # Windows'ta pencerenin her zaman üstte kalmasını sağlamak için ek yöntem 1
        self.keep_on_top()

    def keep_on_top(self):
        self.root.attributes("-topmost", True)  # Daima üstte
        self.root.update()  # Pencereyi güncelle
        self.root.after(1000, self.keep_on_top)  # Her saniye kontrol

    def create_context_menu(self):
        """Sağ tıklama menüsünü oluşturur."""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        # Vakitleri güncelleme komutu
        self.context_menu.add_command(label="Vakitleri Güncelle", command=self.update_vakitler_manual)

        # Opacity değiştirme alt menüsü
        opacity_menu = tk.Menu(self.context_menu, tearoff=0)
        opacity_menu.add_command(label="50%", command=lambda: self.set_opacity(0.5))
        opacity_menu.add_command(label="75%", command=lambda: self.set_opacity(0.75))
        opacity_menu.add_command(label="100%", command=lambda: self.set_opacity(1.0))
        self.context_menu.add_cascade(label="Opacity Değiştir", menu=opacity_menu)

        # Zaman görüntüleme biçimi alt menüsü
        format_menu = tk.Menu(self.context_menu, tearoff=0)
        format_menu.add_command(label="Yatay", command=self.set_display_format_horizontal)
        format_menu.add_command(label="Dikey", command=self.set_display_format_vertical)
        self.context_menu.add_cascade(label="Yön", menu=format_menu)

        # Çıkış ve kapatma komutları
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Kapat", command=self.root.destroy)

    def update_vakitler_manual(self):
        """Kullanıcı tarafından manuel olarak vakitleri günceller."""
        self.manager.update_times()
        self.update_vakitler()

    def show_context_menu(self, event):
        """Sağ tıklama menüsünü gösterir."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def set_opacity(self, opacity_value):
        """Pencerenin opaklığını ayarlar."""
        self.root.attributes("-alpha", opacity_value)

    def set_display_format_horizontal(self):
        """Zaman görüntüleme biçimini yatay olarak ayarlar."""
        if self.display_vertical:
            self.display_vertical = False
            self.update_window_size()
            self.update_time()

    def set_display_format_vertical(self):
        """Zaman görüntüleme biçimini dikey olarak ayarlar."""
        if not self.display_vertical:
            self.display_vertical = True
            self.update_window_size()
            self.update_time()

    def update_window_size(self):
        """Pencere boyutunu günceller."""
        if self.display_vertical:
            new_width = self.window_width_vertical
            new_height = self.window_height_vertical
        else:
            new_width = self.window_width_horizontal
            new_height = self.window_height_horizontal
        # Güncel konumu al
        current_geometry = self.root.geometry()
        pos = current_geometry.split('+')[1:]
        if len(pos) == 2:
            x, y = pos
        else:
            x, y = 100, 100  # Varsayılan konum
        self.root.geometry(f"{new_width}x{new_height}+{x}+{y}")

    def click_window(self, event):
        """Pencereye tıklandığında sürükleme başlangıcı için koordinatları kaydeder."""
        self.offset_x = event.x
        self.offset_y = event.y

    def drag_window(self, event):
        """Pencereyi sürükler ve ekran kenarlarına yapışmasını sağlar."""
        # Yeni pencere konumunu hesapla
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y

        # Snapping mantığı
        # Sol kenar
        if abs(x) <= self.snap_threshold:
            x = 0
        # Sağ kenar
        elif abs(self.screen_width - (x + self.get_window_width())) <= self.snap_threshold:
            x = self.screen_width - self.get_window_width()
        # Üst kenar
        if abs(y) <= self.snap_threshold:
            y = 0
        # Alt kenar
        elif abs(self.screen_height - (y + self.get_window_height())) <= self.snap_threshold:
            y = self.screen_height - self.get_window_height()

        # Pencere konumunu ayarla
        self.root.geometry(f"+{x}+{y}")

    def get_window_width(self):
        """Güncel pencere genişliğini döner."""
        return self.window_width_vertical if self.display_vertical else self.window_width_horizontal

    def get_window_height(self):
        """Güncel pencere yüksekliğini döner."""
        return self.window_height_vertical if self.display_vertical else self.window_height_horizontal

    def update_vakitler(self):
        """Namaz vakitlerini günceller ve bir sonraki namaz vaktine odaklanır."""
        def fetch_and_update():
            self.vakitler = self.manager.get_times()
            self.calculate_next_prayer()
            self.update_time()

        # Veri güncelleme işlemini ayrı bir iş parçacığında gerçekleştir
        threading.Thread(target=fetch_and_update, daemon=True).start()

    def calculate_next_prayer(self):
        """Bir sonraki namaz vakitini hesaplar."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        yarin_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        bugun_vakitler = self.vakitler.get(today_str, [])
        yarin_vakitler = self.vakitler.get(yarin_str, [])

        self.next_prayer_time = ZamanHesapla.find_next_prayer_time(bugun_vakitler)
        if not self.next_prayer_time and yarin_vakitler:
            # Bugünün tüm vakitleri geçtiyse, yarının ilk vakitini al
            try:
                ilk_vakit = datetime.strptime(yarin_vakitler[0], "%H:%M").time()
                self.next_prayer_time = datetime.combine(now.date() + timedelta(days=1), ilk_vakit)
            except ValueError:
                self.next_prayer_time = None

    def update_time(self):
        """Geri sayımı günceller, arkaplan ve metin rengini ayarlar ve ekranda gösterir."""
        if self.next_prayer_time:
            remaining_hms = ZamanHesapla.get_countdown(self.next_prayer_time)
            remaining_time = self.next_prayer_time - datetime.now()

            # Kalan süreyi saniye cinsinden al
            remaining_seconds = max(int(remaining_time.total_seconds()), 0)
            remaining_minutes = remaining_seconds // 60
            remaining_hours = remaining_minutes // 60

            # Renk ayarlama mantığı
            if remaining_hours >= 1:
                bg_color = self.COLORS["Oxford Blue"]
                fg_color = self.COLORS["White"]
            elif 30 <= remaining_minutes < 60:  # 30 <= minutes < 60
                bg_color = self.COLORS["Rosewood"]
                fg_color = self.COLORS["White"]
            elif 10 <= remaining_minutes < 30:  # 10 <= minutes < 30
                bg_color = self.COLORS["Fire Brick"]
                fg_color = self.COLORS["White"]
            else:  # remaining_time < 10 minutes
                bg_color = self.COLORS["Orange Peel"]
                fg_color = self.COLORS["Dark"]

            # Arkaplan ve metin rengini ayarla
            self.root.configure(bg=bg_color)
            self.time_label.configure(bg=bg_color, fg=fg_color)

            # Zaman formatına göre metni ayarla
            if self.display_vertical:
                # Dikey format: HH\nMM\nSS
                remaining_hms_formatted = remaining_hms.replace(":", "\n")
                self.time_label.config(text=remaining_hms_formatted)
            else:
                # Yatay format: HH:MM:SS
                self.time_label.config(text=remaining_hms)

        else:
            self.time_label.config(text="----")
            self.root.configure(bg=self.COLORS["Oxford Blue"])
            self.time_label.configure(bg=self.COLORS["Oxford Blue"], fg=self.COLORS["White"])

        # Bir sonraki güncelleme için 1 saniye sonra tekrar çağır
        self.root.after(1000, self.update_time)

