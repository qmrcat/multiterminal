# settings_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QFontComboBox,
                             QSpinBox, QPushButton, QColorDialog, QLabel,
                             QHBoxLayout, QLineEdit, QFileDialog, QComboBox)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import pyqtSignal, QSettings

import config # Importa la configuració

class ColorButton(QPushButton):
    """Botó que mostra un color i obre un QColorDialog al clicar."""
    colorChanged = pyqtSignal(QColor)

    def __init__(self, initial_color=QColor("white"), parent=None):
        super().__init__(parent)
        self._color = initial_color
        self.setStyleSheet(f"background-color: {self._color.name()};")
        self.clicked.connect(self._pick_color)

    def _pick_color(self):
        dialog = QColorDialog(self._color, self)
        if dialog.exec_():
            new_color = dialog.currentColor()
            self.setColor(new_color)

    def setColor(self, color):
        if color != self._color:
            self._color = color
            self.setStyleSheet(f"background-color: {self._color.name()};")
            self.colorChanged.emit(self._color)

    def color(self) -> QColor:
        return self._color

class SettingsDialog(QDialog):
    """Diàleg per configurar les opcions de l'aplicació."""
    settings_applied = pyqtSignal() # Senyal emès quan s'apliquen els canvis

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuració - MultiTerminal")
        self.settings = QSettings(config.ORGANIZATION_NAME, config.APPLICATION_NAME)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # --- Aparença ---
        self.font_combo = QFontComboBox(self)
        self.font_size_spin = QSpinBox(self)
        self.font_size_spin.setRange(6, 72)
        self.font_size_spin.setSuffix(" pt")

        font_layout = QHBoxLayout()
        font_layout.addWidget(self.font_combo)
        font_layout.addWidget(self.font_size_spin)
        form_layout.addRow("Font:", font_layout)

        self.bg_color_button = ColorButton(parent=self)
        form_layout.addRow("Color de fons:", self.bg_color_button)

        self.fg_color_button = ColorButton(parent=self)
        form_layout.addRow("Color de text:", self.fg_color_button)

        # self.cursor_color_button = ColorButton(self) # El color del cursor és més complex
        # form_layout.addRow("Color del cursor:", self.cursor_color_button)

        self.theme_combo = QComboBox(self)
        # Afegeix temes disponibles (pots buscar fitxers .qss a la carpeta themes)
        self.theme_combo.addItems(["default", "dark", "light"]) # Afegir més si cal
        form_layout.addRow("Tema:", self.theme_combo)


        # --- Terminal ---
        self.shell_edit = QLineEdit(self)
        self.shell_browse_button = QPushButton("Navega...", self)
        self.shell_browse_button.clicked.connect(self._browse_shell)
        shell_layout = QHBoxLayout()
        shell_layout.addWidget(self.shell_edit)
        shell_layout.addWidget(self.shell_browse_button)
        form_layout.addRow("Shell:", shell_layout)

        self.encoding_edit = QLineEdit(self)
        form_layout.addRow("Codificació:", self.encoding_edit)

        self.prompt_timeout_spin = QSpinBox(self)
        self.prompt_timeout_spin.setRange(50, 2000)
        self.prompt_timeout_spin.setSuffix(" ms")
        form_layout.addRow("Temps espera prompt:", self.prompt_timeout_spin)

        # --- Botons ---
        button_box = QHBoxLayout()
        self.reset_button = QPushButton("Restaurar Predeterminat", self)
        self.reset_button.clicked.connect(self._load_defaults)
        self.apply_button = QPushButton("Aplicar", self)
        self.apply_button.clicked.connect(self.apply_settings)
        self.ok_button = QPushButton("Acceptar", self)
        self.ok_button.clicked.connect(self.accept) # accept() crida a apply_settings
        self.cancel_button = QPushButton("Cancel·lar", self)
        self.cancel_button.clicked.connect(self.reject)

        button_box.addWidget(self.reset_button)
        button_box.addStretch()
        button_box.addWidget(self.apply_button)
        button_box.addWidget(self.ok_button)
        button_box.addWidget(self.cancel_button)

        layout.addLayout(form_layout)
        layout.addLayout(button_box)

        self.load_settings() # Carrega valors actuals

    def _browse_shell(self):
        """Obre un diàleg per seleccionar l'executable del shell."""
        filename, _ = QFileDialog.getOpenFileName(self, "Selecciona el Shell", "", "Executables (*.exe);;Tots els fitxers (*)")
        if filename:
            self.shell_edit.setText(filename)

    def load_settings(self):
        """Carrega la configuració des de QSettings."""
        # font_family = self.settings.value(config.SETTINGS_FONT_FAMILY, config.DEFAULT_FONT_FAMILY)
        font_family = self.settings.value(config.SETTINGS_FONT_FAMILY, config.DEFAULT_FONT_FAMILY()) # Afegit ()
        font_size = int(self.settings.value(config.SETTINGS_FONT_SIZE, config.DEFAULT_FONT_SIZE))

        # bg_color = QColor(self.settings.value(config.SETTINGS_BG_COLOR, config.DEFAULT_BG_COLOR))
        # fg_color = QColor(self.settings.value(config.SETTINGS_FG_COLOR, config.DEFAULT_FG_COLOR))
        bg_color_str = self.settings.value(config.SETTINGS_BG_COLOR, config.DEFAULT_BG_COLOR)
        fg_color_str = self.settings.value(config.SETTINGS_FG_COLOR, config.DEFAULT_FG_COLOR)

        bg_color = QColor(bg_color_str)
        fg_color = QColor(fg_color_str)
        # cursor_color = QColor(self.settings.value(config.SETTINGS_CURSOR_COLOR, config.DEFAULT_CURSOR_COLOR))
        theme = self.settings.value(config.SETTINGS_THEME, "default")

        shell_path = self.settings.value(config.SETTINGS_SHELL_PATH, config.DEFAULT_SHELL)
        encoding = self.settings.value(config.SETTINGS_ENCODING, config.DEFAULT_ENCODING)
        prompt_timeout = int(self.settings.value(config.SETTINGS_PROMPT_TIMEOUT, config.DEFAULT_PROMPT_TIMEOUT))

        self.font_combo.setCurrentFont(QFont(font_family))
        self.font_size_spin.setValue(font_size)
        self.bg_color_button.setColor(bg_color)
        self.fg_color_button.setColor(fg_color)
        # self.cursor_color_button.setColor(cursor_color)
        self.theme_combo.setCurrentText(theme)

        self.shell_edit.setText(shell_path)
        self.encoding_edit.setText(encoding)
        self.prompt_timeout_spin.setValue(prompt_timeout)

    def _load_defaults(self):
         """Carrega els valors per defecte als controls del diàleg."""
        #  self.font_combo.setCurrentFont(QFont(config.DEFAULT_FONT_FAMILY))
         self.font_combo.setCurrentFont(QFont(config.DEFAULT_FONT_FAMILY())) # Afegit ()
         self.font_size_spin.setValue(config.DEFAULT_FONT_SIZE)
         
         self.bg_color_button.setColor(QColor(config.DEFAULT_BG_COLOR))
         self.fg_color_button.setColor(QColor(config.DEFAULT_FG_COLOR))
         # self.cursor_color_button.setColor(QColor(config.DEFAULT_CURSOR_COLOR))
         self.theme_combo.setCurrentText("default")

         self.shell_edit.setText(config.DEFAULT_SHELL)
         self.encoding_edit.setText(config.DEFAULT_ENCODING)
         self.prompt_timeout_spin.setValue(config.DEFAULT_PROMPT_TIMEOUT)


    def save_settings(self):
        """Guarda la configuració actual a QSettings."""
        self.settings.setValue(config.SETTINGS_FONT_FAMILY, self.font_combo.currentFont().family())
        self.settings.setValue(config.SETTINGS_FONT_SIZE, self.font_size_spin.value())
        self.settings.setValue(config.SETTINGS_BG_COLOR, self.bg_color_button.color().name())
        self.settings.setValue(config.SETTINGS_FG_COLOR, self.fg_color_button.color().name())
        # self.settings.setValue(config.SETTINGS_CURSOR_COLOR, self.cursor_color_button.color().name())
        self.settings.setValue(config.SETTINGS_THEME, self.theme_combo.currentText())

        self.settings.setValue(config.SETTINGS_SHELL_PATH, self.shell_edit.text())
        self.settings.setValue(config.SETTINGS_ENCODING, self.encoding_edit.text())
        self.settings.setValue(config.SETTINGS_PROMPT_TIMEOUT, self.prompt_timeout_spin.value())

        print("Configuració guardada.")

    def apply_settings(self):
        """Guarda la configuració i emet el senyal per aplicar-la."""
        self.save_settings()
        self.settings_applied.emit()
        print("Senyal settings_applied emès.")

    def accept(self):
        """Aplica els canvis i tanca el diàleg."""
        self.apply_settings()
        super().accept()