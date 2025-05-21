# Startup window on opening of the application
from PySide6.QtWidgets import QWidget
from frontend_pages.ui_startup_window import Ui_HomePage
from frontend_pages import new_project_window
import classes
class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_HomePage()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.handle_new_project)
        self.ui.pushButton.setToolTip("Create a new OrthoVis project with CT and Fluoroscopy data.")
        self.ui.pushButton_2.setToolTip("Open an existing OrthoVis project from your computer.")
        self.ui.pushButton.setStyleSheet("""
            QPushButton {
                background-color: rgb(255, 215, 0);
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgb(255, 230, 50);
                font-size: 18px;
            }
        """)
        self.ui.pushButton_2.setStyleSheet("""
                    QPushButton {
                        background-color: rgb(255, 215, 0);
                        border-radius: 10px;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: rgb(255, 230, 50);
                        font-size: 18px;
                    }
                """)
    def handle_new_project(self):
        # Jump to the new project page
        self.parent().setCurrentIndex(1)


