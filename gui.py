import tkinter as tk
from tkinter import font
from datetime import datetime, timedelta
import threading
from helper import ZamanGetir, ZamanHesapla


class ClockApp:
    """Tkinter-based GUI application displaying a countdown to the next prayer time."""

    # Renkler
    COLORS = {
        "Oxford Blue": "#0a1932",
        "Rosewood": "#540000",
        "Fire Brick": "#c1121f",
        "Orange Peel": "#FFA340",
        "White": "#ffffff",
        "Dark": "#1F2633"
    }
    # Zaman dilimleri için renk atamaları ve default seçenekler
    TIMED_CONDITIONS = {
        60: ("#0a1932", "#ffffff"),  # 1 saat veya daha fazla
        30: ("#540000", "#ffffff"),  # 30-59 dakika arası
        10: ("#c1121f", "#ffffff"),  # 10-29 dakika arası
        0:  ("#FFA340", "#1F2633")   # 10 dakikadan az
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

    def __init__(self, root):
        self.root = root
        self.root.configure(bg=self.COLORS["Oxford Blue"])
        self.root.attributes("-alpha", 1.0)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)  # Remove title bar

        self.initialize_variables()
        self.configure_window()
        self.setup_fonts()
        self.setup_labels()
        self.setup_events()
        self.create_context_menu()
        self.update_vakitler()
        self.keep_on_top()

    def initialize_variables(self):
        """Initialize variables and retrieve screen dimensions."""
        self.offset_x = 0
        self.offset_y = 0

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.snap_threshold = self.CONFIG["snap_threshold"]

        self.manager = ZamanGetir()
        self.vakitler = {}
        self.next_prayer_time = None

        self.display_vertical = False  # False = Horizontal, True = Vertical

    def configure_window(self):
        """Configure the initial window size and position."""
        self.window_sizes = self.WINDOW_SIZES
        self.set_window_geometry(initial=True)

    def set_window_geometry(self, initial=False):
        """Set window geometry based on display orientation."""
        if self.display_vertical:
            size = self.WINDOW_SIZES["vertical"]
        else:
            size = self.WINDOW_SIZES["horizontal"]

        width = size["width"]
        height = size["height"]

        if initial:
            x = self.CONFIG["initial_position"]["x"]
            y = self.screen_height - height - self.CONFIG["initial_position"]["y_offset"]
        else:
            x, y = self.get_current_position()

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_fonts(self):
        """Set up the font for the time label."""
        try:
            font_config = self.FONTS["default"]
            self.custom_font = font.Font(**font_config)
        except Exception:
            font_config = self.FONTS["fallback"]
            self.custom_font = font.Font(**font_config)

    def setup_labels(self):
        """Create and place the time label."""
        self.time_label = tk.Label(
            self.root,
            font=self.custom_font,
            fg=self.COLORS["White"],
            bg=self.COLORS["Oxford Blue"]
        )
        self.time_label.pack(expand=True, fill='both')

    def setup_events(self):
        """Bind events for window movement and context menu."""
        self.time_label.bind("<ButtonPress-1>", self.click_window)
        self.time_label.bind("<B1-Motion>", self.drag_window)
        self.time_label.bind("<Button-3>", self.show_context_menu)  # Right-click

        self.root.bind("<Escape>", lambda e: self.root.destroy())  # Escape key to close

    def keep_on_top(self):
        """Ensure the window stays on top."""
        self.root.attributes("-topmost", True)
        self.root.after(self.CONFIG["update_interval_ms"], self.keep_on_top)

    def create_context_menu(self):
        """Create the right-click context menu."""
        self.context_menu = tk.Menu(self.root, tearoff=0)

        # Update prayer times
        self.context_menu.add_command(label="Vakitleri Güncelle", command=self.update_vakitler_manual)

        # Opacity submenu
        opacity_menu = tk.Menu(self.context_menu, tearoff=0)
        opacity_menu.add_command(label="50%", command=lambda: self.set_opacity(0.5))
        opacity_menu.add_command(label="75%", command=lambda: self.set_opacity(0.75))
        opacity_menu.add_command(label="100%", command=lambda: self.set_opacity(1.0))
        self.context_menu.add_cascade(label="Opacity Değiştir", menu=opacity_menu)

        # Display format submenu
        format_menu = tk.Menu(self.context_menu, tearoff=0)
        format_menu.add_command(label="Yatay", command=self.set_display_format_horizontal)
        format_menu.add_command(label="Dikey", command=self.set_display_format_vertical)
        self.context_menu.add_cascade(label="Yön", menu=format_menu)

        # Separator and Exit
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Kapat", command=self.root.destroy)

    def update_vakitler_manual(self):
        """Manually trigger the update of prayer times."""
        self.manager.update_times()
        self.update_vakitler()

    def show_context_menu(self, event):
        """Display the context menu at the cursor position."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def set_opacity(self, opacity_value):
        """Set the window's opacity."""
        self.root.attributes("-alpha", opacity_value)

    def set_display_format_horizontal(self):
        """Set the display format to horizontal."""
        if self.display_vertical:
            self.display_vertical = False
            self.set_window_geometry()

    def set_display_format_vertical(self):
        """Set the display format to vertical."""
        if not self.display_vertical:
            self.display_vertical = True
            self.set_window_geometry()

    def get_current_position(self):
        """Retrieve the current window position."""
        try:
            geometry = self.root.geometry()
            _, x, y = geometry.split('+')
            return int(x), int(y)
        except ValueError:
            return self.CONFIG["initial_position"]["x"], self.screen_height - self.WINDOW_SIZES["horizontal"]["height"]

    def click_window(self, event):
        """Store the offset when the window is clicked for dragging."""
        self.offset_x = event.x
        self.offset_y = event.y

    def drag_window(self, event):
        """Handle the window dragging with snapping to screen edges."""
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y

        x = self.snap_to_edge(x, self.get_window_width(), self.screen_width)
        y = self.snap_to_edge(y, self.get_window_height(), self.screen_height)

        self.root.geometry(f"+{x}+{y}")

    def snap_to_edge(self, pos, window_size, screen_size):
        """Snap the window to the screen edge if within the threshold."""
        if abs(pos) <= self.snap_threshold:
            return 0
        elif abs(screen_size - (pos + window_size)) <= self.snap_threshold:
            return screen_size - window_size
        return pos

    def get_window_width(self):
        """Get the current window width based on orientation."""
        return self.WINDOW_SIZES["vertical"]["width"] if self.display_vertical else self.WINDOW_SIZES["horizontal"]["width"]

    def get_window_height(self):
        """Get the current window height based on orientation."""
        return self.WINDOW_SIZES["vertical"]["height"] if self.display_vertical else self.WINDOW_SIZES["horizontal"]["height"]

    def update_vakitler(self):
        """Start a thread to fetch and update prayer times."""
        threading.Thread(target=self.fetch_and_update_vakitler, daemon=True).start()

    def fetch_and_update_vakitler(self):
        """Fetch prayer times and update the display."""
        self.vakitler = self.manager.get_times()
        self.calculate_next_prayer()
        self.update_time()

    def calculate_next_prayer(self):
        """Determine the next prayer time."""
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
        """Update the countdown timer and refresh the display."""
        if self.next_prayer_time:
            remaining_time = self.next_prayer_time - datetime.now()
            remaining_seconds = max(int(remaining_time.total_seconds()), 0)
            remaining_minutes, remaining_seconds = divmod(remaining_seconds, 60)
            remaining_hours, remaining_minutes = divmod(remaining_minutes, 60)

            bg_color, fg_color = self.get_colors(remaining_hours, remaining_minutes)
            self.apply_colors(bg_color, fg_color)

            formatted_time = self.format_time(remaining_hours, remaining_minutes, remaining_seconds)
            self.time_label.config(text=formatted_time)
        else:
            self.apply_colors(self.COLORS["Oxford Blue"], self.COLORS["White"])
            self.time_label.config(text="----")

        self.root.after(self.CONFIG["update_interval_ms"], self.update_time)

    def get_colors(self, hours, minutes):
        """Determine colors based on the remaining time."""
        if hours >= 1:
            return self.COLORS["Oxford Blue"], self.COLORS["White"]
        elif 30 <= minutes < 60:
            return self.COLORS["Rosewood"], self.COLORS["White"]
        elif 10 <= minutes < 30:
            return self.COLORS["Fire Brick"], self.COLORS["White"]
        else:
            return self.COLORS["Orange Peel"], self.COLORS["Dark"]

    def apply_colors(self, bg_color, fg_color):
        """Apply background and foreground colors to the window and label."""
        self.root.configure(bg=bg_color)
        self.time_label.configure(bg=bg_color, fg=fg_color)

    def format_time2(self, hours, minutes, seconds):
        """Format the remaining time for display."""
        # formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"
        formatted_time = f"{hours}:{minutes:02}:{seconds:02}"
        return formatted_time.replace(":", "\n") if self.display_vertical else formatted_time



    def format_time(self, hours, minutes, seconds):
        """Format the remaining time for display."""
        if hours > 0:
            formatted_time_H = f"{hours}:{minutes:02}:{seconds:02}"
            formatted_time_V = f"{hours}\n{minutes:02}\n{seconds:02}"
        else:
            formatted_time_H = f"{minutes:02}:{seconds:02}"
            formatted_time_V = f"{minutes:02}\n{seconds:02}"

        return formatted_time_V if self.display_vertical else formatted_time_H
