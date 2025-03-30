# command_line_edit.py
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal

class CommandLineEdit(QLineEdit):
    """
    QLineEdit especialitzat amb historial de comandes i gestió de tecles.
    """
    execute_command = pyqtSignal(str)
    interrupt_signal = pyqtSignal() # Senyal per Ctrl+C

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._history_index = -1
        self._pending_text = "" # Per guardar text escrit abans de navegar per l'historial

    def add_to_history(self, command):
        """Afegeix una comanda a l'historial si no és buida i no és igual a l'última."""
        if command and (not self._history or self._history[-1] != command):
            self._history.append(command)
            # Opcional: Limitar la mida de l'historial
            # MAX_HISTORY = 100
            # if len(self._history) > MAX_HISTORY:
            #     self._history.pop(0)
        self._history_index = len(self._history) # Reset index per apuntar al final (nova entrada)
        self._pending_text = ""

    def keyPressEvent(self, event):
        """Gestiona les tecles de fletxa per a l'historial i Enter per executar."""
        key = event.key()

        if key == Qt.Key_Return or key == Qt.Key_Enter:
            command = self.text().strip()
            if command:
                self.execute_command.emit(command)
                self.add_to_history(command)
            self.clear() # Neteja després d'enviar
            self._history_index = len(self._history) # Apunta al final
            self._pending_text = ""
        elif key == Qt.Key_Up:
            if self._history_index == len(self._history):
                 self._pending_text = self.text() # Guarda text actual si comencem a navegar

            if self._history_index > 0:
                self._history_index -= 1
                self.setText(self._history[self._history_index])
            elif self._history_index == 0 and self._history:
                 self.setText(self._history[0]) # Queda't a la primera entrada
            else:
                 # Ja estem al principi o no hi ha historial
                 pass

        elif key == Qt.Key_Down:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self.setText(self._history[self._history_index])
            elif self._history_index == len(self._history) - 1:
                 # Estem a l'última entrada de l'historial, anem a la línia pendent
                 self._history_index = len(self._history)
                 self.setText(self._pending_text)

        elif key == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
            # Captura Ctrl+C per interrompre el procés associat
            self.interrupt_signal.emit()
            # No passem l'event per evitar que QLineEdit faci alguna acció (com copiar)
            event.accept()
            # Important! Retornar immediatament per evitar que PyQt processi el Ctrl+C
            return
        else:
            # Qualsevol altra tecla, deixa que QLineEdit la gestioni
            super().keyPressEvent(event)
            # Si l'usuari escriu després de navegar, reseteja l'índex
            # (això pot ser una mica complex de gestionar perfectament,
            #  però és un bon punt de partida)
            # if self._history_index != len(self._history):
            #     pass # De moment, permet editar l'entrada de l'historial




    def clear_history(self):
        self._history = []
        self._history_index = -1
        self._pending_text = ""