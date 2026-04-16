"""
py2app setup script for macOS .app bundle.
Build with: python setup_mac.py py2app
"""
from setuptools import setup

APP = ['zippy_launcher.py']
DATA_FILES = [
    ('icons', ['debian/icons/zippy.icns']), 
]
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'debian/icons/zippy.icns',
    'packages': ['zippy'],
    'includes': ['zippy.cli'],
    'plist': {
        'CFBundleName': 'Zippy',
        'CFBundleDisplayName': 'Zippy Toolkit',
        'CFBundleIdentifier': 'no.on1.zippy',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHumanReadableCopyright': '© 2025 John Hauger Mitander',
    }
}

setup(
    name='Zippy',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
