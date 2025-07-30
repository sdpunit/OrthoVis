# Shows imported ct file in 3 views? 
# allows for the segmentation of the previously imported CT.
from PySide6.QtWidgets import QWidget
from frontend_pages.visualisation.ui_visualisation_window import Ui_Form

class Visualisation(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.titlebar.ui.title.setText("Visualisation")

        self.ui.sidebar.ui.visualisation.setStyleSheet(
        """
            QPushButton { 
                color: white; 
                background-color: #6f8ab7; 
                border: none; 
                padding: 10px 25px;  
                text-align: center;}
        """
        )