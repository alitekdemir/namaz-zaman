import logging as logger
import tkinter as tk
from tools import Tools
from clock_widget import ClockWidget

if __name__ == "__main__":
    try:
        tools = Tools()
        tools.configure_logging("INFO")
        logger.info("-------Program başlatıldı-------")

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

# pyinstaller --onefile --noconsole main.py