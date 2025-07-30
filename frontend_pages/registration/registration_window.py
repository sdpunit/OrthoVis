# Shows imported ct file in 3 views? 
# allows for the segmentation of the previously imported CT.
from PySide6.QtWidgets import QWidget
from frontend_pages.registration.ui_registration_window import Ui_Form

class Registration(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.titlebar.ui.title.setText("Registration")

        self.ui.sidebar.ui.registration.setStyleSheet(
        """
            QPushButton { 
                color: white; 
                background-color: #6f8ab7; 
                border: none; 
                padding: 10px 25px;  
                text-align: center;}
        """
        )