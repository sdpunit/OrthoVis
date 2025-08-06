from PySide6.QtWidgets import QWidget
from frontend_pages.segmentation.ui_segmentation_window import Ui_Form

# Use the native Qt6 VTK widget (more stable on macOS)
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingOpenGL2 import vtkGenericOpenGLRenderWindow
from vtkmodules.vtkRenderingCore import vtkRenderer


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

        # --- Replace 'VTK_display' placeholder with a VTK native widget ---
        placeholder = self.ui.VTK_display
        parent_layout = placeholder.parentWidget().layout()
        idx = parent_layout.indexOf(placeholder)
        left_stretch = parent_layout.stretch(idx)

        parent_layout.removeWidget(placeholder)
        # placeholder.deleteLater()

        # Native widget (no Initialize/Start needed)
        self.vtk_widget = QVTKRenderWindowInteractor(self.ui.mainpanel)
        self.vtk_widget.setStyleSheet("background-color: black;")
        self.vtk_widget.setAutoFillBackground(True)
        parent_layout.insertWidget(idx, self.vtk_widget)
        if left_stretch is not None:
            parent_layout.setStretch(idx, left_stretch)

        # Minimal VTK scene hook-up
        rw = vtkGenericOpenGLRenderWindow()
        self.vtk_widget.SetRenderWindow(rw)

        ren = vtkRenderer()
        ren.SetBackground(0.0, 0.0, 0.0)
        ren.SetBackgroundAlpha(1.0)
        rw.SetAlphaBitPlanes(0)
        rw.AddRenderer(ren)

        # Keep a ref if you’ll add actors later
        self.renderer = ren
