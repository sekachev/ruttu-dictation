from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QTextEdit, QFormLayout, QHBoxLayout)
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
        
        # Tab 1: General
        self.tabs.addTab(self.create_general_tab(), "General")
        
        # Tab 2: API & Engine
        self.tabs.addTab(self.create_api_tab(), "API & Engine")
        
        # Tab 3: Exclusions
        self.tabs.addTab(self.create_exclusions_tab(), "Exclusions")
        
        # Tab 4: Commands
        self.tabs.addTab(self.create_commands_tab(), "Commands")
        
        layout.addWidget(self.tabs)
        
        # Save Button
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
        layout = QFormLayout()
        
        self.api_key_edit = QLineEdit(self.config.get("api_key"))
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["nova-3", "nova-2", "enhanced"])
        self.model_combo.setCurrentText(self.config.get("model"))
        
        layout.addRow("Deepgram API Key:", self.api_key_edit)
        layout.addRow("Model Engine:", self.model_combo)
        
        widget.setLayout(layout)
        return widget

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
        self.config.set("language", self.lang_combo.currentText())
        self.config.set("hotkey", self.hotkey_edit.text())
        self.config.set("api_key", self.api_key_edit.text())
        self.config.set("model", self.model_combo.currentText())
        
        # Parse text areas
        exclusions = [l.strip() for l in self.exclusions_edit.toPlainText().split("\n") if l.strip()]
        self.config.set("exclusions", exclusions)
        
        # Simple command parsing
        commands = {}
        for line in self.commands_edit.toPlainText().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                commands[k.strip()] = v.strip().replace("\\n", "\n")
        self.config.set("commands", commands)
        
        self.config.save()
        self.close()
