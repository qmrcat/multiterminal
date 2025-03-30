# terminal_widget.py
import re
import os
import locale # Per obtenir l'encoding preferit del sistema com a fallback
import time
import sys      # Necessari per comprovar la plataforma
import subprocess
# import subprocess # Necessari per executar taskkill
import ctypes   # Necessari per cridar l'API de Windows
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtGui import QFont, QColor, QTextCursor, QPalette
from PyQt5.QtCore import Qt, QProcess, pyqtSignal, QTimer, QByteArray

# Importa el convertidor ANSI
from ansi2html import Ansi2HTMLConverter

import config # Importa la configuració

CREATE_NEW_PROCESS_GROUP = 0x00000200

import ctypes # Ja hauria d'estar per GenerateConsoleCtrlEvent
# ... altres imports ...

# Constant de Windows per crear un nou grup de processos
CREATE_NEW_PROCESS_GROUP = 0x00000200

# Funció que s'executarà per modificar els arguments de creació del procés
def modify_startup_info(startupinfo):
    """Afegeix el flag CREATE_NEW_PROCESS_GROUP a l'estructura STARTUPINFO."""
    try:
         # Modifiquem dwFlags de l'objecte STARTUPINFOW que QProcess ens passa
         startupinfo.dwFlags |= CREATE_NEW_PROCESS_GROUP
         print(f"[modify_startup_info] Afegit flag CREATE_NEW_PROCESS_GROUP. Nou dwFlags: {startupinfo.dwFlags:#0x}")
    except AttributeError as e:
         print(f"[modify_startup_info] Error en accedir a startupinfo.dwFlags: {e}. Potser l'estructura no és l'esperada.")
    # No cal retornar res, modifiquem l'objecte in-place.


class TerminalWidget(QWidget):
    """
    Widget que conté un QTextEdit per a la sortida i gestiona un QProcess (cmd.exe).
    """
    

    process_finished = pyqtSignal(int, QProcess.ExitStatus) # exitCode, exitStatus
    title_changed = pyqtSignal(str) # Per canviar el títol de la pestanya
    prompt_available = pyqtSignal() # Indica que el prompt està llest

    def __init__(self, shell_path=config.DEFAULT_SHELL, encoding=config.DEFAULT_ENCODING, startup_commands=None, working_directory=None, parent=None):
        super().__init__(parent)
        self._shell_path = shell_path
        # self._encoding = encoding
        # Utilitza l'encoding passat, o el de config, o el del sistema com a últim recurs
        self._encoding = encoding or config.DEFAULT_ENCODING or locale.getpreferredencoding(False)
        self._startup_commands = startup_commands or []
        self._working_directory = working_directory or os.path.expanduser("~") # Directori d'inici

        self._process = QProcess(self)
        self._output_buffer = "" # Buffer per a sortida parcial
        self._prompt_detected = False
        self._command_queue = list(self._startup_commands) # Cua per comandes inicials/automàtiques

        # Timer per detectar el prompt amb un petit retard
        self._prompt_timer = QTimer(self)
        self._prompt_timer.setSingleShot(True)
        # self._prompt_timer.setInterval(config.DEFAULT_PROMPT_TIMEOUT)
        # Augmentem lleugerament el timeout per donar marge a chcp
        self._prompt_timer.setInterval(config.DEFAULT_PROMPT_TIMEOUT + 50)        
        self._prompt_timer.timeout.connect(self._check_prompt_and_run_next)

        
        # --- Convertidor ANSI ---
        self._ansi_converter = Ansi2HTMLConverter(inline=True) # inline=True és útil


        # --- UI ---
        self._output_view = QTextEdit(self)
        self._output_view.setReadOnly(True)
        # Permet selecció de text
        self._output_view.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Sense marges interns
        layout.addWidget(self._output_view)
        self.setLayout(layout)

        self._setup_process()
        self.apply_styles() # Aplica estils inicials

    def _setup_process(self):
        """Configura i inicia el procés del shell amb un grup de processos separat."""
        self._process.setProcessChannelMode(QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._handle_output)
        self._process.finished.connect(self._handle_finished)
        self._process.errorOccurred.connect(self._handle_error)


        # --- MODIFICACIÓ: Comprovem si el mètode existeix abans d'utilitzar-lo ---
        try:
            # Intentem configurar el modificador només si existeix el mètode
            if hasattr(self._process, 'setCreateProcessArgumentsModifier'):
                print("Configurant modificador per afegir CREATE_NEW_PROCESS_GROUP...")
                self._process.setCreateProcessArgumentsModifier(modify_startup_info)
            else:
                print("Advertència: El mètode 'setCreateProcessArgumentsModifier' no està disponible en aquesta versió de PyQt5.")
                # El procés es crearà sense el flag CREATE_NEW_PROCESS_GROUP
        except Exception as e:
            print(f"Error en configurar els arguments del procés: {e}")
        # --- FI DE LA MODIFICACIÓ ---

        # ... (codi per gestionar _working_directory) ...
        if self._working_directory and os.path.isdir(self._working_directory):
             self._process.setWorkingDirectory(self._working_directory)
        else:
             # ... (missatge d'advertència i directori per defecte) ...
             self._working_directory = self._process.workingDirectory()

        print(f"Iniciant procés: {self._shell_path} a {self._working_directory}")
        # ... (missatge sobre chcp) ...

        # Forçar UTF-8 i prompt estàndard
        startup_cmd_args = ['/K', 'chcp 65001 > nul && @PROMPT $P$G']
        print(f"Executant: {self._shell_path} amb arguments: {startup_cmd_args}")
        self._process.start(self._shell_path, startup_cmd_args)

        # Opcional: Netejar el modificador després de start (probablement no necessari)
        # self._process.setCreateProcessArgumentsModifier(None)

        self._process.waitForStarted(1500)

        if self._process.state() == QProcess.Running:
            print(f"Procés iniciat (PID: {self._process.processId()}) amb el seu propi grup de processos.")
            # ...
        else:
            # ... (gestió d'error d'inici) ...
            error_msg = f"Error en iniciar el procés: {self._shell_path}\nError: {self._process.errorString()}"
            print(error_msg)
            # Mostra error a la UI...

    def _decode_bytes(self, byte_array: QByteArray) -> str:
        """Intenta decodificar bytes, prioritzant UTF-8."""
        try:
            # 1. Intenta amb UTF-8 primer (molt comú amb chcp 65001 i eines modernes)
            return str(byte_array, 'utf-8')
        except UnicodeDecodeError:
            # 2. Intenta amb l'encoding configurat/detectat (si és diferent d'utf-8)
            if self._encoding != 'utf-8':
                try:
                    return str(byte_array, self._encoding, errors='replace')
                except Exception as e:
                    print(f"Error de decodificació amb {self._encoding}: {e}. Intentant amb locale.")
                    pass # Continua al següent intent
            # 3. Intenta amb l'encoding preferit del sistema
            try:
                sys_enc = locale.getpreferredencoding(False)
                if sys_enc.lower() != 'utf-8' and sys_enc.lower() != self._encoding.lower():
                     return str(byte_array, sys_enc, errors='replace')
                else:
                     # Si sys_enc és utf-8 o el mateix que self._encoding, ja ho hem provat
                     raise ValueError("Ja s'ha provat utf-8/encoding configurat")
            except Exception as e2:
                 print(f"Error de decodificació amb locale ({locale.getpreferredencoding(False)}): {e2}. Usant repr().")
                 # 4. Fallback molt bàsic: representació dels bytes
                 return repr(byte_array)    


    def _handle_output(self):
        """Gestiona la sortida del procés, decodifica i converteix ANSI a HTML."""
        if not self._process: return
        byte_data = self._process.readAllStandardOutput()
        decoded_text = self._decode_bytes(byte_data)

        # Actualitza el buffer de text pla per a la detecció de prompt
        self._output_buffer += decoded_text

        # --- CORRECCIÓ: Reemplaça \n per <br>\n ---
        # Reemplacem \n per la versió HTML del salt de línia. Afegim un \n
        # després de <br> perquè el codi HTML resultant sigui una mica més llegible
        # si l'inspeccionem, però no afecta la renderització.
        # També eliminem \r (retorn de carro) si n'hi ha, que pot causar problemes.
        # text_for_html = decoded_text.replace('\r', '').replace('\n', '<br>\n')
        # Converteix el text original (amb codis ANSI però sense <br>) a HTML
        # ansi2html preservarà els \n originals o els convertirà en espais segons el context
        converted_html = self._ansi_converter.convert(decoded_text, full=False)        
        # ---------------------------------------------

        # Converteix el text decodificat (amb codis ANSI) a HTML
        # html_output = self._ansi_converter.convert(decoded_text, full=False)
        # html_output = self._ansi_converter.convert(text_for_html, full=False)
        # --- CORRECCIÓ: Reemplaça \n per <br> DESPRÉS de la conversió ANSI ---
        # Ara treballem sobre l'HTML generat per ansi2html
        # Reemplacem qualsevol \n restant (si ansi2html els va mantenir) per <br>
        # També eliminem \r per seguretat.
        final_html = converted_html.replace('\r', '').replace('\n', '<br>')
        # ----------------------------------------------------------------------

        # Mou el cursor al final abans d'afegir text HTML
        cursor = self._output_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._output_view.setTextCursor(cursor)

        # Inserir HTML
        # Important: Assegurem que els colors base del terminal (paleta)
        # tinguin prioritat sobre els que pugui generar ansi2html per defecte
        # si no hi ha codi ANSI de color específic.
        # Això es fa principalment ajustant el tema QSS o la paleta.
        # ansi2html respecta els colors ANSI explícits.
        # cursor.insertHtml(html_output)
        cursor.insertHtml(final_html)

        # Assegura que el final sigui visible
        self._output_view.ensureCursorVisible()

        # Reinicia el timer del prompt
        self._prompt_timer.start()
        self._prompt_detected = False


    def _is_prompt_like(self, text: str) -> bool:
        """Heurística bàsica per detectar un prompt de CMD."""
        # Busca línies que acabin amb '> ' precedides per un path o similar
        # Això és molt bàsic i pot fallar. Pot ser necessari ajustar-ho.
        lines = text.splitlines()
        if not lines:
            return False
        last_line = lines[-1].rstrip() # Treu espais finals

        # Exemple: C:\Users\Nom> , D:\Projecte> , etc.
        # També pot ser només '>' si està en una línia nova
        # Considera prompts personalitzats (més difícil)
        prompt_pattern = r"(?:[a-zA-Z]:\\.*>|>$)" # Patró molt simple
        return bool(re.search(prompt_pattern, last_line)) or last_line.endswith(">")

    def _check_prompt_and_run_next(self):
        """
        Mètode cridat pel timer. Comprova si la sortida recent s'assembla a un prompt
        i executa la següent comanda de la cua si n'hi ha.
        """
        if self._is_prompt_like(self._output_buffer):
            print("Prompt detectat.")
            self._prompt_detected = True
            self.prompt_available.emit() # Notifica que el prompt està llest

            # Executa la següent comanda de la cua (inicial o afegida)
            if self._command_queue:
                command = self._command_queue.pop(0)
                print(f"Executant comanda en cua: {command}")
                self.execute_command(command)
            else:
                # Actualitza el títol amb la branca Git si escau
                self._try_update_git_branch()


        # Neteja el buffer per a la propera detecció
        self._output_buffer = ""


    def execute_command(self, command: str):
        """Envia una comanda al procés del shell (utilitzant l'encoding correcte)."""
        if self._process and self._process.state() == QProcess.Running:
            print(f"Enviant comanda: {command}")
            # Sempre codifiquem a UTF-8 ara que hem forçat chcp 65001
            try:
                command_bytes = (command + '\n').encode('utf-8', errors='replace')
                self._process.write(command_bytes)
            except Exception as e:
                print(f"Error en codificar/escriure comanda: {e}")
                # Mostra l'error al terminal també
                error_html = f'<span style="color: red;">[Error enviant comanda: {e}]</span><br>'
                cursor = self._output_view.textCursor()
                cursor.movePosition(QTextCursor.End)
                self._output_view.setTextCursor(cursor)
                cursor.insertHtml(error_html)

            self._prompt_detected = False

            if command.strip().lower() in ['cls', 'clear']:
                QTimer.singleShot(100, self._output_view.clear) # Donem una mica més de temps

            cd_match = re.match(r"^\s*cd\s+(.*)", command, re.IGNORECASE)
            if cd_match:
                QTimer.singleShot(500, self._query_current_directory)

        else:
            # ... (gestió d'error si el procés no corre, mostra en HTML) ...
             error_html = '<span style="color: orange;">[Error: El terminal no està actiu]</span><br>'
             cursor = self._output_view.textCursor()
             cursor.movePosition(QTextCursor.End)
             self._output_view.setTextCursor(cursor)
             cursor.insertHtml(error_html)

    def _query_current_directory(self):
         """Envia 'cd' per obtenir el directori actual i actualitzar _working_directory."""
         # Això és una mica un hack. Una millor solució requeriria una lògica més complexa
         # per interpretar la sortida de 'cd'.
         if self._process and self._process.state() == QProcess.Running:
             # Aquesta comanda mostrarà el directori actual en la següent sortida
             self.execute_command("cd")
             # Idealment, hauríem de capturar aquesta sortida específicament,
             # però per ara, només actualitzem el títol quan es detecti el prompt.

    def _try_update_git_branch(self):
        """Intenta obtenir la branca Git actual i actualitza el títol."""
        # Només ho fem si estem raonablement segurs que el prompt està disponible
        if not self._prompt_detected:
             return

        # Executa 'git rev-parse...' en un procés separat per no bloquejar
        # i no interferir amb el terminal principal.
        git_process = QProcess(self)
        git_process.setWorkingDirectory(self._working_directory)
        git_process.finished.connect(lambda exitCode, exitStatus: self._handle_git_branch_result(git_process, exitCode, exitStatus))
        git_process.start("git", ["rev-parse", "--abbrev-ref", "HEAD"])

    def _handle_git_branch_result(self, process, exitCode, exitStatus):
        """Processa el resultat de la comanda git."""
        base_title = f"Terminal ({os.path.basename(self._working_directory)})" # O un nom donat
        if exitCode == 0 and exitStatus == QProcess.NormalExit:
            branch_name_bytes = process.readAllStandardOutput()
            branch_name = self._decode_bytes(branch_name_bytes).strip()
            if branch_name and branch_name != "HEAD": # HEAD indica detached state
                 self.title_changed.emit(f"{base_title} [{branch_name}]")
            else:
                 self.title_changed.emit(base_title) # No és repo Git o detached
        else:
            # Error en executar git o no és un repositori git
            self.title_changed.emit(base_title)

        process.deleteLater() # Neteja el procés temporal


    # def send_interrupt(self):
    #     """
    #     Envia un senyal CTRL_C_EVENT al grup de processos del terminal fill.
    #     """
    #     if self._process and self._process.state() == QProcess.Running:
    #         pid = self._process.processId() # Encara podem obtenir el PID per si el necessitem per logs
    #         print(f"Intentant enviar senyal Ctrl+C al grup de processos del terminal (associat a PID: {pid})...")

    #         if sys.platform == "win32":
    #             try:
    #                 CTRL_C_EVENT = 0
    #                 kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    #                 # --- Assegura't que el segon argument és 0 ---
    #                 if kernel32.GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0):
    #                      print("Senyal CTRL_C_EVENT enviat amb èxit al grup de processos del terminal.")
    #                 else:
    #                      error_code = ctypes.get_last_error()
    #                      error_message = ctypes.format_error(error_code)
    #                      print(f"Error en enviar CTRL_C_EVENT via API (grup 0) (Codi {error_code}): {error_message}")
    #                      # Fallback (opcional, però potser menys útil ara)
    #                      print("Intentant enviar caràcter Ctrl+C (fallback)...")
    #                      self._process.write(b'\x03')
    #             except Exception as e:
    #                 print(f"Error inesperat intentant enviar CTRL_C_EVENT via API: {e}")
    #                 # Fallback
    #                 print("Intentant enviar caràcter Ctrl+C (fallback)...")
    #                 self._process.write(b'\x03')
    #         else:
    #             # ... (codi per a altres plataformes) ...
    #             print("Plataforma no Windows. Enviant caràcter Ctrl+C...")
    #             self._process.write(b'\x03')

    #         # Esperem que el prompt torni
    #         self._prompt_detected = False
    #         self._prompt_timer.start()

    #     else:
    #         print("No es pot interrompre, el procés no està actiu.")


    # def send_interrupt(self):
    #     """
    #     Envia un senyal CTRL_C_EVENT al grup de processos del terminal fill.
    #     Si no es pot, intenta enviar directament el caràcter Ctrl+C.
    #     """
    #     if self._process and self._process.state() == QProcess.Running:
    #         pid = self._process.processId()
    #         print(f"Intentant enviar senyal Ctrl+C al procés (PID: {pid})...")

    #         if sys.platform == "win32":
    #             try:
    #                 # Intentem utilitzar l'API de Windows
    #                 CTRL_C_EVENT = 0
    #                 kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    #                 # Primer intentem amb el mètode més compatible (caràcter Ctrl+C)
    #                 print("Enviant caràcter Ctrl+C...")
    #                 self._process.write(b'\x03')

    #                 # Després, intentem usar l'API de Windows si no funciona el primer mètode
    #                 try:
    #                     if hasattr(kernel32, 'GenerateConsoleCtrlEvent'):
    #                         # Intentem enviar al grup de processos 0 (el propi)
    #                         if kernel32.GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0):
    #                             print("Senyal CTRL_C_EVENT enviat amb èxit.")
    #                         else:
    #                             error_code = ctypes.get_last_error()
    #                             error_message = ctypes.format_error(error_code)
    #                             print(f"Error en enviar CTRL_C_EVENT (Codi {error_code}): {error_message}")
    #                     else:
    #                         print("L'API GenerateConsoleCtrlEvent no està disponible, utilitzant només el caràcter Ctrl+C.")
    #                 except Exception as e:
    #                     print(f"Error en accedir a GenerateConsoleCtrlEvent: {e}")
    #             except Exception as e:
    #                 print(f"Error inesperat en gestionar la interrupció: {e}")
    #                 # Assegurem que almenys s'envia el caràcter Ctrl+C com a fallback
    #                 self._process.write(b'\x03')
    #         else:
    #             # Per a altres plataformes no Windows
    #             print("Plataforma no Windows. Enviant caràcter Ctrl+C...")
    #             self._process.write(b'\x03')

    #         # Esperem que el prompt torni
    #         self._prompt_detected = False
    #         self._prompt_timer.start()
    #     else:
    #         print("No es pot interrompre, el procés no està actiu.")   
    
    # def send_interrupt(self):
    #     """
    #     Envia un senyal d'interrupció Ctrl+C al procés fill.
    #     """
    #     if self._process and self._process.state() == QProcess.Running:
    #         pid = self._process.processId()
    #         print(f"Intentant enviar interrupció al procés (PID: {pid})...")

    #         if sys.platform == "win32":
    #             try:
    #                 # Opció 1: Envia el caràcter Ctrl+C directament al procés
    #                 print("Enviant caràcter Ctrl+C (\\x03)...")
    #                 self._process.write(b'\x03')
                    
    #                 # Opció 2: Si el mètode anterior falla, podem utilitzar taskkill amb l'opció /T per generar Ctrl+C
    #                 # (descomenteu si la primera opció no funciona prou bé)
    #                 # import subprocess
    #                 # print(f"Enviant senyal CTRL+BREAK a l'arbre de processos de {pid}...")
    #                 # try:
    #                 #     subprocess.run(['taskkill', '/PID', str(pid), '/T'], 
    #                 #                    capture_output=True, text=True, check=False)
    #                 #     print("Taskkill executat")
    #                 # except Exception as e:
    #                 #     print(f"Error al executar taskkill: {e}")
                    
    #             except Exception as e:
    #                 print(f"Error en enviar la interrupció: {e}")
    #         else:
    #             # Per a altres plataformes no Windows
    #             print("Plataforma no Windows. Enviant caràcter Ctrl+C...")
    #             self._process.write(b'\x03')

    #         # Esperem que el prompt torni
    #         self._prompt_detected = False
    #         self._prompt_timer.start()
            
    #         # Afegim una pausa curta per permetre el processament del senyal
    #         QTimer.singleShot(100, self._check_process_after_interrupt)
    #     else:
    #         print("No es pot interrompre, el procés no està actiu.")

    # def _check_process_after_interrupt(self):
    #     """Comprova l'estat del procés després d'enviar una interrupció."""
    #     if self._process and self._process.state() == QProcess.Running:
    #         print("El procés continua en execució després de la interrupció.")
    #     else:
    #         print("El procés s'ha aturat després de la interrupció.")
    #         # Si el procés s'ha aturat, podem emetre un senyal o fer una altra acció


    # def send_interrupt(self):
    #     """
    #     Envia un senyal d'interrupció al procés fill utilitzant diversos mètodes.
    #     """
    #     if self._process and self._process.state() == QProcess.Running:
    #         pid = self._process.processId()
    #         print(f"Intentant interrompre el procés (PID: {pid})...")

    #         if sys.platform == "win32":
    #             # Provem diversos mètodes en ordre, del més suau al més contundent
                
    #             # Mètode 1: Enviar caràcter Ctrl+C directament
    #             print("Mètode 1: Enviant caràcter Ctrl+C (\\x03)...")
    #             self._process.write(b'\x03')
                
    #             # Mètode 2: Utilitzar taskkill amb l'opció /BREAK
    #             # Això intenta enviar un break (similar a Ctrl+C) en comptes de matar el procés
    #             print(f"Mètode 2: Utilitzant taskkill /BREAK a PID {pid}...")
    #             try:
    #                 subprocess.run(['taskkill', '/PID', str(pid), '/BREAK'], 
    #                             capture_output=True, text=True, check=False)
    #             except Exception as e:
    #                 print(f"Error amb taskkill /BREAK: {e}")
                
    #             # Verificació i possible mètode 3 si es necessari
    #             QTimer.singleShot(500, lambda: self._check_and_try_alternate_interrupt(pid))
    #         else:
    #             # Per a altres plataformes no Windows
    #             print("Plataforma no Windows. Enviant caràcter Ctrl+C...")
    #             self._process.write(b'\x03')

    #         # Esperem que el prompt torni
    #         self._prompt_detected = False
    #         self._prompt_timer.start()
    #     else:
    #         print("No es pot interrompre, el procés no està actiu.")



    # def send_interrupt(self):
    #     """
    #     Envia un senyal d'interrupció al procés fill sense afectar l'aplicació principal.
    #     """
    #     if self._process and self._process.state() == QProcess.Running:
    #         pid = self._process.processId()
    #         print(f"Intentant interrompre el procés (PID: {pid})...")

    #         if sys.platform == "win32":
    #             # Opció 1: Enviar caràcter Ctrl+C directament
    #             print("Enviant caràcter Ctrl+C (\\x03)...")
    #             self._process.write(b'\x03')
                
    #             # Esperem un moment per veure si funciona
    #             QTimer.singleShot(300, lambda: self._try_additional_methods(pid))
    #         else:
    #             # Per a altres plataformes no Windows
    #             print("Plataforma no Windows. Enviant caràcter Ctrl+C...")
    #             self._process.write(b'\x03')

    #         # Esperem que el prompt torni
    #         self._prompt_detected = False
    #         self._prompt_timer.start()
    #     else:
    #         print("No es pot interrompre, el procés no està actiu.")



    def send_interrupt(self):
        """
        Mètode millorat per aturar processos Node.js i similars.
        """
        if self._process and self._process.state() == QProcess.Running:
            pid = self._process.processId()
            print(f"Intentant aturar el procés (PID: {pid})...")

            # Primer intentem amb Ctrl+C normal
            print("Enviant caràcter Ctrl+C (\\x03)...")
            self._process.write(b'\x03')
            
            # Esperem un moment i després utilitzem una aproximació més directa
            QTimer.singleShot(300, lambda: self._kill_node_processes(pid))

            # Esperem que el prompt torni
            self._prompt_detected = False
            self._prompt_timer.start()
        else:
            print("No es pot interrompre, el procés no està actiu.")

    def _kill_node_processes(self, cmd_pid):
        """
        Busca i atura específicament processos de Node.js i NPM.
        """
        if not self._process or self._process.state() != QProcess.Running:
            print("El procés ja s'ha aturat.")
            return
        
        cursor = self._output_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._output_view.setTextCursor(cursor)
        cursor.insertHtml('<br><span style="color:orange;"><b>Intentant aturar el servidor Node.js...</b></span><br>')
        
        try:
            # 1. Mètode directe: matar tots els processos node.exe descendents
            print("Buscant i aturant processos node.exe i npm...")
            
            # Obtenim la llista completa de processos
            result = subprocess.run(['tasklist', '/FO', 'CSV'], 
                                capture_output=True, text=True, check=False)
            
            # Busquem processos node.exe i npm
            node_pids = []
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'node.exe' in line.lower() or 'npm' in line.lower():
                        parts = line.strip('"').split('","')
                        if len(parts) >= 2:
                            try:
                                process_pid = parts[1]
                                node_pids.append(process_pid)
                                print(f"Trobat procés Node/NPM: {parts[0]} (PID: {process_pid})")
                            except:
                                pass
            
            # Si hem trobat processos Node.js, els aturem
            if node_pids:
                for node_pid in node_pids:
                    try:
                        print(f"Aturant procés Node.js {node_pid}...")
                        kill_result = subprocess.run(['taskkill', '/F', '/PID', node_pid], 
                                                capture_output=True, text=True, check=False)
                        print(f"Resultat: {kill_result.stdout}")
                        
                        cursor.insertHtml(f'<span style="color:green;">Procés Node.js {node_pid} aturat.</span><br>')
                    except Exception as e:
                        print(f"Error en aturar node {node_pid}: {e}")
            else:
                print("No s'han trobat processos Node.js específics.")
                
            # 2. Mètode alternatiu: obtenir i matar tots els processos descendents del cmd.exe
            print(f"Aturant tots els processos descendents del cmd.exe (PID: {cmd_pid})...")
            try:
                kill_tree = subprocess.run(['taskkill', '/F', '/T', '/PID', str(cmd_pid)], 
                                        capture_output=True, text=True, check=False)
                print(f"Resultat: {kill_tree.stdout}")
                if "No s'ha trobat" not in kill_tree.stdout and "ERROR:" not in kill_tree.stdout:
                    cursor.insertHtml('<span style="color:green;">Procés aturat correctament!</span><br>')
            except Exception as e:
                print(f"Error en aturar l'arbre de processos: {e}")
                
            # 3. Mètode de fallback: intentar matar només el procés CMD
            if self._process and self._process.state() == QProcess.Running:
                print("Intent final: terminant el procés cmd.exe...")
                self._process.kill()  # Això és bastant agressiu
                
        except Exception as e:
            print(f"Error en el procés d'aturada: {e}")
            cursor.insertHtml(f'<span style="color:red;">Error en aturar el servidor: {e}</span><br>')
        
        # Comprovem una última vegada
        QTimer.singleShot(1000, self._verify_process_termination)

    def _verify_process_termination(self):
        """
        Verifica si el procés s'ha aturat correctament i dona feedback a l'usuari.
        """
        if not self._process or self._process.state() != QProcess.Running:
            cursor = self._output_view.textCursor()
            cursor.movePosition(QTextCursor.End)
            self._output_view.setTextCursor(cursor)
            cursor.insertHtml('<span style="color:green;"><b>Tots els processos aturats correctament!</b></span><br>')
            print("Tots els processos aturats.")
        else:
            print("Alguns processos segueixen en execució.")
            cursor = self._output_view.textCursor()
            cursor.movePosition(QTextCursor.End)
            self._output_view.setTextCursor(cursor)
            cursor.insertHtml('<span style="color:orange;"><b>Alguns processos segueixen en execució.</b><br>Pots aturar-los manualment amb la comanda: <code>taskkill /F /IM node.exe /T</code></span><br>')


    def _try_additional_methods(self, pid):
        """
        Prova mètodes addicionals per interrompre el procés de manera segura.
        """
        if not self._process or self._process.state() != QProcess.Running:
            print("El procés ja s'ha aturat.")
            return
            
        print("Intent addicional: Buscant els processos fills per matar...")
        
        try:
            # Utilitzem tasklist per obtenir els fills del procés CMD
            result = subprocess.run(['tasklist', '/FI', f'PARENTPID eq {pid}', '/FO', 'CSV'], 
                                capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                # Processem la sortida per trobar PIDs de processos fill (node.exe, etc.)
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Primer línia és capçalera
                    for line in lines[1:]:
                        parts = line.strip('"').split('","')
                        if len(parts) >= 2:
                            process_name = parts[0]
                            child_pid = parts[1]
                            print(f"Trobat procés fill: {process_name} (PID: {child_pid})")
                            
                            # Si és node.exe o un altre procés que volem aturar
                            if 'node' in process_name.lower() or 'npm' in process_name.lower():
                                print(f"Enviant taskkill /T /PID {child_pid}...")
                                try:
                                    # /T mata l'arbre del procés
                                    kill_result = subprocess.run(['taskkill', '/T', '/PID', child_pid], 
                                                            capture_output=True, text=True, check=False)
                                    print(f"Resultat: {kill_result.stdout}")
                                except Exception as e:
                                    print(f"Error amb taskkill: {e}")
                else:
                    print("No s'han trobat processos fills.")
        except Exception as e:
            print(f"Error en buscar/matar processos fills: {e}")

        # Si encara segueix, ofereix comandes alternatives
        QTimer.singleShot(500, self._check_process_and_advise)

    def _check_process_and_advise(self):
        """
        Verifica si el procés encara s'executa i ofereix consell a l'usuari.
        """
        if not self._process or self._process.state() != QProcess.Running:
            print("El procés s'ha aturat correctament.")
            return
            
        print("Advertència: El procés encara s'executa.")
        print("Per a servidors Node.js, pots provar aquestes comandes:")
        print("1. 'taskkill /FI \"WINDOWTITLE eq node\" /T' per matar tots els processos node")
        print("2. Prem Ctrl+C directament a la finestra del CMD")
        
        # Insereix un text informatiu al terminal
        cursor = self._output_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._output_view.setTextCursor(cursor)
        cursor.insertHtml('<br><span style="color:orange;"><b>Per aturar el servidor:</b> Escriu .exit o prem Ctrl+C directament.</span><br>')




    def _check_and_try_alternate_interrupt(self, pid):
        """
        Comprova si el procés encara s'executa i prova un mètode alternatiu si cal.
        """
        if self._process and self._process.state() == QProcess.Running:
            print("El procés continua en execució. Provant mètode alternatiu...")
            
            # Mètode 3: Utilitzar generació d'esdeveniment de consola via API de Windows
            try:
                import ctypes
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                CTRL_C_EVENT = 0
                
                # Intentem amb el grup de processos 0 (el nostre propi grup)
                print("Mètode 3: Generant CTRL_C_EVENT al grup de processos...")
                if hasattr(kernel32, 'GenerateConsoleCtrlEvent'):
                    if kernel32.GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0):
                        print("Senyal CTRL_C_EVENT enviat.")
                    else:
                        error_code = ctypes.get_last_error()
                        print(f"Error enviant CTRL_C_EVENT: {ctypes.FormatError(error_code)}")
                
                # Verificació final
                QTimer.singleShot(500, self._final_interrupt_check)
                
            except Exception as e:
                print(f"Error amb l'API de Windows: {e}")
                self._try_taskkill_terminate(pid)
        else:
            print("El procés s'ha aturat correctament.")


    def _final_interrupt_check(self):
        """Comprova final i ofereix l'opció de terminació forçosa."""
        if self._process and self._process.state() == QProcess.Running:
            print("Advertència: El procés encara s'executa després de diversos intents d'interrupció.")
            print("Si desitges forçar la terminació, pots utilitzar 'kill' com a comanda.")
            
            # Opcionalment, podríem mostrar un diàleg preguntant a l'usuari
            # from PyQt5.QtWidgets import QMessageBox
            # if QMessageBox.question(self, "Procés No Respon", 
            #                         "El procés no respon a les senyals d'interrupció. Vols forçar la terminació?",
            #                         QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            #     self._process.kill()
        else:
            print("El procés s'ha aturat correctament.")



    def _try_taskkill_terminate(self, pid):
        """Intent final utilitzant taskkill /F si tot el demés falla."""
        try:
            print(f"Intent final: taskkill /F /PID {pid}...")
            # Atenció: això matarà el procés forçosament
            # subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
            #                capture_output=True, text=True, check=False)
            # En comptes d'executar-ho automàticament, només mostrem el missatge
            print("Pots executar manualment 'taskkill /F /PID {pid}' si ho necessites.")
        except Exception as e:
            print(f"Error amb taskkill /F: {e}")




    def _handle_finished(self, exitCode, exitStatus):
        """Gestiona quan el procés del shell finalitza."""
        status_text = "normalment" if exitStatus == QProcess.NormalExit else "amb error"
        final_message = f"\n[Terminal finalitzat {status_text} amb codi: {exitCode}]"
        print(final_message)

        # Mostra el missatge a la sortida
        cursor = self._output_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._output_view.setTextCursor(cursor)
        # Canvia el color per al missatge de finalització
        palette = self._output_view.palette()
        original_color = palette.color(QPalette.Text)
        self._output_view.setTextColor(QColor("orange"))
        cursor.insertText(final_message)
        self._output_view.setTextColor(original_color) # Restaura color original
        self._output_view.ensureCursorVisible()

        self._prompt_timer.stop()
        self.process_finished.emit(exitCode, exitStatus)

    def _handle_error(self, error):
        """Gestiona errors del QProcess."""
        error_map = {
            QProcess.FailedToStart: "No s'ha pogut iniciar el procés",
            QProcess.Crashed: "El procés ha fallat",
            QProcess.Timedout: "Temps d'espera esgotat",
            QProcess.WriteError: "Error d'escriptura al procés",
            QProcess.ReadError: "Error de lectura del procés",
            QProcess.UnknownError: "Error desconegut"
        }
        error_string = error_map.get(error, "Error desconegut")
        message = f"\n[Error del procés: {error_string} - {self._process.errorString()}]"
        print(message)
        self._output_view.setTextColor(QColor("red"))
        self._output_view.append(message)
        # Podríem voler restaurar el color aquí també

    def set_font(self, font: QFont):
        """Estableix la font del terminal."""
        self._output_view.setFont(font)

    def set_colors(self, background_color: QColor, text_color: QColor, cursor_color: QColor):
        """Estableix els colors del terminal."""
        palette = self._output_view.palette()
        palette.setColor(QPalette.Base, background_color) # Fons del QTextEdit
        palette.setColor(QPalette.Text, text_color)       # Color del text
        self._output_view.setPalette(palette)

        # El color del cursor del QTextEdit no es controla directament per paleta
        # Normalment hereta, però podem intentar canviar el color del text temporalment
        # o utilitzar fulls d'estil (més efectiu).
        # Per ara, actualitzem la paleta. El cursor sol ser similar al text o invertir.

        # Actualitza el convertidor ANSI segons el fons
        self._update_ansi_converter_theme(background_color)

    def _update_ansi_converter_theme(self, background_color: QColor):
        """Configura el tema del convertidor ANSI segons la lluminositat del fons."""
        if background_color.lightnessF() < 0.5:
             # Fons fosc
             self._ansi_converter = Ansi2HTMLConverter(inline=True, dark_bg=True, scheme='xterm')
        else:
             # Fons clar
             self._ansi_converter = Ansi2HTMLConverter(inline=True, dark_bg=False, scheme='solarized') # Prova solarized per a fons clars
        # Pots provar diferents 'scheme' (ex: 'solarized', 'monokai', 'vscode', 'xterm', etc.)

    def apply_styles(self, font=None, bg_color=None, fg_color=None, cursor_color=None):
        """Aplica estils (font i colors) al terminal."""
        # Utilitza valors per defecte si no es proporcionen
        if font is None:
            # font = QFont(config.DEFAULT_FONT_FAMILY, config.DEFAULT_FONT_SIZE)
            font = QFont(config.DEFAULT_FONT_FAMILY(), config.DEFAULT_FONT_SIZE) # Afegit ()
        if bg_color is None:
            bg_color = QColor(config.DEFAULT_BG_COLOR)
        if fg_color is None:
            fg_color = QColor(config.DEFAULT_FG_COLOR)
        if cursor_color is None:
            cursor_color = QColor(config.DEFAULT_CURSOR_COLOR) # Nota: cursor_color no s'aplica directament aquí

        self.set_font(font)
        # self.set_colors(bg_color, fg_color, cursor_color)
        self.set_colors(bg_color, fg_color, QColor(config.DEFAULT_CURSOR_COLOR)) # Passa cursor color (encara que no s'usi directament)

        # Actualitza el convertidor ANSI segons el fons
        self._update_ansi_converter_theme(bg_color)


    def close_terminal(self):
        """Tanca el procés del terminal de manera segura."""
        print("Intentant tancar el terminal...")
        self._prompt_timer.stop()
        if self._process and self._process.state() != QProcess.NotRunning:
            # Intenta tancar suaument primer (pot no funcionar amb CMD)
            self._process.terminate()
            # Espera una mica a que tanqui
            if not self._process.waitForFinished(500):
                print("El procés no ha terminat suaument, forçant el tancament.")
                self._process.kill() # Força el tancament
                self._process.waitForFinished(500) # Espera final
        print("Terminal tancat.")

    def get_state(self) -> dict:
        """Retorna l'estat actual per guardar-lo en un layout."""
        # Nota: No podem obtenir fàcilment les comandes pendents si ja s'han enviat
        return {
            "name": self.windowTitle(), # O un nom intern si el gestionem
            "shell": self._shell_path,
            "encoding": self._encoding,
            "working_directory": self._working_directory,
            "startup_commands": self._startup_commands # Les comandes originals
        }

    def set_working_directory(self, directory: str):
        """Canvia el directori de treball (si el procés ja ha començat, això és més complex)."""
        # Això és millor fer-ho a la creació. Canviar-ho després requeriria enviar 'cd'
        if self._process.state() == QProcess.NotRunning:
             if os.path.isdir(directory):
                 self._working_directory = directory
                 self._process.setWorkingDirectory(directory)
             else:
                 print(f"Directori no vàlid: {directory}")
        else:
            # Envia comanda 'cd' al terminal actiu
            if os.path.isdir(directory):
                 # Cal escapar espais i caràcters especials si és necessari
                 self.execute_command(f'cd /d "{directory}"') # /d per canviar de unitat també
                 # Actualitza internament després d'un temps o quan es detecti el prompt
                 # self._working_directory = directory # Actualitza immediatament o espera confirmació?
                 # Esperar confirmació és més segur
                 QTimer.singleShot(200, lambda: setattr(self, '_working_directory', directory))

            else:
                 print(f"Directori no vàlid per 'cd': {directory}")


    # --- Getters ---
    def get_output_view(self) -> QTextEdit:
        return self._output_view

    def get_working_directory(self) -> str:
        return self._working_directory
    
