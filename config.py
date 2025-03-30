# config.py
import os
#from PyQt5.QtGui import QFontDatabase

# --- Noms per a QSettings ---
ORGANIZATION_NAME = "QMRCAT" # Canvia això!
APPLICATION_NAME = "MultiTerminal"

# --- Valors per defecte ---
_default_font_family_cache = None # Per guardar el resultat i no calcular-ho cada cop

def get_default_font_family():
    """
    Obté un nom de font monoespaiada per defecte adequat ('Consolas' o 'Courier New').
    Només accedeix a QFontDatabase quan es crida per primer cop.
    """
    global _default_font_family_cache
    if _default_font_family_cache is None:
        # Importa les classes de Qt aquí dins per assegurar que QApplication existeix
        # i evitar problemes d'importació circular primerenca.
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QFontDatabase

        # Comprova si QApplication ja s'ha inicialitzat (hauria de ser així quan es cridi)
        if QApplication.instance() is None:
            print("Advertència: QApplication no inicialitzada en obtenir la font per defecte. Usant 'Courier New'.")
            # Retorna un valor segur si QApplication encara no existeix
            # Això no hauria de passar en l'ús normal dins de l'aplicació ja iniciada.
            _default_font_family_cache = "Courier New"
        else:
            # Ara és segur accedir a QFontDatabase
            db = QFontDatabase()
            if "Consolas" in db.families():
                _default_font_family_cache = "Consolas"
            else:
                _default_font_family_cache = "Courier New"
            print(f"Font per defecte detectada: {_default_font_family_cache}") # Missatge de depuració
    return _default_font_family_cache

# En lloc d'assignar el resultat directament, assignem la *funció*
# Qui necessiti el valor haurà de cridar config.DEFAULT_FONT_FAMILY()
DEFAULT_FONT_FAMILY = get_default_font_family
# DEFAULT_FONT_FAMILY = "Consolas" if "Consolas" in QFontDatabase().families() else "Courier New"
DEFAULT_FONT_SIZE = 10
DEFAULT_BG_COLOR = "#1E1E1E" # Fosc
DEFAULT_FG_COLOR = "#D4D4D4" # Clar
DEFAULT_CURSOR_COLOR = "#A0A0A0"
DEFAULT_PROMPT_TIMEOUT = 150 # ms per esperar el prompt després de la sortida
DEFAULT_SHELL = "cmd.exe"
# DEFAULT_ENCODING = "cp850" # Codificació comuna per a CMD en moltes regions
                            # Pots provar 'utf-8' o locale.getpreferredencoding(False)
DEFAULT_ENCODING = "utf-8" # Millor punt de partida per a eines modernes

# --- Claus per a QSettings ---
SETTINGS_GEOMETRY = "window/geometry"
SETTINGS_STATE = "window/state"
SETTINGS_FONT_FAMILY = "appearance/fontFamily"
SETTINGS_FONT_SIZE = "appearance/fontSize"
SETTINGS_BG_COLOR = "appearance/bgColor"
SETTINGS_FG_COLOR = "appearance/fgColor"
SETTINGS_CURSOR_COLOR = "appearance/cursorColor"
SETTINGS_THEME = "appearance/theme" # Nom del tema (ex: "dark", "light")
SETTINGS_PROMPT_TIMEOUT = "terminal/promptTimeout"
SETTINGS_SHELL_PATH = "terminal/shellPath"
SETTINGS_ENCODING = "terminal/encoding"
SETTINGS_LAST_LAYOUT = "layout/lastUsed" # Opcional: per carregar l'últim layout

# --- Altres ---
DEFAULT_LAYOUT_FILENAME = "default_layout.json"
THEMES_DIR = os.path.join(os.path.dirname(__file__), "themes")