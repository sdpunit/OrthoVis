# Startup window on opening of the application
from PySide6.QtWidgets import QWidget
from frontend_pages.startup.ui_startup_window import Ui_HomePage

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_HomePage()
        self.ui.setupUi(self)