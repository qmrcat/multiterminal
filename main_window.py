# main_window.py
import sys
import os
import json
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QAction, QMenuBar, QFileDialog,
                             QMessageBox, QLineEdit, QApplication, QLabel,
                             QInputDialog)
# from PyQt5.QtCore import Qt, QSettings, QSize, QPoint, pyqtSignal, QByteArray
# from PyQt5.QtGui import QFont, QColor, QIcon # Afegir QIcon

# Afegeix QProcess aquí:
from PyQt5.QtCore import Qt, QSettings, QSize, QPoint, pyqtSignal, QByteArray, QProcess, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette

import config
from terminal_widget import TerminalWidget
from command_line_edit import CommandLineEdit
from settings_dialog import SettingsDialog
from process_viewer_dialog import ProcessViewerDialog

# Importa la funció d'ajuda si la vas posar a utils.py o config.py
try:
    # Intenta importar des d'utils.py primer (si existeix)
    from utils import resource_path
except ImportError:
    try:
        # Si no, intenta des de config.py
        from config import resource_path
    except ImportError:
        # Fallback o avís si no es troba enlloc
        print("Advertència: Funció resource_path no trobada. La creació d'executables pot fallar.")
        # Defineix una funció bàsica com a fallback per a desenvolupament
        def resource_path(relative_path):
            return os.path.join(os.path.abspath("."), relative_path)
        


def get_layouts_dir():
    """
    Obté el directori on guardar els layouts.
    Utilitza AppData a Windows o .config a Linux.
    """
    if sys.platform == "win32":
        # A Windows, utilitzem AppData/Roaming
        app_data = os.environ.get('APPDATA')
        if app_data:
            layouts_dir = os.path.join(app_data, "MultiTerminal", "layouts")
        else:
            # Fallback a una carpeta local
            layouts_dir = os.path.join(os.path.expanduser("~"), "MultiTerminal", "layouts")
    else:
        # A Unix/Linux/Mac, utilitzem ~/.config/
        layouts_dir = os.path.join(os.path.expanduser("~"), ".config", "MultiTerminal", "layouts")
    
    # Assegurem que la carpeta existeix
    os.makedirs(layouts_dir, exist_ok=True)
    print(f"Directori de layouts: {layouts_dir}")
    return layouts_dir

# Afegeix aquesta variable global a la classe MainWindow
def __init__(self, parent=None):
    super().__init__(parent)
    self.settings = QSettings(config.ORGANIZATION_NAME, config.APPLICATION_NAME)
    self.current_layout_file = None
    
    # Directori per layouts
    self.layouts_dir = get_layouts_dir()
    
    # ... resta del codi ...

# Modifica la funció prompt_save_layout
def prompt_save_layout(self, save_as=False):
    """Demana a l'usuari on guardar el layout actual."""
    filename = self.current_layout_file
    if save_as or not filename:
        # Utilitza el directori de layouts com a punt de partida
        initial_dir = self.layouts_dir
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Layout", 
                                                initial_dir, 
                                                "Layouts JSON (*.json);;Tots els fitxers (*)")
        if not filename:
            return # Cancel·lat per l'usuari
        if not filename.lower().endswith('.json'):
            filename += '.json' # Assegura l'extensió

    self.save_layout(filename)

# Modifica la funció prompt_load_layout
def prompt_load_layout(self):
    """Demana a l'usuari quin layout carregar."""
    # Utilitza el directori de layouts com a punt de partida
    initial_dir = self.layouts_dir
    filename, _ = QFileDialog.getOpenFileName(self, "Carregar Layout", 
                                             initial_dir, 
                                             "Layouts JSON (*.json);;Tots els fitxers (*)")
    if filename:
        self.load_layout(filename)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings(config.ORGANIZATION_NAME, config.APPLICATION_NAME)
        self.current_layout_file = None # Per saber quin layout està carregat

        self._terminal_widgets = {} # Diccionari per accedir als TerminalWidget per índex de pestanya

        # Inicialitza el directori de layouts
        self.layouts_dir = get_layouts_dir()

        self.setWindowTitle(config.APPLICATION_NAME)
        # self.setWindowIcon(QIcon("path/to/your/icon.png")) # Descomentar i posar icona

        self._setup_ui()
        self._create_actions()
        self._create_menus()
        self._connect_signals()

        self.load_app_settings() # Carrega geometria, estat i tema
        self.apply_current_theme() # Aplica el tema carregat

        # Carrega l'últim layout si està configurat o un terminal per defecte
        last_layout = self.settings.value(config.SETTINGS_LAST_LAYOUT)
        if last_layout and os.path.exists(last_layout):
             print(f"Carregant l'últim layout: {last_layout}")
             self.load_layout(last_layout)
        else:
             print("Creant un terminal inicial per defecte.")
             self.add_new_terminal() # Afegeix un terminal si no hi ha layout

        # Aplica la configuració als terminals existents (després de carregar layout o crear el primer)
        self._apply_terminal_settings_to_all()
        print(f"MainWindow inicialitzat amb layouts_dir = {self.layouts_dir}")


    def _setup_ui(self):
        """Configura la interfície d'usuari principal."""
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # Sense marges exteriors

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True) # Permet reordenar pestanyes

        main_layout.addWidget(self.tab_widget)

        # Status bar (opcional)
        self.statusBar().showMessage("A punt")

    def _create_actions(self):
        """Crea les accions per als menús i barres d'eines."""
        # --- File ---
        # self.new_tab_action = QAction(QIcon.fromTheme("document-new", QIcon("")), "&Nou Terminal", self, shortcut="Ctrl+T", triggered=self.add_new_terminal)
        self.new_tab_action = QAction(QIcon.fromTheme("document-new", QIcon("")), "&Nou Terminal", self, shortcut="Ctrl+T", triggered=lambda: self.add_new_terminal())

        # self.load_layout_action = QAction(QIcon.fromTheme("document-open", QIcon("")), "Carre&gar Layout...", self, shortcut="Ctrl+L", triggered=self.prompt_load_layout)
        # self.save_layout_action = QAction(QIcon.fromTheme("document-save", QIcon("")), "&Guardar Layout", self, shortcut="Ctrl+S", triggered=self.prompt_save_layout)
        # self.save_layout_as_action = QAction(QIcon.fromTheme("document-save-as", QIcon("")), "Guardar Layout &Com...", self, shortcut="Ctrl+Shift+S", triggered=lambda: self.prompt_save_layout(save_as=True))
        # self.settings_action = QAction(QIcon.fromTheme("preferences-system", QIcon("")), "&Configuració...", self, triggered=self.open_settings_dialog)
        # self.exit_action = QAction(QIcon.fromTheme("application-exit", QIcon("")), "&Sortir", self, shortcut="Ctrl+Q", triggered=self.close)
        self.load_layout_action = QAction(QIcon.fromTheme("document-open", QIcon("")), "Carre&gar Layout...", self, shortcut="Ctrl+L", triggered=self.prompt_load_layout)
        self.save_layout_action = QAction(QIcon.fromTheme("document-save", QIcon("")), "&Guardar Layout", self, shortcut="Ctrl+S", triggered=self.prompt_save_layout)
        self.save_layout_as_action = QAction(QIcon.fromTheme("document-save-as", QIcon("")), "Guardar Layout &Com...", self, shortcut="Ctrl+Shift+S", triggered=lambda: self.prompt_save_layout(save_as=True))
        self.settings_action = QAction(QIcon.fromTheme("preferences-system", QIcon("")), "&Configuració...", self, triggered=self.open_settings_dialog)
        self.exit_action = QAction(QIcon.fromTheme("application-exit", QIcon("")), "&Sortir", self, shortcut="Ctrl+Q", triggered=self.close)
        # Accions específiques per a layouts
        self.open_layouts_folder_action = QAction("Obrir Carpeta de &Layouts - beta", self, triggered=self.open_layouts_folder)
        self.export_layout_action = QAction("E&xportar Layout... - beta", self, triggered=self.export_layout)
        self.import_layout_action = QAction("&Importar Layout... - beta", self, triggered=self.import_layout)        

        # --- Edit ---
        # Les accions de Copiar/Enganxar es gestionaran millor contextualment
        self.rename_tab_action = QAction("Canviar &Nom Pestanya...", self, triggered=self.rename_current_tab)

        # --- View ---
        # Nova acció per veure processos
        self.view_processes_action = QAction(QIcon.fromTheme("system-search", QIcon("")), "&Veure Processos...", self, triggered=self.show_process_viewer)

        # --- Help ---
        self.about_action = QAction("&Quant a...", self, triggered=self.show_about_dialog)

    def _create_menus(self):
        """Crea la barra de menú."""
        menu_bar = self.menuBar()

        # --- File Menu ---
        file_menu = menu_bar.addMenu("&Fitxer")
        file_menu.addAction(self.new_tab_action)
        file_menu.addSeparator()

        # Submenu de layouts
        layouts_menu = file_menu.addMenu("&Layouts")        
        # file_menu.addAction(self.load_layout_action)
        # file_menu.addAction(self.save_layout_action)
        # file_menu.addAction(self.save_layout_as_action)
        layouts_menu.addAction(self.load_layout_action)
        layouts_menu.addAction(self.save_layout_action)
        layouts_menu.addAction(self.save_layout_as_action)
        layouts_menu.addSeparator()
        layouts_menu.addAction(self.open_layouts_folder_action)
        layouts_menu.addAction(self.export_layout_action)
        layouts_menu.addAction(self.import_layout_action)


        file_menu.addSeparator()
        file_menu.addAction(self.settings_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # --- Edit Menu ---
        edit_menu = menu_bar.addMenu("&Edita")
        edit_menu.addAction(self.rename_tab_action)
        # Podríem afegir accions per copiar/enganxar aquí, però normalment
        # QTextEdit ja té menús contextuals.

        # --- View Menu (opcional per a temes ràpids) ---
        # view_menu = menu_bar.addMenu("&Visualitza")

        # --- View Menu (afegim o modifiquem per incloure el visor de processos) ---
        view_menu = menu_bar.addMenu("&Visualitza")
        view_menu.addAction(self.view_processes_action)

        # --- Help Menu ---
        help_menu = menu_bar.addMenu("A&juda")
        help_menu.addAction(self.about_action)

    def _connect_signals(self):
        """Connecta senyals i slots."""
        self.tab_widget.tabCloseRequested.connect(self.close_terminal_tab)
        self.tab_widget.currentChanged.connect(self._update_active_terminal)

        # Doble clic a la pestanya per canviar el nom
        # self.tab_widget.tabBar().doubleClicked.connect(self.rename_current_tab)
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_current_tab) # Senyal correcte


    # --- Gestió de Terminals ---

    def add_new_terminal(self, name="Terminal", shell=None, encoding=None, startup_commands=None, working_dir=None):
        """Afegeix una nova pestanya amb un terminal."""
        index = self.tab_widget.count()

        # Utilitza la configuració global si no s'especifica res
        term_shell = shell or self.settings.value(config.SETTINGS_SHELL_PATH, config.DEFAULT_SHELL)
        term_encoding = encoding or self.settings.value(config.SETTINGS_ENCODING, config.DEFAULT_ENCODING)
        term_wd = working_dir or os.path.expanduser("~") # O un valor per defecte més intel·ligent?

        # Crea el widget del terminal
        terminal_widget = TerminalWidget(
            shell_path=term_shell,
            encoding=term_encoding,
            startup_commands=startup_commands,
            working_directory=term_wd,
            parent=self # Important per a la gestió de la memòria
        )

        # Crea l'entrada de comandes
        command_input = CommandLineEdit(self)

        # Connecta senyals del terminal i l'entrada
        command_input.execute_command.connect(terminal_widget.execute_command)
        command_input.interrupt_signal.connect(terminal_widget.send_interrupt)
        terminal_widget.prompt_available.connect(command_input.setFocus) # Focus a l'entrada quan el prompt està llest
        terminal_widget.process_finished.connect(lambda code, status, idx=index: self._handle_terminal_finished(idx, code, status))
        terminal_widget.title_changed.connect(lambda new_title, idx=index: self.tab_widget.setTabText(idx, new_title))

        # Aplica estils actuals al nou terminal
        self._apply_terminal_settings(terminal_widget, command_input)

        # Crea un contenidor per al terminal i l'entrada
        container = QWidget()
        term_layout = QVBoxLayout(container)
        term_layout.setContentsMargins(2, 2, 2, 2) # Petits marges interns
        term_layout.addWidget(terminal_widget)
        term_layout.addWidget(command_input)

        # Afegeix la pestanya
        tab_index = self.tab_widget.addTab(container, name)
        self.tab_widget.setCurrentIndex(tab_index)

        # Guarda referències
        self._terminal_widgets[tab_index] = {
            "widget": terminal_widget,
            "input": command_input,
            "container": container
        }

        # Forcem el focus a l'entrada de text
        command_input.setFocus()
        print(f"Terminal '{name}' afegit a l'índex {tab_index}")

        # Actualitza títol inicial (possiblement amb Git) després d'un moment
        # per donar temps a que el primer prompt aparegui
        QTimer.singleShot(config.DEFAULT_PROMPT_TIMEOUT + 200, terminal_widget._try_update_git_branch)


    def close_terminal_tab(self, index: int):
        """Tanca la pestanya i el terminal associat."""
        if index < 0 or index >= self.tab_widget.count():
            return

        print(f"Iniciant tancament de la pestanya índex {index}")

        term_data = self._terminal_widgets.pop(index, None)

        if term_data:
            widget = term_data.get("widget")
            container = term_data.get("container")

            if widget:
                print(f"Tancant el procés del terminal a l'índex {index}")
                widget.close_terminal() # Intenta tancar el procés subjacent

            # Elimina el widget contenidor de la pestanya
            # Important: Fer-ho abans d'eliminar els fills
            self.tab_widget.removeTab(index)
            print(f"Pestanya {index} eliminada del QTabWidget.")

            # Marca els widgets per ser eliminats més tard per Qt
            if container:
                 container.deleteLater()
                 print(f"Contenidor de la pestanya {index} marcat per eliminar.")
            # Els fills del contenidor (TerminalWidget, CommandLineEdit)
            # s'eliminaran automàticament quan s'elimini el contenidor.

            # Actualitzar els índexs al diccionari _terminal_widgets
            new_widgets = {}
            current_tab_count = self.tab_widget.count() # Recompte després d'eliminar
            original_keys = sorted(self._terminal_widgets.keys())

            for i in range(current_tab_count):
                 # Troba la clau original que correspon a la nova posició 'i'
                 # Això assumeix que QTabWidget manté l'ordre relatiu
                 original_key = -1
                 temp_idx = 0
                 for key in original_keys:
                      if key < index: # Claus abans de l'eliminada
                           if temp_idx == i:
                                original_key = key
                                break
                      elif key > index: # Claus després de l'eliminada
                           if temp_idx == i:
                                original_key = key
                                break
                      temp_idx += 1


                 if original_key != -1 and original_key in self._terminal_widgets:
                      new_widgets[i] = self._terminal_widgets[original_key]
                      # Opcionalment, actualitza les connexions que depenen de l'índex si n'hi ha
                      # lambda code, status, idx=i: self._handle_terminal_finished(idx, code, status)
                      # lambda new_title, idx=i: self.tab_widget.setTabText(idx, new_title)
                      # Això pot ser complex, potser és millor referenciar per objecte
                 else:
                      print(f"Advertència: No s'ha trobat la clau original per al nou índex {i} durant la reindexació.")


            self._terminal_widgets = new_widgets
            print(f"Diccionari de widgets actualitzat: {list(self._terminal_widgets.keys())}")


        else:
             # Si no estava al diccionari, igualment treu la pestanya
             print(f"Advertència: No s'ha trobat informació del widget per a l'índex {index}. Eliminant només la pestanya.")
             self.tab_widget.removeTab(index)

        # Si no queden pestanyes, opcionalment tanca l'aplicació o mostra un missatge
        if self.tab_widget.count() == 0:
            print("No queden pestanyes.")
            # self.close() # Descomenta per tancar l'app quan es tanca l'última pestanya


    # def _handle_terminal_finished(self, index: int, exit_code: int, exit_status: QProcess.ExitStatus):
    #     """Gestiona quan el procés d'un terminal finalitza inesperadament."""
    #     # Podríem canviar el títol de la pestanya per indicar que està tancat
    #     current_text = self.tab_widget.tabText(index)
    #     if not current_text.endswith(" (Tancat)"):
    #         self.tab_widget.setTabText(index, f"{current_text} (Tancat)")
    #     # Podríem desactivar l'entrada de comandes
    #     term_data = self._terminal_widgets.get(index)
    #     if term_data and term_data.get("input"):
    #          term_data["input"].setEnabled(False)
    #          term_data["input"].setPlaceholderText("Terminal tancat")
    def _handle_terminal_finished(self, index: int, exit_code: int, exit_status: QProcess.ExitStatus):
        """Gestiona quan el procés d'un terminal finalitza inesperadament."""
        # El codi aquí dins ara hauria de funcionar perquè QProcess està importat
        current_text = self.tab_widget.tabText(index)
        if "(Tancat)" not in current_text: # Evita afegir-ho múltiples vegades
            self.tab_widget.setTabText(index, f"{current_text} (Tancat)")

        term_data = self._terminal_widgets.get(index)
        if term_data and term_data.get("input"):
             term_data["input"].setEnabled(False)
             term_data["input"].setPlaceholderText("Terminal tancat")


    def _update_active_terminal(self, index: int):
        """Accions a fer quan canvia la pestanya activa."""
        if 0 <= index < self.tab_widget.count():
            term_data = self._terminal_widgets.get(index)
            if term_data and term_data.get("input"):
                 term_data["input"].setFocus() # Focus a l'entrada de la pestanya activa
                 # Actualitza l'estat (opcional)
                 # self.statusBar().showMessage(f"Terminal actiu: {self.tab_widget.tabText(index)}")
            else:
                 # Potser la pestanya s'està tancant o hi ha un error
                 self.statusBar().showMessage("A punt")

        else:
            self.statusBar().showMessage("A punt")

    def rename_current_tab(self, index=None):
        """Demana un nou nom per a la pestanya actual."""
        # current_index = self.tab_widget.currentIndex()
        # if current_index < 0:
        #     return

        # old_name = self.tab_widget.tabText(current_index)
        # new_name, ok = QInputDialog.getText(self, "Canviar Nom Pestanya", "Nou nom:", QLineEdit.Normal, old_name)
        current_index = -1
        if index is not None:
             # Si el senyal ens dóna l'índex, l'usem directament
             current_index = index
        else:
             # Si es crida des d'una acció de menú, agafem l'actual
             current_index = self.tab_widget.currentIndex()

        if current_index < 0:
            return

        old_name = self.tab_widget.tabText(current_index)
        # És útil mostrar l'índex o nom antic al diàleg? Potser no.
        new_name, ok = QInputDialog.getText(self, "Canviar Nom Pestanya", f"Nou nom per a '{old_name}':", QLineEdit.Normal, old_name)

        if ok and new_name:
            self.tab_widget.setTabText(current_index, new_name)
            # Si el TerminalWidget gestiona el títol (p.ex. amb Git),
            # hauríem de tenir una manera de dir-li que el nom base ha canviat.
            term_data = self._terminal_widgets.get(current_index)
            # if term_data and term_data.get("widget"):
                 # Passa el nou nom base al widget perquè l'utilitzi
                 # term_data["widget"].set_base_title(new_name) # Necessitaria implementar aquesta funció

    # --- Gestió de Layouts ---

    def prompt_save_layout(self, save_as=False):
        """Demana a l'usuari on guardar el layout actual."""
        filename = self.current_layout_file
        if save_as or not filename:
            filename, _ = QFileDialog.getSaveFileName(self, "Guardar Layout", "", "Layouts JSON (*.json);;Tots els fitxers (*)")
            if not filename:
                return # Cancel·lat per l'usuari
            if not filename.lower().endswith('.json'):
                filename += '.json' # Assegura l'extensió

        self.save_layout(filename)

    def save_layout(self, filename: str):
        """Guarda la configuració de les pestanyes actuals en un fitxer JSON."""
        layout_data = {"terminals": []}
        for index in range(self.tab_widget.count()):
            term_data = self._terminal_widgets.get(index)
            if term_data and term_data.get("widget"):
                widget = term_data["widget"]
                state = widget.get_state()
                # Afegeix el nom de la pestanya actual
                state["name"] = self.tab_widget.tabText(index)
                layout_data["terminals"].append(state)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, indent=4)
            self.statusBar().showMessage(f"Layout guardat a {os.path.basename(filename)}")
            self.current_layout_file = filename
            # Guarda el path de l'últim layout guardat/carregat
            self.settings.setValue(config.SETTINGS_LAST_LAYOUT, filename)
        except Exception as e:
            QMessageBox.critical(self, "Error Guardant Layout", f"No s'ha pogut guardar el layout:\n{e}")
            self.statusBar().showMessage("Error en guardar el layout")

    def prompt_load_layout(self):
        """Demana a l'usuari quin layout carregar."""
        filename, _ = QFileDialog.getOpenFileName(self, "Carregar Layout", "", "Layouts JSON (*.json);;Tots els fitxers (*)")
        if filename:
            self.load_layout(filename)

    def load_layout(self, filename: str):
        """Carrega un layout des d'un fitxer JSON, tancant els terminals actuals."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                layout_data = json.load(f)
        except FileNotFoundError:
            QMessageBox.warning(self, "Error Carregant Layout", f"El fitxer de layout no s'ha trobat:\n{filename}")
            self.settings.remove(config.SETTINGS_LAST_LAYOUT) # Esborra si no existeix
            return
        except Exception as e:
            QMessageBox.critical(self, "Error Carregant Layout", f"No s'ha pogut carregar o parsejar el layout:\n{e}")
            return

        # Tanca tots els terminals actuals abans de carregar
        print("Tancant terminals actuals per carregar layout...")
        # Iterem a la inversa per evitar problemes amb la reindexació durant el tancament
        for index in range(self.tab_widget.count() - 1, -1, -1):
             self.close_terminal_tab(index)

        # Crea els nous terminals des del layout
        print(f"Carregant {len(layout_data.get('terminals', []))} terminals del layout...")
        terminals_config = layout_data.get("terminals", [])
        if not terminals_config:
             print("Layout buit o invàlid, creant un terminal per defecte.")
             self.add_new_terminal()
        else:
             for term_config in terminals_config:
                 self.add_new_terminal(
                     name=term_config.get("name", "Terminal"),
                     shell=term_config.get("shell"), # Pot ser None, agafarà el global
                     encoding=term_config.get("encoding"), # Pot ser None
                     startup_commands=term_config.get("startup_commands"),
                     working_dir=term_config.get("working_directory")
                 )

        self.current_layout_file = filename
        self.statusBar().showMessage(f"Layout '{os.path.basename(filename)}' carregat")
        # Guarda com a últim layout carregat
        self.settings.setValue(config.SETTINGS_LAST_LAYOUT, filename)
        # Assegura que els nous terminals tinguin els estils correctes
        self._apply_terminal_settings_to_all()



    # Finalment, afegeix les noves funcions:
    def open_layouts_folder(self):
        """Obre l'explorador de fitxers a la carpeta de layouts."""
        import subprocess
        import os
        import sys  # Assegura't que sys estigui importat aquí també
        
        try:
            print(f"Intentant obrir la carpeta: {self.layouts_dir}")
        
            if not hasattr(self, 'layouts_dir') or not self.layouts_dir:
                # Si per alguna raó no existeix l'atribut, el recreem
                self.layouts_dir = get_layouts_dir()

            print(f"Directori a obrir: {self.layouts_dir}")

            if sys.platform == "win32":
                os.startfile(self.layouts_dir)
            elif sys.platform == "win64":
                os.startfile(self.layouts_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.layouts_dir], check=True)
            else:
                subprocess.run(["xdg-open", self.layouts_dir], check=True)

            print(f"Carpeta oberta: {self.layouts_dir}")

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"No s'ha pogut obrir la carpeta de layouts: {str(e)}")
            print(f"Error en obrir carpeta: {e}")


    def export_layout(self):
        """Exporta el layout actual a una ubicació seleccionada per l'usuari."""
        if not self.current_layout_file:
            QMessageBox.information(self, "Informació", "Cal guardar el layout actual abans d'exportar-lo.")
            return
        
        export_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Layout", 
            os.path.expanduser("~"), 
            "Layouts JSON (*.json);;Tots els fitxers (*)"
        )
        
        if not export_path:
            return
        
        if not export_path.lower().endswith('.json'):
            export_path += '.json'
        
        try:
            import shutil
            shutil.copy2(self.current_layout_file, export_path)
            QMessageBox.information(self, "Èxit", f"Layout exportat a:\n{export_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No s'ha pogut exportar el layout: {e}")

    def import_layout(self):
        """Importa un layout d'una ubicació externa a la carpeta de layouts."""
        import_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Layout", 
            os.path.expanduser("~"), 
            "Layouts JSON (*.json);;Tots els fitxers (*)"
        )
        
        if not import_path:
            return
        
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                layout_data = json.load(f)
            
            # Validem que sigui un layout vàlid
            if "terminals" not in layout_data:
                raise ValueError("El fitxer no sembla ser un layout vàlid")
            
            # Demanem un nom per al layout importat
            from PyQt5.QtWidgets import QInputDialog
            import os
            
            base_name = os.path.basename(import_path)
            layout_name, ok = QInputDialog.getText(
                self, "Nom del Layout", 
                "Nom per al layout importat:",
                text=base_name
            )
            
            if not ok or not layout_name:
                return
            
            if not layout_name.lower().endswith('.json'):
                layout_name += '.json'
            
            # Guardem el layout a la carpeta de layouts
            target_path = os.path.join(self.layouts_dir, layout_name)
            
            # Comprovem si ja existeix
            if os.path.exists(target_path):
                reply = QMessageBox.question(
                    self, 
                    "Confirmar Sobreescriptura",
                    f"El fitxer '{layout_name}' ja existeix. Vols sobreescriure'l?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
            
            import shutil
            shutil.copy2(import_path, target_path)
            
            QMessageBox.information(
                self, 
                "Èxit", 
                f"Layout '{layout_name}' importat correctament.\n\nPots carregar-lo des del menú Fitxer > Carregar Layout."
            )
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No s'ha pogut importar el layout: {e}")

    # Finalment, afegeix el mètode per mostrar el diàleg de processos
    def show_process_viewer(self):
        """Mostra el diàleg per veure els processos en execució als terminals."""
        # Preparem la informació dels terminals per passar-la al diàleg
        terminals_data = {}
        for idx, term_data in self._terminal_widgets.items():
            if term_data.get("widget") and term_data.get("widget")._process:
                terminals_data[idx] = term_data
        
        if not terminals_data:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Sense Terminals Actius", "No hi ha terminals actius per mostrar.")
            return
        
        # Creem i mostrem el diàleg
        dialog = ProcessViewerDialog(terminals_data, self)
        dialog.exec_()

    # --- Gestió de Configuració i Temes ---

    def open_settings_dialog(self):
        """Obre el diàleg de configuració."""
        dialog = SettingsDialog(self)
        dialog.settings_applied.connect(self._apply_app_settings) # Connecta el senyal
        dialog.exec_() # Mostra el diàleg modalment

    def _apply_app_settings(self):
        """Aplica la configuració global a l'aplicació i als terminals."""
        print("Aplicant configuració...")
        self.apply_current_theme()
        self._apply_terminal_settings_to_all()
        self.statusBar().showMessage("Configuració aplicada.")

    def _apply_terminal_settings_to_all(self):
        """Aplica la configuració de font, color, etc., a tots els terminals oberts."""
        font = QFont(
            # self.settings.value(config.SETTINGS_FONT_FAMILY, config.DEFAULT_FONT_FAMILY),
            # int(self.settings.value(config.SETTINGS_FONT_SIZE, config.DEFAULT_FONT_SIZE))
            self.settings.value(config.SETTINGS_FONT_FAMILY, config.DEFAULT_FONT_FAMILY()), # Afegit ()
            int(self.settings.value(config.SETTINGS_FONT_SIZE, config.DEFAULT_FONT_SIZE))
        )
        bg_color = QColor(self.settings.value(config.SETTINGS_BG_COLOR, config.DEFAULT_BG_COLOR))
        fg_color = QColor(self.settings.value(config.SETTINGS_FG_COLOR, config.DEFAULT_FG_COLOR))
        # cursor_color = QColor(self.settings.value(config.SETTINGS_CURSOR_COLOR, config.DEFAULT_CURSOR_COLOR)) # Encara no utilitzat directament

        for index in range(self.tab_widget.count()):
             term_data = self._terminal_widgets.get(index)
             if term_data:
                 self._apply_terminal_settings(
                     term_data.get("widget"),
                     term_data.get("input"),
                     font, bg_color, fg_color # Passa els valors carregats
                 )

    def _apply_terminal_settings(self, terminal_widget, command_input, font=None, bg_color=None, fg_color=None):
        """Aplica configuració específica a un TerminalWidget i el seu CommandLineEdit."""
        if not terminal_widget or not command_input:
            return
        # Obtenir valors de la configuració si no es passen explícitament
        if font is None:
            font = QFont(
               #  self.settings.value(config.SETTINGS_FONT_FAMILY, config.DEFAULT_FONT_FAMILY),
               #  int(self.settings.value(config.SETTINGS_FONT_SIZE, config.DEFAULT_FONT_SIZE))
               self.settings.value(config.SETTINGS_FONT_FAMILY, config.DEFAULT_FONT_FAMILY()), # Afegit ()
               int(self.settings.value(config.SETTINGS_FONT_SIZE, config.DEFAULT_FONT_SIZE))
            )
        if bg_color is None:
            bg_color = QColor(self.settings.value(config.SETTINGS_BG_COLOR, config.DEFAULT_BG_COLOR))
        if fg_color is None:
            fg_color = QColor(self.settings.value(config.SETTINGS_FG_COLOR, config.DEFAULT_FG_COLOR))
        # cursor_color = QColor(self.settings.value(config.SETTINGS_CURSOR_COLOR, config.DEFAULT_CURSOR_COLOR))
        # Aplica al TerminalWidget (QTextEdit intern)
        terminal_widget.apply_styles(font, bg_color, fg_color) # Passa None per cursor_color de moment
        # Aplica al CommandLineEdit
        command_input.setFont(font)
        palette = command_input.palette()

        # --- Text: Forcem un color brillant per a la barra de comandes ---
        # Si el fons general (bg_color) és fosc, usem un color molt clar.
        # Si el fons general és clar, usem un color fosc.
        # (Fem servir la lluminositat del color base del terminal per decidir)
        if bg_color.lightnessF() < 0.5:
            command_fg = QColor("#F0F0F0") # Gris molt clar (quasi blanc)
        else:
            command_fg = QColor("#101010") # Negre (o gris fosc)

        palette.setColor(QPalette.Text, command_fg)
    

        # # Fons una mica diferent per distingir? O el mateix?
        # palette.setColor(QPalette.Base, bg_color.lighter(110)) # Una mica més clar
        # palette.setColor(QPalette.Text, fg_color)
        # command_input.setPalette(palette)

        # ------------------------------------------------------------------

        # Opcional: Millorar el contrast de la selecció de text també
        if bg_color.lightnessF() < 0.5:
            palette.setColor(QPalette.Highlight, QColor("#264F78")) # Blau fosc per selecció (sobre fons clar)
            palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF")) # Text blanc sobre selecció
        else:
            palette.setColor(QPalette.Highlight, QColor(Qt.darkBlue)) # Blau estàndard
            palette.setColor(QPalette.HighlightedText, QColor(Qt.white)) # Text blanc

        command_input.setPalette(palette)


    def apply_current_theme(self):
        """Aplica el tema seleccionat (utilitzant QSS)."""
        theme_name = self.settings.value(config.SETTINGS_THEME, "default")
        qss_file = os.path.join(config.THEMES_DIR, f"{theme_name}.qss")

        default_qss = """
            /* Estils base per assegurar consistència */
            QWidget { /* Potser massa general, ajustar si cal */
                /* color: #D4D4D4; */ /* Color de text per defecte */
                /* background-color: #2A2A2A; */ /* Fons per defecte */
            }
            QTabWidget::pane {
                border-top: 1px solid #444;
                /* background: #2A2A2A; */
            }
            QTabBar::tab {
                background: #333;
                color: #AAA;
                border: 1px solid #444;
                border-bottom: none; /* Solid border on top pane */
                padding: 5px 10px;
                margin-right: 1px;
            }
            QTabBar::tab:selected {
                background: #444; /* O el color base del terminal */
                color: #FFF;
                border-bottom: 1px solid #444; /* Match pane border */
            }
            QTabBar::tab:!selected:hover {
                background: #555;
            }
            QStatusBar {
                background: #333;
                color: #AAA;
            }
            QMenuBar {
                 background-color: #333;
                 color: #AAA;
            }
            QMenuBar::item {
                 background-color: #333;
                 color: #AAA;
                 padding: 4px 8px;
            }
            QMenuBar::item:selected { /* Quan el ratolí passa per sobre */
                 background-color: #555;
                 color: #FFF;
            }
            QMenu {
                background-color: #3C3C3C; /* Fons del menú desplegable */
                color: #D4D4D4;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #555; /* Element seleccionat al menú */
                 color: #FFF;
            }
            QLineEdit {
                 border: 1px solid #555;
                 padding: 2px;
                 /* Els colors es defineixen per paleta normalment */
            }
            QTextEdit {
                 border: none; /* El terminal no necessita vores */
                 /* Els colors es defineixen per paleta */
            }
            QPushButton {
                 background-color: #555;
                 color: #DDD;
                 border: 1px solid #666;
                 padding: 5px 15px;
                 min-width: 60px;
            }
            QPushButton:hover {
                 background-color: #666;
                 border-color: #777;
            }
            QPushButton:pressed {
                 background-color: #4A4A4A;
            }
        """

        qss = default_qss
        if os.path.exists(qss_file):
            print(f"Carregant tema des de: {qss_file}")
            try:
                with open(qss_file, 'r', encoding='utf-8') as f:
                    qss += f.read() # Afegeix els estils específics del tema
            except Exception as e:
                print(f"Error en llegir el fitxer de tema QSS: {e}")
                QMessageBox.warning(self, "Error de Tema", f"No s'ha pogut llegir el fitxer de tema:\n{qss_file}\n{e}")
        else:
            print(f"Fitxer de tema no trobat: {qss_file}. Utilitzant estils base.")
            if theme_name != "default":
                 QMessageBox.warning(self, "Tema no Trobat", f"El fitxer de tema '{theme_name}.qss' no s'ha trobat a la carpeta 'themes'.")


        self.setStyleSheet(qss)
        # Important: Tornar a aplicar els colors de la paleta als widgets
        # que els gestionen directament (com QTextEdit, QLineEdit)
        # perquè QSS pot sobreescriure la paleta per a certs estats.
        self._apply_terminal_settings_to_all()


    # --- Gestió de la Finestra ---

    def load_app_settings(self):
        """Carrega la geometria i estat de la finestra."""
        # Geometria (mida i posició)
        geometry = self.settings.value(config.SETTINGS_GEOMETRY)
        if geometry and isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        else:
            self.resize(1000, 700) # Mida per defecte si no hi ha res guardat
            self.move(QApplication.desktop().screen().rect().center() - self.rect().center()) # Centra

        # Estat (barres d'eines, docks - si n'hi hagués)
        state = self.settings.value(config.SETTINGS_STATE)
        if state and isinstance(state, QByteArray):
             self.restoreState(state)

        # Altres configuracions globals (com el tema) es carreguen
        # i s'apliquen on calgui (p.ex., a _apply_app_settings o apply_current_theme)

    def save_app_settings(self):
        """Guarda la geometria i estat de la finestra."""
        self.settings.setValue(config.SETTINGS_GEOMETRY, self.saveGeometry())
        self.settings.setValue(config.SETTINGS_STATE, self.saveState())
        print("Geometria i estat de la finestra guardats.")

    def closeEvent(self, event):
        """Gestiona l'event de tancament de la finestra."""
        print("Iniciant tancament de l'aplicació...")
        self.save_app_settings() # Guarda mida/posició finestra

        # Tanca tots els terminals de manera controlada
        # Iterem directament sobre els widgets gestionats per evitar problemes
        # si close_terminal_tab modifica la llista mentre iterem
        widgets_to_close = list(self._terminal_widgets.values())
        for term_data in widgets_to_close:
             widget = term_data.get("widget")
             if widget:
                 print(f"Tancant terminal durant el tancament de l'aplicació...")
                 widget.close_terminal()

        # Assegura que QSettings es guarda al disc
        self.settings.sync()
        print("Tancament completat.")
        event.accept() # Accepta el tancament

    # --- Diàlegs ---

    def show_about_dialog(self):
        """Mostra un diàleg simple 'Quant a...'."""
        QMessageBox.about(self, "Quant a MultiTerminal",
                          f"<b>{config.APPLICATION_NAME}</b><br>"
                          "Un gestor de múltiples terminals CMD.<br><br>"
                          "Desenvolupat amb Python i PyQt5.<br>"
                          "Versio 0.9.2<br>"
                          "(c) 2024 QMR") # Canvia això