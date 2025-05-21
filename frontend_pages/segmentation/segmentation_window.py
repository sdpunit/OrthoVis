# Shows imported ct file in 3 views? 
# allows for the segmentation of the previously imported CT.
from PySide6.QtWidgets import QWidget
from frontend_pages.segmentation.ui_segmentation_window import Ui_Form

class Segmentation(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.titlebar.ui.title.setText("Segmentation")