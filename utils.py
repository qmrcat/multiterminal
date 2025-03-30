# utils.py
import sys
import os

def resource_path(relative_path):
    """
    Obté el camí absolut als recursos, funciona tant en mode de
    desenvolupament com quan s'executa des d'un executable de PyInstaller.
    """
    try:
        # PyInstaller crea una carpeta temporal i emmagatzema la ruta
        # base en l'atribut _MEIPASS del mòdul sys.
        # Aquesta és la carpeta on s'extreuen tots els fitxers empaquetats.
        base_path = sys._MEIPASS
    except AttributeError:
        # Si l'atribut _MEIPASS no existeix, significa que no estem
        # executant des d'un bundle de PyInstaller (mode desenvolupament).
        # En aquest cas, el camí base és el directori on es troba
        # el script principal o el directori actual de treball.
        # Utilitzar os.path.abspath(".") sol ser segur si executes
        # el main.py des de l'arrel del projecte.
        # Si executes des d'un altre lloc, potser necessites ajustar-ho
        # (p.ex., basant-te en __file__ d'algun mòdul principal).
        base_path = os.path.abspath(".")

    # Combina el camí base amb el camí relatiu del recurs
    path_to_resource = os.path.join(base_path, relative_path)

    # Línia de depuració (pots comentar-la un cop funcioni)
    # print(f"[resource_path] Requested: '{relative_path}', Base: '{base_path}', Result: '{path_to_resource}'")

    return path_to_resource

# Pots afegir altres funcions d'utilitat aquí si cal en el futur.