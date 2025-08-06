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

        self.ui.calibration.clicked.connect(self.select_calibration)
        self.ui.define_axis.clicked.connect(self.select_define_axis)
        self.ui.registration.clicked.connect(self.select_registration)
        self.ui.visualisation.clicked.connect(self.select_visualisation)

    def select_project_setup(self):
        print(self.parent().parent())
        self.parent().parent().setCurrentIndex(1)

    def select_segmentation(self):
        self.parent().parent().setCurrentIndex(2)

    def select_calibration(self):
        self.parent().parent().setCurrentIndex(3)

    def select_define_axis(self):
        self.parent().parent().setCurrentIndex(4)

    def select_registration(self):
        self.parent().parent().setCurrentIndex(5)

    def select_visualisation(self):
        self.parent().parent().setCurrentIndex(6)
