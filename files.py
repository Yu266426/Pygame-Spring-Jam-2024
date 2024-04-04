import os
import pathlib
import sys

CURRENT_DIR = pathlib.Path(os.path.dirname(os.path.realpath(sys.argv[0])))
ASSET_DIR = CURRENT_DIR / "assets"
FONTS_DIR = ASSET_DIR / "fonts"

FONT_PATH = str(FONTS_DIR / "Raleway-Bold.ttf")
# FONT_PATH = str(FONTS_DIR / "good times rg.otf")
