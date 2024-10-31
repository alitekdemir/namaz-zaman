from setuptools import setup

APP = ['main.py']
# DATA_FILES = ['il_plaka.json']  # JSON dosyasını ekliyoruz
OPTIONS = {
    'argv_emulation': True,
    'packages': [],
    'plist': {
        'CFBundleName': 'NamazZamani',
        'CFBundleVersion': '1.0',
        'CFBundleIdentifier': 'com.example.myapp',
        'LSUIElement': True,  # Terminal penceresini gizler
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
