# This file can open pop up for importing both CT and Fluroscopy
from PySide6.QtWidgets import QWidget
from frontend_pages.project_setup.ui_project_setup_window import Ui_Form

name = ""

class ProjectSetup(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.titlebar.ui.title.setText("Project Setup")
        self.ui.projectNameInput.setText(name)
        
        self.ui.sidebar.ui.project_setup.setStyleSheet(
        """
            QPushButton { 
                color: white; 
                background-color: #6f8ab7; 
                border: none; 
                padding: 10px 25px;  
                text-align: center;}
        """
        )
    
    

    def changeName(self, new_name):
        name = new_name
        self.ui.projectNameInput.setText(name)
