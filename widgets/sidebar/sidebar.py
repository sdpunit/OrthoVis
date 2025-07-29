from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize
from widgets.sidebar.ui_sidebar import Ui_Form

class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.logo.setPixmap(QPixmap("assets/logo_small.png"))

        self.ui.project_setup.clicked.connect(self.select_project_setup)
        self.ui.segmentation.clicked.connect(self.select_segmentation)
        

    def select_project_setup(self):
        print(self.parent().parent())
        self.parent().parent().setCurrentIndex(1)

    def select_segmentation(self):
        self.parent().parent().setCurrentIndex(2)
