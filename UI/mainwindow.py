from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog
from UI.canvas import Canvas, CanvasMode
import json

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
        
        self.json_files = []
        
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
    
    def load_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose a JSON file", "", "JSON Files (*.json)")
        self.json_path = file_path
        if file_path:
            self.json_files = [file_path]
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.canvas.load_json(data)
            
    def save(self):
        if self.json_path:
            json_data = self.canvas.save()
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)