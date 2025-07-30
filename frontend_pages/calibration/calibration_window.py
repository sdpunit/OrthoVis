# Shows imported ct file in 3 views? 
# allows for the segmentation of the previously imported CT.
from PySide6.QtWidgets import QWidget
from frontend_pages.calibration.ui_calibration_window import Ui_Form

class Calibration(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.titlebar.ui.title.setText("Calibration")

        self.ui.sidebar.ui.calibration.setStyleSheet(
        """
            QPushButton { 
                color: white; 
                background-color: #6f8ab7; 
                border: none; 
                padding: 10px 25px;  
                text-align: center;}
        """
        )