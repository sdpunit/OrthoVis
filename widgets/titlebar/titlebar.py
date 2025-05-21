from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from widgets.titlebar.ui_titlebar import Ui_TitleBar

class Titlebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TitleBar()
        self.ui.setupUi(self)