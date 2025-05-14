# Startup window on opening of the application
from PySide6.QtWidgets import QMainWindow
from frontend_pages.ui_startup_window import Ui_MainWindow as Ui_HomePage

class HomePage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_HomePage()
        self.ui.setupUi(self)