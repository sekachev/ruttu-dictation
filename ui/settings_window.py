from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QTextEdit, QFormLayout, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt

class SettingsWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.setWindowTitle("ruttu.ee - Settings")
        self.setMinimumSize(500, 400)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        self.tabs.addTab(self.create_general_tab(), "General")
        self.tabs.addTab(self.create_api_tab(), "API & Engine")
        self.tabs.addTab(self.create_exclusions_tab(), "Exclusions")
        self.tabs.addTab(self.create_commands_tab(), "Commands")
        
        layout.addWidget(self.tabs)
        
        self.save_btn = QPushButton("Save & Restart")
        self.save_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_btn)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def create_general_tab(self):
        widget = QWidget()
        layout = QFormLayout()
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ru", "ee", "en"])
        self.lang_combo.setCurrentText(self.config.get("language"))
        
        self.hotkey_edit = QLineEdit(self.config.get("hotkey"))
        
        layout.addRow("Default Language:", self.lang_combo)
        layout.addRow("Dictation Hotkey:", self.hotkey_edit)
        
        widget.setLayout(layout)
        return widget

    def create_api_tab(self):
        widget = QWidget()
        self.api_layout = QFormLayout()

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["deepgram", "whisper_live"])
        self.engine_combo.setCurrentText(self.config.get("transcription_engine", "deepgram"))
        self.engine_combo.currentTextChanged.connect(self.on_engine_change)
        self.api_layout.addRow("Transcription Engine:", self.engine_combo)

        self.deepgram_api_key_label = QLabel("Deepgram API Key:")
        self.api_key_edit = QLineEdit(self.config.get("api_key"))
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_layout.addRow(self.deepgram_api_key_label, self.api_key_edit)

        self.deepgram_model_label = QLabel("Deepgram Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["nova-3", "nova-2", "enhanced"])
        self.model_combo.setCurrentText(self.config.get("model"))
        self.api_layout.addRow(self.deepgram_model_label, self.model_combo)

        self.whisper_host_label = QLabel("Whisper Host:")
        self.whisper_host_edit = QLineEdit(self.config.get("whisper_host", "localhost"))
        self.api_layout.addRow(self.whisper_host_label, self.whisper_host_edit)

        self.whisper_port_label = QLabel("Whisper Port:")
        self.whisper_port_edit = QLineEdit(str(self.config.get("whisper_port", 9090)))
        self.api_layout.addRow(self.whisper_port_label, self.whisper_port_edit)
        
        self.whisper_model_label = QLabel("Whisper Model:")
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.whisper_model_combo.setCurrentText(self.config.get("whisper_model", "small"))
        self.api_layout.addRow(self.whisper_model_label, self.whisper_model_combo)

        widget.setLayout(self.api_layout)
        self.on_engine_change(self.engine_combo.currentText())
        return widget

    def on_engine_change(self, engine):
        is_deepgram = (engine == "deepgram")
        self.deepgram_api_key_label.setVisible(is_deepgram)
        self.api_key_edit.setVisible(is_deepgram)
        self.deepgram_model_label.setVisible(is_deepgram)
        self.model_combo.setVisible(is_deepgram)

        is_whisper = (engine == "whisper_live")
        self.whisper_host_label.setVisible(is_whisper)
        self.whisper_host_edit.setVisible(is_whisper)
        self.whisper_port_label.setVisible(is_whisper)
        self.whisper_port_edit.setVisible(is_whisper)
        self.whisper_model_label.setVisible(is_whisper)
        self.whisper_model_combo.setVisible(is_whisper)

    def create_exclusions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Exclusions (one per line):"))
        self.exclusions_edit = QTextEdit()
        self.exclusions_edit.setPlainText("\n".join(self.config.get("exclusions")))
        layout.addWidget(self.exclusions_edit)
        widget.setLayout(layout)
        return widget

    def create_commands_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Commands (Keyword: Action):"))
        self.commands_edit = QTextEdit()
        commands_str = "\n".join([f"{k}: {v}" for k, v in self.config.get("commands").items()])
        self.commands_edit.setPlainText(commands_str)
        layout.addWidget(self.commands_edit)
        widget.setLayout(layout)
        return widget

    def save_settings(self):
        try:
            port = int(self.whisper_port_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "The port must be a number.")
            return

        self.config.set("language", self.lang_combo.currentText())
        self.config.set("hotkey", self.hotkey_edit.text())

        self.config.set("transcription_engine", self.engine_combo.currentText())
        self.config.set("api_key", self.api_key_edit.text())
        self.config.set("model", self.model_combo.currentText())
        self.config.set("whisper_host", self.whisper_host_edit.text())
        self.config.set("whisper_port", port)
        self.config.set("whisper_model", self.whisper_model_combo.currentText())

        exclusions = [l.strip() for l in self.exclusions_edit.toPlainText().split("\n") if l.strip()]
        self.config.set("exclusions", exclusions)
        
        commands = {}
        for line in self.commands_edit.toPlainText().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                commands[k.strip()] = v.strip().replace("\\n", "\n")
        self.config.set("commands", commands)
        
        self.config.save()
        self.close()
