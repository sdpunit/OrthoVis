# This file can open pop up for importing both CT and Fluroscopy
from PySide6.QtWidgets import QWidget
from frontend_pages.new_project.ui_new_project_window import Ui_Form

class NewProject(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.widget.ui.label.setText("new project sidebar")