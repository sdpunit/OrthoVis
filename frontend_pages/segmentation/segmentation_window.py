from PySide6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsProxyWidget
from frontend_pages.segmentation.ui_segmentation_window import Ui_Form

# Use the native Qt6 VTK widget (more stable on macOS)
# from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
# from vtkmodules.vtkRenderingOpenGL2 import vtkGenericOpenGLRenderWindow
# from vtkmodules.vtkRenderingCore import vtkRenderer

import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from frontend_pages.segmentation.vtk_window import VTKWidget


class Segmentation(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.titlebar.ui.title.setText("Segmentation")

        self.ui.sidebar.ui.segmentation.setStyleSheet(
        """
            QPushButton { 
                color: white; 
                background-color: #6f8ab7; 
                border: none; 
                padding: 10px 25px;  
                text-align: center;}
        """
        )




    
