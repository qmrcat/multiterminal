# main.py
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer

# Assegura que podem importar els mòduls del directori actual
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config # Per accedir a ORGANIZATION_NAME, APPLICATION_NAME
from main_window import MainWindow

import signal

# Opció 1: Importar tota la funció
from main_window import get_layouts_dir

# Afegeix aquesta funció a main.py just abans de la funció main()
def ensure_default_layout():
    """
    Assegura que hi ha un layout per defecte disponible a la carpeta de layouts.
    """
    # from main_window import get_layouts_dir
    import json
    import os
    
    layouts_dir = get_layouts_dir()
    default_layout_path = os.path.join(layouts_dir, "default_layout.json")
    
    # Si ja existeix un layout per defecte, no fem res
    if os.path.exists(default_layout_path):
        return
    
    # Creem un layout per defecte senzill
    default_layout = {
        "terminals": [
            {
                "name": "Terminal 1",
                "shell": "cmd.exe",
                "encoding": "utf-8",
                "working_directory": os.path.expanduser("~"),
                "startup_commands": []
            }
        ]
    }
    
    # Guardem el layout per defecte
    try:
        with open(default_layout_path, 'w', encoding='utf-8') as f:
            json.dump(default_layout, f, indent=4)
        print(f"Layout per defecte creat a: {default_layout_path}")
    except Exception as e:
        print(f"Error en crear el layout per defecte: {e}")


def main():

       
    # Assegurem que hi ha un layout per defecte
    ensure_default_layout()
    
    # Ignora la senyal Ctrl+C a nivell d'aplicació
    signal.signal(signal.SIGINT, signal.SIG_IGN)


    # Configura l'aplicació Qt
    # Habilita High DPI scaling si és necessari
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Estableix els noms per a QSettings
    app.setOrganizationName(config.ORGANIZATION_NAME)
    app.setApplicationName(config.APPLICATION_NAME)

    # Crea i mostra la finestra principal
    main_win = MainWindow()
    main_win.show()

    # Executa el bucle d'events de l'aplicació
    # sys.exit(app.exec_()) # Forma estàndard

    # Alternativa per a millor gestió d'excepcions Python
    try:
        status = app.exec_()
        print(f"Surtint amb estat: {status}")
        sys.exit(status)
    except Exception as e:
        print(f"Error no capturat en el bucle principal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()