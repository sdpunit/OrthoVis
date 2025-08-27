# frontend_pages/registration/registration_window.py

from PySide6.QtCore import Qt, Signal, QSignalBlocker, QEvent
from PySide6.QtGui import QSurfaceFormat, QVector3D, QQuaternion
from PySide6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout

from frontend_pages.registration.ui_registration_window import Ui_Form

# VTK
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk


# --------------------------
#  Low-level VTK viewport
# --------------------------
class VTKView(QWidget):
    # def setup_camera(self, fov=45.0, aspect=16/9, near=0.1, far=1000, position=(0,0,10), view_center=(0,0,0)):
    #     camera = self.renderer.GetActiveCamera()
    #     camera.SetViewAngle(fov)
    #     camera.SetClippingRange(near, far)
    #     camera.SetPosition(*position)
    #     camera.SetFocalPoint(*view_center)
    #     self.renderer.ResetCameraClippingRange()
    #     self.render_window.Render()
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
        self.iren.setMouseTracking(True)
        # Move the ACTOR with the mouse so pose actually changes:
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballActor())
        # Picker required for TrackballActor:
        self.picker = vtk.vtkPropPicker()
        self.iren.SetPicker(self.picker)

        self.renderer.SetBackground(*bg)
        self.actor = None

        # axes marker
        self._axes_widget = None
        self._axes_actor = None
        self._axes_follow = "actor"

        # Emit pose while user interacts
        self.iren.AddObserver(vtk.vtkCommand.InteractionEvent, self._on_interaction)
        self.iren.AddObserver(vtk.vtkCommand.EndInteractionEvent, self._on_interaction)
    # self.iren.AddObserver("LeftButtonPressEvent", self.mousePressEvent)  # Removed: VTK event does not have .pos()

        self.iren.Initialize()
        self.last_mouse_pos = None

        # self.setup_camera()

        # Install event filter after initialization
        self.vtk.installEventFilter(self)

    def eventFilter(self, obj, event):
        # Intercept mouse events from QVTKRenderWindowInteractor
        if obj == self.vtk:
            if event.type() == QEvent.MouseButtonPress:
                self.last_mouse_pos = event.pos()
                print(self.last_mouse_pos)
                return True
            
            if event.type() == QEvent.MouseMove:
                if self.last_mouse_pos is None:
                    return False
                dx = event.x() - self.last_mouse_pos.x()
                dy = event.y() - self.last_mouse_pos.y()
                self.last_mouse_pos = event.pos()
                if self.actor:
                    if event.modifiers() & Qt.ControlModifier:
                        # Rotate with Ctrl
                        rx, ry, rz = self.actor.GetOrientation()
                        sensitivity = 0.1
                        self.set_actor_rotation_euler(rx + dy*sensitivity, ry + dx*sensitivity, rz)
                    else:
                        # Translate with drag
                        x, y, z = self.actor.GetPosition()
                        sensitivity = 0.001
                        self.set_actor_translation(x + dx * sensitivity, y - dy * sensitivity, z)
                return True
            if event.type() == QEvent.Wheel:
                print("scroll")
                if self.actor:
                    x, y, z = self.actor.GetPosition()
                    sensitivity = 0.1
                    delta = event.angleDelta().y() / 120
                    # Scroll up: move closer (increase Z), scroll down: move away (decrease Z)
                    self.set_actor_translation(x, y, z + delta * sensitivity)
                return True
            
            if event.type() == QEvent.MouseButtonRelease:
                self.last_mouse_pos = None
                return True
            
        return super().eventFilter(obj, event)

    # --- Methods to handle mouse events   
    # def mousePressEvent(self, *args):
    #     print("mouse press")
    #     event = args[0]
    #     self.last_mouse_pos = event.pos()
    #     super().mousePressEvent(event)

    # def mouseMoveEvent(self, event):
    #     if self.last_mouse_pos is None:
    #         return

    #     dx = event.x() - self.last_mouse_pos.x()
    #     dy = event.y() - self.last_mouse_pos.y()
    #     self.last_mouse_pos = event.pos()

    #     # Rotate with Ctrl
    #     if event.modifiers() & Qt.ControlModifier:
    #         print("press + ctrl")
    #         current_rot = self.transform.rotation()
    #         rot_x = QQuaternion.fromAxisAndAngle(QVector3D(1, 0, 0), dy)
    #         rot_y = QQuaternion.fromAxisAndAngle(QVector3D(0, 1, 0), dx)
    #         # self.view.set_actor_rotation_euler(rot_x, rot_y, current_rot.z())
    #         self.transform.setRotation(rot_x * rot_y * current_rot)

    #     # Translate with Shift
    #     else:
    #         print("drag")
    #         current_translation = self.transform.translation()
    #         # Adjust sensitivity as needed
    #         sensitivity = 0.01
    #         new_translation = QVector3D(
    #             current_translation.x() + dx * sensitivity,
    #             current_translation.y() - dy * sensitivity,  # invert Y
    #             current_translation.z()
    #         )
    #         tx = current_translation.x() + dx * sensitivity
    #         ty = current_translation.y() - dy * sensitivity
    #         # self.view.set_actor_translation(tx, ty, current_translation.z())
    #         self.transform.setTranslation(new_translation)

    #     super().mouseMoveEvent(event)

    # def wheelEvent(self, event):
    #     # Get current translation
    #     current_translation = self.transform.translation()
    #     print("scroll")
        
    #     # Adjust sensitivity
    #     sensitivity = 0.5
        
    #     # Delta from the wheel event (positive = scroll up, negative = scroll down)
    #     delta = event.angleDelta().y() / 120  # 1 step = 120 units
        
    #     # Update Z position
    #     new_translation = QVector3D(
    #         current_translation.x(),
    #         current_translation.y(),
    #         current_translation.z() - delta * sensitivity  # subtract to zoom in
    #     )
    #     # tz = current_translation.z() - delta * sensitivity
    #     # self.view.set_actor_translation(current_translation.x(), current_translation.y(), tz)
    #     self.transform.setTranslation(new_translation)

    # def mouseReleaseEvent(self, a0):
        self.last_mouse_pos = None
        super().mouseReleaseEvent(a0)

    # ---- Public helpers -------------------------------------------------
    def add_cube(self, size, color=(0.27, 0.51, 0.71)):
        cube = vtk.vtkCubeSource()
        cube.SetXLength(size); cube.SetYLength(size); cube.SetZLength(size)
        mapper = vtk.vtkPolyDataMapper(); mapper.SetInputConnection(cube.GetOutputPort())
        actor = vtk.vtkActor(); actor.SetMapper(mapper); actor.GetProperty().SetColor(*color)
        actor.PickableOn()
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.actor = actor
        self._emit_pose()              # sync axes first
        self.render_window.Render()    # then render


        return actor    

    def set_background(self, r, g, b):
        self.renderer.SetBackground(r, g, b); self.render_window.Render()

    def reset_camera(self):
        self.renderer.ResetCamera(); self.render_window.Render()

    def set_actor_translation(self, x=0.0, y=0.0, z=0.0):
        if not self.actor: return
        self.actor.SetPosition(x, y, z)
        self.renderer.ResetCameraClippingRange()
        self._emit_pose()              # sync axes first
        self.render_window.Render()    # then render

    def set_actor_rotation_euler(self, rx_deg=0.0, ry_deg=0.0, rz_deg=0.0):
        if not self.actor: return
        self.actor.SetOrientation(rx_deg, ry_deg, rz_deg)
        self.renderer.ResetCameraClippingRange()
        self._emit_pose()              # sync axes first
        self.render_window.Render()    # then render

    def add_axes_widget(self, size=0.15, follow="actor"):
        if self._axes_widget:
            self._axes_follow = follow
            return self._axes_widget

        axes = vtk.vtkAxesActor()
        widget = vtk.vtkOrientationMarkerWidget()
        widget.SetOrientationMarker(axes)
        widget.SetInteractor(self.iren)
        widget.SetViewport(0.0, 0.0, size, size)
        widget.SetEnabled(1)
        widget.InteractiveOff()

        self._axes_widget = widget
        self._axes_actor = axes
        self._axes_follow = follow
        self.render_window.Render()
        return widget

    def clear(self):
        self.renderer.RemoveAllViewProps()
        self.actor = None
        self.render_window.Render()
        self._emit_pose()

    # ---------- internal ----------
    def _on_interaction(self, *_):
        # while dragging: keep marker in lockstep and render
        self._sync_axes_to_actor_matrix()
        self.render_window.Render()
        self._emit_pose()

    def _emit_pose(self):
        if not self.actor:
            return
        # keep marker aligned (also used for programmatic changes)
        self._sync_axes_to_actor_matrix()

        x, y, z = self.actor.GetPosition()
        rx, ry, rz = self.actor.GetOrientation()
        self.poseChanged.emit(x, y, z, rx, ry, rz)

    def _sync_axes_to_actor_matrix(self):
        """Copy the actor's rotation into the corner axes (translation removed)."""
        if not (self._axes_widget and self._axes_actor and self._axes_follow == "actor" and self.actor):
            return
        m = vtk.vtkMatrix4x4()
        self.actor.GetMatrix(m)

        # zero translation so the corner marker doesn't drift
        m.SetElement(0, 3, 0.0)
        m.SetElement(1, 3, 0.0)
        m.SetElement(2, 3, 0.0)
        m.SetElement(3, 0, 0.0); m.SetElement(3, 1, 0.0); m.SetElement(3, 2, 0.0); m.SetElement(3, 3, 1.0)

        t = vtk.vtkTransform()
        t.SetMatrix(m)
        self._axes_actor.SetUserTransform(t)
        self._axes_actor.Modified()



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
        self.view.add_axes_widget(size=0.18, follow="actor")
        self.view.reset_camera()

        # input fields trigger actor live updates
        self.ui.pos_x.textChanged.connect(self._on_pos_changed)
        self.ui.pos_y.textChanged.connect(self._on_pos_changed)
        self.ui.pos_z.textChanged.connect(self._on_pos_changed)
        self.ui.rotation_x.textChanged.connect(self._on_rot_changed)
        self.ui.rotation_y.textChanged.connect(self._on_rot_changed)
        self.ui.rotation_z.textChanged.connect(self._on_rot_changed)

        # actor/camera interaction -> fields live updates
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
            with QSignalBlocker(w):
                w.setText(val)

    # move actor when fields change
    def _on_pos_changed(self):
        try:
            x = 0.1* float(self.ui.pos_x.text())
            y = 0.1* float(self.ui.pos_y.text())
            z = 0.1* float(self.ui.pos_z.text())
        except ValueError:
            return
        self.view.set_actor_translation(x, y, z)

    def _on_rot_changed(self):
        try:
            rx = 0.1* float(self.ui.rotation_x.text())
            ry = 0.1* float(self.ui.rotation_y.text())
            rz = 0.1* float(self.ui.rotation_z.text())
        except ValueError:
            return
        self.view.set_actor_rotation_euler(rx, ry, rz)