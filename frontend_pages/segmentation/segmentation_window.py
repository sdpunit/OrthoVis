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

    def main(img):
        #img = cache_ct(ct_path)
        vtk_img, arr = sitk_to_vtk(img)

        render_window = vtkRenderWindow()
        render_window.SetAlphaBitPlanes(1)
        render_window.SetSize(900, 900)
        render_window.SetNumberOfLayers(3)

        # Define quadrants (axial, coronal, sagittal)
        quads = {
            'Axial':    (0.0, 0.5, 0.5, 1.0),
            'Coronal':  (0.0, 0.0, 0.5, 0.5),
            'Sagittal': (0.5, 0.0, 1.0, 0.5)
        }

        # Create viewers for each quadrant
        viewers = []
        for name, vp in quads.items():
            sv = SliceViewer(vtk_img, arr, name.lower(), vp, name, render_window)
            viewers.append(sv)

        # Create interactor and style
        interactor = vtkRenderWindowInteractor()
        interactor.SetRenderWindow(render_window)
        interactor.SetInteractorStyle(QuadStyle(viewers))


        # Reset each camera so the slice fills the quadrant
        for sv in viewers:
            ren = sv.viewer.GetRenderer()
            ren.ResetCamera()             # zoom so image fills viewport
            ren.ResetCameraClippingRange()
            cam = ren.GetActiveCamera()
            cam.Zoom(1.4)

        # Window/Level sliders on right (in their own layer)
        slider_renderer = vtkRenderer()
        slider_renderer.SetLayer(2)
        slider_renderer.InteractiveOff()
        slider_renderer.SetViewport(0.0, 0.0, 1.0, 1.0)
        render_window.AddRenderer(slider_renderer)

        hu_min, hu_max = int(arr.min()), int(arr.max())
        win_rep = make_slider(1, hu_max - hu_min, hu_max - hu_min, 0.97)
        lvl_rep = make_slider(hu_min, hu_max, (hu_max + hu_min)//2, 0.94)

        win_wid = vtk.vtkSliderWidget()
        lvl_wid = vtk.vtkSliderWidget()

        def wl_callback(obj, event):
            w = int(round(win_rep.GetValue()))
            l = int(round(lvl_rep.GetValue()))
            for sv in viewers:
                sv.viewer.SetColorWindow(w)
                sv.viewer.SetColorLevel(l)
            render_window.Render()

        for wid, rep in ((win_wid, win_rep), (lvl_wid, lvl_rep)):
            wid.SetInteractor(interactor)
            wid.SetRepresentation(rep)
            wid.SetAnimationModeToJump()
            wid.SetCurrentRenderer(slider_renderer)
            # strip out VTK’s incremental redraws
            wid.RemoveObservers("StartInteractionEvent")
            wid.RemoveObservers("InteractionEvent")
            wid.RemoveObservers("EndInteractionEvent")
            # attach only our full-render callback
            wid.AddObserver("InteractionEvent", wl_callback)
            wid.EnabledOn()

        # Add "W" and "L" text actors above each slider
        for label, xpos in (("L", 0.937), ("W", 0.967)):
            txt = vtkTextActor()
            txt.SetInput(label)
            tp = txt.GetTextProperty()
            tp.SetFontSize(16)
            tp.BoldOn()
            tp.SetColor(1, 1, 1)
            coord = txt.GetPositionCoordinate()
            coord.SetCoordinateSystemToNormalizedDisplay()
            coord.SetValue(xpos, 0.335) 
            slider_renderer.AddActor2D(txt)

        # Start interaction
        render_window.Render()
        interactor.Initialize()
        interactor.Start()

