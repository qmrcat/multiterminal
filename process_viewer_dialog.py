# process_viewer_dialog.py
import os
import sys
import subprocess

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTableWidget, QTableWidgetItem, QLabel, QHeaderView,
                            QMessageBox, QComboBox, QProgressBar, QApplication,
                            QCheckBox )
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QColor

class ProcessInfoWorker(QThread):
    """Thread separat per obtenir informació de processos sense bloquejar la interfície."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, cmd_pid, parent=None):
        super().__init__(parent)
        self.cmd_pid = cmd_pid
        
    def run(self):
        try:
            process_info = self._get_process_info(self.cmd_pid)
            self.finished.emit(process_info)
        except Exception as e:
            self.error.emit(str(e))
            
    def _get_process_info(self, cmd_pid):
        """Obté només informació dels processos relacionats amb el terminal."""
        processes = {}
        
        try:
            # Primer afegim el procés CMD
            processes[str(cmd_pid)] = {
                "name": "cmd.exe",
                "pid": str(cmd_pid),
                "memory": "N/A",
                "cpu": "N/A",
                "title": "Terminal CMD (procés principal)",
                "related": True
            }
            
            # Obtenim els processos relacionats
            try:
                # 1. Intentem obtenir tots els processos
                result = subprocess.run(
                    ['tasklist', '/FO', 'CSV'], 
                    capture_output=True, 
                    text=True,
                    encoding='cp850',
                    errors='replace',
                    check=False,
                    timeout=3
                )
                
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        for line in lines[1:]:
                            try:
                                parts = line.strip('"').split('","')
                                if len(parts) >= 2:
                                    name = parts[0]
                                    pid = parts[1]
                                    mem = parts[4] if len(parts) > 4 else "N/A"
                                    
                                    # Només afegim processos que són probablement relacionats
                                    if (name.lower() in ['node.exe', 'npm.cmd', 'npm.exe', 'python.exe', 
                                                        'java.exe', 'gcc.exe', 'cargo.exe', 'rustc.exe',
                                                        'git.exe', 'php.exe', 'tailwindcss.exe']):
                                        processes[pid] = {
                                            "name": name,
                                            "pid": pid,
                                            "memory": mem,
                                            "cpu": "N/A",
                                            "title": f"{name} (PID: {pid})",
                                            "related": True
                                        }
                            except Exception as e:
                                continue
                
                # 2. Intentem identificar els fills directes del procés CMD
                # Això és complex a Windows però podem utilitzar WMIC
                try:
                    # Aquest mètode busca processos iniciats des del cmd
                    creations = subprocess.run(
                        ['wmic', 'process', 'where', f'ParentProcessId={cmd_pid}', 'get', 'ProcessId,Name,CommandLine'],
                        capture_output=True,
                        text=True,
                        encoding='cp850',
                        errors='replace',
                        check=False,
                        timeout=3
                    )
                    
                    if creations.returncode == 0 and creations.stdout:
                        lines = creations.stdout.strip().split('\n')
                        for line in lines[1:]:  # Saltant capçalera
                            parts = line.strip().split()
                            if parts and len(parts) >= 2:
                                try:
                                    # L'últim element sol ser el PID a la sortida de WMIC
                                    child_pid = parts[-1]
                                    if child_pid.isdigit() and child_pid != str(cmd_pid):
                                        # Obtenim més informació del procés si no és cmd.exe
                                        child_name = parts[-2] if len(parts) >= 2 else "Desconegut"
                                        # Si és un procés interessant i no estava ja a la llista, l'afegim
                                        if child_pid not in processes:
                                            processes[child_pid] = {
                                                "name": child_name,
                                                "pid": child_pid,
                                                "memory": "N/A",
                                                "cpu": "N/A",
                                                "title": f"Fill directe del CMD: {child_name}",
                                                "related": True
                                            }
                                except Exception:
                                    pass  # Ignorem errors en processar la línia
                except Exception as e:
                    print(f"Error en detectar fills directes: {e}")
                
            except Exception as e:
                print(f"Error en obtenir la llista de processos: {e}")
            
            return processes
            
        except Exception as e:
            print(f"Error global: {e}")
            # Retornem almenys el procés CMD
            return {
                str(cmd_pid): {
                    "name": "cmd.exe",
                    "pid": str(cmd_pid),
                    "memory": "N/A",
                    "cpu": "N/A", 
                    "title": "Terminal CMD (error en trobar més processos)",
                    "related": True
                }
            }

class ProcessViewerDialog(QDialog):
    """Diàleg per veure i gestionar els processos associats als terminals."""
    
    def __init__(self, terminals_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processos en Execució")
        self.resize(700, 400)
        self.terminals_data = terminals_data
        self.process_info = {}
        self.worker = None
        self.auto_refresh_enabled = False  # Per defecte, desactivat
        
        self._setup_ui()
        self._connect_signals()
        
        # Primera càrrega inicial
        QTimer.singleShot(100, self.refresh_processes)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Selector de terminal
        terminal_layout = QHBoxLayout()
        terminal_layout.addWidget(QLabel("Terminal:"))
        self.terminal_selector = QComboBox()
        self._populate_terminal_selector()
        terminal_layout.addWidget(self.terminal_selector)
        terminal_layout.addStretch()
        
        # Botons i opcions
        self.refresh_button = QPushButton("Actualitza")
        self.kill_button = QPushButton("Finalitza Procés")
        self.auto_refresh_check = QCheckBox("Actualització automàtica")
        self.auto_refresh_check.setChecked(False)
        
        terminal_layout.addWidget(self.auto_refresh_check)
        terminal_layout.addWidget(self.refresh_button)
        terminal_layout.addWidget(self.kill_button)
        
        layout.addLayout(terminal_layout)
        
        # Barra de progrés 
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Etiqueta d'estat
        self.status_label = QLabel("Carregant informació de processos...")
        layout.addWidget(self.status_label)
        
        # Taula de processos amb millor contrast
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels(["PID", "Procés", "Memòria", "CPU", "Detalls"])
        self.process_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setSortingEnabled(True)
        
        # Millora del contrast general de la taula
        palette = self.process_table.palette()
        palette.setColor(palette.Text, Qt.black)
        palette.setColor(palette.Base, Qt.white)
        palette.setColor(palette.AlternateBase, QColor(240, 240, 240))  # Gris molt clar pels alternatius
        self.process_table.setPalette(palette)
        
        # També per als headers
        header_palette = self.process_table.horizontalHeader().palette()
        header_palette.setColor(palette.Text, Qt.black)
        header_palette.setColor(palette.Button, QColor(220, 220, 220))  # Gris clar pels headers
        self.process_table.horizontalHeader().setPalette(header_palette)
        
        layout.addWidget(self.process_table)


        # Botó de tancar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.close_button = QPushButton("Tanca")
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
    
    def _populate_terminal_selector(self):
        self.terminal_selector.clear()
        for idx, data in self.terminals_data.items():
            tab_name = self.parent().tab_widget.tabText(idx)
            self.terminal_selector.addItem(tab_name, idx)
    
    def _connect_signals(self):
        self.close_button.clicked.connect(self.accept)
        self.refresh_button.clicked.connect(self.refresh_processes)
        self.kill_button.clicked.connect(self._kill_selected_process)
        self.terminal_selector.currentIndexChanged.connect(self.refresh_processes)
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
    
    def _toggle_auto_refresh(self, state):
        """Activa o desactiva l'actualització automàtica."""
        self.auto_refresh_enabled = bool(state)
        if self.auto_refresh_enabled:
            if not hasattr(self, 'update_timer') or not self.update_timer.isActive():
                self.update_timer = QTimer(self)
                self.update_timer.setInterval(5000)  # 5 segons
                self.update_timer.timeout.connect(self.refresh_processes)
                self.update_timer.start()
            self.status_label.setText("Actualització automàtica activada (cada 5 segons)")
        else:
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()
            self.status_label.setText("Actualització automàtica desactivada")
    
    def refresh_processes(self):
        current_idx = self.terminal_selector.currentData()
        if current_idx is None:
            return
        
        term_data = self.terminals_data.get(current_idx)
        if not term_data or not term_data.get("widget"):
            return
        
        term_widget = term_data.get("widget")
        cmd_pid = term_widget._process.processId() if term_widget._process else None
        
        if not cmd_pid:
            self.process_table.setRowCount(0)
            self.status_label.setText("No hi ha processos actius en aquest terminal.")
            return
        
        # Mostrem indicador de càrrega
        self.progress_bar.setVisible(True)
        self.status_label.setText("Carregant informació de processos...")
        self.refresh_button.setEnabled(False)
        QApplication.processEvents()
        
        # Aturem qualsevol worker anterior
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        # Creem i iniciem un nou worker
        self.worker = ProcessInfoWorker(cmd_pid, self)
        self.worker.finished.connect(self._update_process_table)
        self.worker.error.connect(self._handle_worker_error)
        self.worker.finished.connect(lambda: self._finish_loading())
        self.worker.error.connect(lambda: self._finish_loading())
        self.worker.start()
    
    def _finish_loading(self):
        self.progress_bar.setVisible(False)
        self.refresh_button.setEnabled(True)
        
    def _handle_worker_error(self, error_msg):
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.warning(self, "Error", f"Error en obtenir informació dels processos:\n{error_msg}")
    
    def _update_process_table(self, process_info):
        # Guardem l'estat de selecció actual
        selected_pid = None
        current_row = self.process_table.currentRow()
        if current_row >= 0:
            pid_item = self.process_table.item(current_row, 0)
            if pid_item:
                selected_pid = pid_item.text()

        # Actualitzem l'estructura de dades
        self.process_info = process_info
        
        # Només recreem la taula si no hi havia dades abans
        if self.process_table.rowCount() == 0:
            self._recreate_process_table(process_info)
        else:
            # Si ja hi havia dades, només actualitzem els elements que han canviat
            self._update_existing_table(process_info)
            
        # Restaurem la selecció si és possible
        if selected_pid:
            for row in range(self.process_table.rowCount()):
                if self.process_table.item(row, 0).text() == selected_pid:
                    self.process_table.selectRow(row)
                    break
        
        # Actualitzem l'etiqueta d'estat
        self.status_label.setText(f"S'han trobat {len(process_info)} processos relacionats amb el terminal.")
        
        # Si no està marcat l'auto-refresh, desactivem qualsevol temporitzador
        if not self.auto_refresh_enabled and hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()


    
    def _recreate_process_table(self, process_info):
        """Recrea la taula des de zero (només quan cal)."""
        self.process_table.setSortingEnabled(False)  # Desactivem temporalment ordenació
        self.process_table.setRowCount(0)
        
        row = 0
        for pid, info in process_info.items():
            self.process_table.insertRow(row)
            
            # # Afegim les dades
            # self.process_table.setItem(row, 0, QTableWidgetItem(pid))
            # self.process_table.setItem(row, 1, QTableWidgetItem(info["name"]))
            # self.process_table.setItem(row, 2, QTableWidgetItem(info["memory"]))
            # self.process_table.setItem(row, 3, QTableWidgetItem(info["cpu"]))
            # self.process_table.setItem(row, 4, QTableWidgetItem(info["title"]))

            # Afegim les dades amb color de text fosc per més contrast
            for col, text in enumerate([pid, info["name"], info["memory"], info["cpu"], info["title"]]):
                item = QTableWidgetItem(text)
                item.setForeground(Qt.black)  # Text fosc per a totes les cel·les
                self.process_table.setItem(row, col, item)
            
            # Estil especial per al procés cmd.exe
            if info["name"].lower() == "cmd.exe":
                for col in range(5):
                    item = self.process_table.item(row, col)
                    if item:
                        # # Fons més fosc per millorar el contrast
                        # item.setBackground(QColor(180, 180, 180))  # Gris més fosc
                        # item.setForeground(Qt.black)  # Text negre
                        item.setBackground(QColor(180, 180, 180))  # Gris més fosc
                        item.setForeground(Qt.black)  # Text negre
            
            # Estil per a processos importants
            if "node" in info["name"].lower() or "npm" in info["name"].lower():
                for col in range(5):
                    item = self.process_table.item(row, col)
                    if item:
                        # # Fons groc per a node/npm
                        # item.setBackground(Qt.yellow)
                        # Fons groc més intens per contrast
                        item.setBackground(QColor(255, 223, 0))  # Groc més intens
                        item.setForeground(Qt.black)  # Text negre                        
            
            row += 1
            
        self.process_table.setSortingEnabled(True)  # Reactivem ordenació
        
    def _update_existing_table(self, process_info):
        """Actualitza la taula existent sense recrear-la completament."""
        # Construïm un conjunt de PIDs actuals
        current_pids = set()
        for row in range(self.process_table.rowCount()):
            pid_item = self.process_table.item(row, 0)
            if pid_item:
                current_pids.add(pid_item.text())
        
        # Construïm un conjunt de PIDs nous
        new_pids = set(process_info.keys())
        
        # 1. Eliminem files de processos que ja no existeixen
        for row in range(self.process_table.rowCount() - 1, -1, -1):
            pid_item = self.process_table.item(row, 0)
            if pid_item and pid_item.text() not in new_pids:
                self.process_table.removeRow(row)
        
        # 2. Actualitzem les files existents
        for row in range(self.process_table.rowCount()):
            pid_item = self.process_table.item(row, 0)
            if pid_item:
                pid = pid_item.text()
                if pid in process_info:
                    info = process_info[pid]
                    # Actualitzem les dades que podrien haver canviat
                    self.process_table.item(row, 2).setText(info["memory"])
                    self.process_table.item(row, 3).setText(info["cpu"])
                    # La resta normalment no canvia
        
        # 3. Afegim noves files per als processos nous
        for pid in new_pids:
            if pid not in current_pids:
                info = process_info[pid]
                row = self.process_table.rowCount()
                self.process_table.insertRow(row)
                
                # self.process_table.setItem(row, 0, QTableWidgetItem(pid))
                # self.process_table.setItem(row, 1, QTableWidgetItem(info["name"]))
                # self.process_table.setItem(row, 2, QTableWidgetItem(info["memory"]))
                # self.process_table.setItem(row, 3, QTableWidgetItem(info["cpu"]))
                # self.process_table.setItem(row, 4, QTableWidgetItem(info["title"]))

                # Afegim les dades amb color de text fosc
                for col, text in enumerate([pid, info["name"], info["memory"], info["cpu"], info["title"]]):
                    item = QTableWidgetItem(text)
                    item.setForeground(Qt.black)  # Text fosc per a totes les cel·les
                    self.process_table.setItem(row, col, item)
                
                # Estil especial per al procés cmd.exe
                if info["name"].lower() == "cmd.exe":
                    for col in range(5):
                        item = self.process_table.item(row, col)
                        if item:
                            # item.setBackground(Qt.lightGray)
                            item.setBackground(QColor(180, 180, 180))  # Gris més fosc
                            item.setForeground(Qt.black)  # Text negre
                
                # Estil per a processos importants
                if "node" in info["name"].lower() or "npm" in info["name"].lower():
                    for col in range(5):
                        item = self.process_table.item(row, col)
                        if item:
                            # item.setBackground(Qt.yellow)
                            item.setBackground(QColor(255, 223, 0))  # Groc més intens
                            item.setForeground(Qt.black)  # Text negre


    
    def _kill_selected_process(self):
        current_row = self.process_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Selecció", "Cal seleccionar un procés primer.")
            return
        
        pid_item = self.process_table.item(current_row, 0)
        process_item = self.process_table.item(current_row, 1)
        
        if not pid_item or not process_item:
            return
            
        pid = pid_item.text()
        process_name = process_item.text()
        
        # Confirmació
        reply = QMessageBox.question(
            self, 
            "Confirmar Finalització",
            f"Segur que vols finalitzar el procés {process_name} (PID: {pid})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            self.status_label.setText(f"Finalitzant procés {pid}...")
            result = subprocess.run(
                ['taskkill', '/F', '/PID', pid], 
                capture_output=True, 
                text=True, 
                encoding='cp850',
                errors='replace',
                check=False
            )
            
            if result.returncode == 0:
                QMessageBox.information(self, "Èxit", f"El procés {process_name} (PID: {pid}) s'ha finalitzat.")
                QTimer.singleShot(500, self.refresh_processes)
            else:
                QMessageBox.warning(self, "Error", f"No s'ha pogut finalitzar el procés: {result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en finalitzar el procés: {e}")
    
    def closeEvent(self, event):
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        super().closeEvent(event)