# This file can open pop up for importing both CT and Fluroscopy
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QFileDialog
from frontend_pages.new_project.ui_new_project_window import Ui_Form

class NewProject(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.titlebar.ui.title.setText("New Project")
        # self.ui.pushButton.clicked.connect(self.importCT)
        # self.ui.pushButton_2.clicked.connect(self.importFluoro)

    
    def importCT(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select the CT sequence folder (e.g. SE000000)"
        )
    def importFluoro(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select the CT sequence folder (e.g. SE000000)"
        )