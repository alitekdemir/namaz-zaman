import tkinter as tk
from gui import ClockApp


def NamazVaktiApp():
    """Uygulamayı başlatan fonksiyon."""
    root = tk.Tk()
    app = ClockApp(root)
    root.mainloop()

if __name__ == "__main__":
    try:
        NamazVaktiApp()
    except KeyboardInterrupt:
        print("\nProgram kapatıldı.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

