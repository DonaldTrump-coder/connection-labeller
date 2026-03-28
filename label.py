from PyQt6.QtWidgets import QApplication
import sys
from UI.mainwindow import MainWindow

def main():
    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()