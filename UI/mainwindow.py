from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QStatusBar
from UI.canvas import Canvas, CanvasMode
import json
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connection Labeller")
        self.resize(1100, 700)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)
        
        self.tool_panel = self.create_tool_panel()
        self.canvas = Canvas()
        
        layout.addWidget(self.tool_panel)
        layout.addWidget(self.canvas)
        
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        self.json_files = []
        self.index = 0
        self.update_status()
        
        self.saved = False
        
    def create_tool_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        load_button = QPushButton("Load Label")
        load_folder_button = QPushButton("Load Folder")
        next_button = QPushButton("Next")
        last_button = QPushButton("Last")
        btn_select = QPushButton("Move")
        btn_connect = QPushButton("Connect")
        delete_button = QPushButton("Delete")
        save_button = QPushButton("Save")
        
        load_button.clicked.connect(self.load_json)
        load_folder_button.clicked.connect(self.load_folder)
        next_button.clicked.connect(self.load_next)
        last_button.clicked.connect(self.load_last)
        btn_select.clicked.connect(self.set_move)
        btn_connect.clicked.connect(self.set_connect)
        delete_button.clicked.connect(self.set_delete)
        save_button.clicked.connect(self.save)
        
        layout.addWidget(load_button)
        layout.addWidget(load_folder_button)
        layout.addWidget(next_button)
        layout.addWidget(last_button)
        layout.addWidget(btn_select)
        layout.addWidget(btn_connect)
        layout.addWidget(delete_button)
        layout.addWidget(save_button)
        
        layout.addStretch()
        return panel
    
    def set_move(self):
        self.canvas.set_mode(CanvasMode.Move)
        
    def set_connect(self):
        self.canvas.set_mode(CanvasMode.Connect)
        
    def set_delete(self):
        self.canvas.set_mode(CanvasMode.Delete)
        
    def load_folder(self):
        if self.canvas.edges and self.saved is False:
            QMessageBox.warning(self, "Warning", "Haven't saved!")
            return
        folder_path = QFileDialog.getExistingDirectory(self, "Choose a Folder")
        if not folder_path:
            return
        
        self.index = 0
        self.json_files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(".json")
        ]
        self.json_files.sort()
        
        num_files = len(self.json_files)
        if num_files == 0:
            QMessageBox.warning(self, "Warning", "No JSON files found in the folder!")
            return
        with open(self.json_files[self.index], 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.canvas.load_json(data)
        self.saved = False
        self.update_status()
        
    def load_next(self):
        if not self.json_files:
            return
        if self.canvas.edges and self.saved is False:
            QMessageBox.warning(self, "Warning", "Haven't saved!")
            return
        if self.index < len(self.json_files) - 1:
            self.index += 1
        else:
            QMessageBox.warning(self, "Warning", "No more files!")
            return
        with open(self.json_files[self.index], 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.canvas.load_json(data)
        self.saved = False
        self.update_status()
        
    def load_last(self):
        if not self.json_files:
            return
        if self.canvas.edges and self.saved is False:
            QMessageBox.warning(self, "Warning", "Haven't saved!")
            return
        if self.index > 0:
            self.index -= 1
        else:
            QMessageBox.warning(self, "Warning", "No previous files!")
            return
        with open(self.json_files[self.index], 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.canvas.load_json(data)
        self.saved = False
        self.update_status()
    
    def load_json(self):
        if self.canvas.edges and self.saved is False:
            QMessageBox.warning(self, "Warning", "Haven't saved!")
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose a JSON file", "", "JSON Files (*.json)")
        self.index = 0
        if file_path:
            self.json_files = [file_path]
            with open(self.json_files[self.index], 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.canvas.load_json(data)
            self.saved = False
            self.update_status()
            
    def update_status(self):
        if not self.json_files:
            text = f"Label 0 / 0"
        else:
            total = len(self.json_files)
            if self.index < total:
                text = f"Label {self.index + 1} / {total}"
        self.status.showMessage(text)
        
    def save(self):
        if not self.json_files:
            return
        if self.json_files[self.index]:
            json_data = self.canvas.save()
            if json_data == "Isolated point found!":
                QMessageBox.warning(self, "Warning", "Isolated point found!")
                return
            if json_data == "No connections!":
                QMessageBox.warning(self, "Warning", "No connections!")
                return
            with open(self.json_files[self.index], 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
                self.saved = True