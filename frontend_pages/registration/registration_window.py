# frontend_pages/registration/registration_window.py

from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout

from frontend_pages.registration.ui_registration_window import Ui_Form

# VTK
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk


# --------------------------
#  Low-level VTK viewport
# --------------------------
class VTKView(QWidget):
    """Reusable VTK viewport; emits poseChanged(x,y,z, rx,ry,rz) for the primary actor."""
    poseChanged = Signal(float, float, float, float, float, float)

    def __init__(self, parent=None, bg=(0.10, 0.12, 0.14)):
        super().__init__(parent)
        try:
            QSurfaceFormat.setDefaultFormat(QVTKRenderWindowInteractor.defaultFormat())
        except Exception:
            pass

        self.vtk = QVTKRenderWindowInteractor(self)
        self.vtk.setObjectName("vtkInteractor")
        self.vtk.setFocusPolicy(Qt.StrongFocus)
        self.vtk.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.vtk)

        self.render_window = self.vtk.GetRenderWindow()
        self.renderer = vtk.vtkRenderer()
        self.render_window.AddRenderer(self.renderer)

        self.iren = self.vtk
        # Move the ACTOR with the mouse so pose actually changes:
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballActor())
        # Picker required for TrackballActor:
        self.picker = vtk.vtkPropPicker()
        self.iren.SetPicker(self.picker)

        self.renderer.SetBackground(*bg)
        self.actor = None
        self._axes_widget = None

        # Emit pose while user interacts
        self.iren.AddObserver(vtk.vtkCommand.InteractionEvent, self._on_interaction)
        self.iren.AddObserver(vtk.vtkCommand.EndInteractionEvent, self._on_interaction)

        self.iren.Initialize()

    # ---- Public helpers -------------------------------------------------
    def add_cube(self, size=1.0, color=(0.27, 0.51, 0.71)):
        cube = vtk.vtkCubeSource()
        cube.SetXLength(size); cube.SetYLength(size); cube.SetZLength(size)
        mapper = vtk.vtkPolyDataMapper(); mapper.SetInputConnection(cube.GetOutputPort())
        actor = vtk.vtkActor(); actor.SetMapper(mapper); actor.GetProperty().SetColor(*color)
        actor.PickableOn()
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.actor = actor
        self.render_window.Render()
        self._emit_pose()  # publish initial pose
        return actor

    def set_background(self, r, g, b):
        self.renderer.SetBackground(r, g, b); self.render_window.Render()

    def reset_camera(self):
        self.renderer.ResetCamera(); self.render_window.Render()

    def set_actor_translation(self, x=0.0, y=0.0, z=0.0):
        if not self.actor: return
        self.actor.SetPosition(x, y, z); self.render_window.Render(); self._emit_pose()

    def set_actor_rotation_euler(self, rx_deg=0.0, ry_deg=0.0, rz_deg=0.0):
        if not self.actor: return
        self.actor.SetOrientation(rx_deg, ry_deg, rz_deg); self.render_window.Render(); self._emit_pose()

    def add_axes_widget(self, size=0.15):
        if self._axes_widget: return self._axes_widget
        axes = vtk.vtkAxesActor()
        widget = vtk.vtkOrientationMarkerWidget()
        widget.SetOrientationMarker(axes)
        widget.SetInteractor(self.iren)
        widget.SetViewport(0.0, 0.0, size, size)
        widget.SetEnabled(1)
        widget.InteractiveOff()
        self._axes_widget = widget
        self.render_window.Render()
        return widget

    def clear(self):
        self.renderer.RemoveAllViewProps()
        self.actor = None
        self.render_window.Render()
        self._emit_pose()

    # internal: publish pose on interaction
    def _on_interaction(self, *_):
        self._emit_pose()

    def _emit_pose(self):
        if not self.actor: return
        x, y, z = self.actor.GetPosition()
        rx, ry, rz = self.actor.GetOrientation()
        self.poseChanged.emit(x, y, z, rx, ry, rz)


# --------------------------
#  Registration widget
# --------------------------
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

        # Swap placeholder with our VTKView
        self.view = VTKView(self.ui.mainpanel, bg=(0.10, 0.12, 0.14))
        self.ui.horizontalLayout_2.replaceWidget(self.ui.VTK_display, self.view)
        self.ui.VTK_display.setParent(None); self.ui.VTK_display.deleteLater()

        # Scene
        self.view.add_cube(size=0.5, color=(0.27, 0.51, 0.71))
        self.view.add_axes_widget(size=0.18)
        self.view.reset_camera()

        # input fields trigger actor live updates
        self.ui.pos_x.textChanged.connect(self._on_pos_changed)
        self.ui.pos_y.textChanged.connect(self._on_pos_changed)
        self.ui.pos_z.textChanged.connect(self._on_pos_changed)
        self.ui.rotation_x.textChanged.connect(self._on_rot_changed)
        self.ui.rotation_y.textChanged.connect(self._on_rot_changed)
        self.ui.rotation_z.textChanged.connect(self._on_rot_changed)

        # ---- actor/camera interaction -> fields live updates
        self.view.poseChanged.connect(self._update_fields_from_pose)

        # Seed UI with initial pose
        x, y, z = self.view.actor.GetPosition()
        rx, ry, rz = self.view.actor.GetOrientation()
        self._update_fields_from_pose(x, y, z, rx, ry, rz)

    # update fields when the actor moves in the view
    def _update_fields_from_pose(self, x, y, z, rx, ry, rz):
        pairs = [
            (self.ui.pos_x,      f"{x:.3f}"),
            (self.ui.pos_y,      f"{y:.3f}"),
            (self.ui.pos_z,      f"{z:.3f}"),
            (self.ui.rotation_x, f"{rx:.2f}"),
            (self.ui.rotation_y, f"{ry:.2f}"),
            (self.ui.rotation_z, f"{rz:.2f}"),
        ]
        for w, val in pairs:
            with QSignalBlocker(w):  # avoid feedback loops
                w.setText(val)

    # ---- move actor when fields change
    def _on_pos_changed(self):
        try:
            x = float(self.ui.pos_x.text())
            y = float(self.ui.pos_y.text())
            z = float(self.ui.pos_z.text())
        except ValueError:
            return
        self.view.set_actor_translation(x, y, z)

    def _on_rot_changed(self):
        try:
            rx = float(self.ui.rotation_x.text())
            ry = float(self.ui.rotation_y.text())
            rz = float(self.ui.rotation_z.text())
        except ValueError:
            return
        self.view.set_actor_rotation_euler(rx, ry, rz)