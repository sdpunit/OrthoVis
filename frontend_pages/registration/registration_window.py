# frontend_pages/registration/registration_window.py

from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QLabel, QApplication

from frontend_pages.registration.ui_registration_window import Ui_Form
from classes.objects import SingletonPatient

import os
import numpy as np
import pydicom

# VTK
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk
from vtkmodules.vtkRenderingCore import vtkImageActor
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkIOImage import vtkImageImport


# --------------------------
#  Low-level VTK viewport
# --------------------------
class VTKView(QWidget):
    """Shows a 2D DICOM frame as background (via pydicom + vtkImageImport) and a 3D actor on top."""
    poseChanged = Signal(float, float, float, float, float, float)
    frameChanged = Signal(int, int)  # (current_index, total_frames)

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

        # Background renderer (layer 0) for the fluoroscopy frame
        self.bg_renderer = vtk.vtkRenderer()
        self.bg_renderer.SetLayer(0)
        self.bg_renderer.SetInteractive(0)

        # Foreground renderer (layer 1) for 3D content
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetLayer(1)
        self.renderer.SetBackground(*bg)

        self.render_window.SetNumberOfLayers(2)
        self.render_window.AddRenderer(self.bg_renderer)
        self.render_window.AddRenderer(self.renderer)

        # Interactor
        self.iren = self.vtk
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballActor())
        self.picker = vtk.vtkPropPicker()
        self.iren.SetPicker(self.picker)
        self.iren.AddObserver(vtk.vtkCommand.InteractionEvent, self._on_interaction)
        self.iren.AddObserver(vtk.vtkCommand.EndInteractionEvent, self._on_interaction)
        self.iren.Initialize()

        # --- custom wheel-to-Z handling ---
        self._wheel_step = 0.05  # adjust sensitivity
        self.iren.AddObserver("MouseWheelForwardEvent", self._on_wheel_forward, 1.0)
        self.iren.AddObserver("MouseWheelBackwardEvent", self._on_wheel_backward, 1.0)

        # 3D state
        self.actor = None
        self._axes_widget = None
        self._axes_actor = None
        self._axes_follow = "actor"

        # DICOM/frame state
        self._frames_u8: np.ndarray | None = None  # shape (N, H, W), uint8
        self._num_frames: int = 0
        self._frame: int = 0

        # VTK image pipeline (numpy -> importer -> window/level -> image actor)
        self._importer: vtkImageImport | None = None
        self._wl: vtkImageMapToWindowLevelColors | None = None
        self._bg_actor: vtkImageActor | None = None
        self._last_shape: tuple[int, int] | None = None  # (H, W)

    # ---------- wheel handlers ----------
    def _on_wheel_forward(self, caller, evt):
        if self.actor:
            x, y, z = self.actor.GetPosition()
            self.set_actor_translation(x, y, z + self._wheel_step)
            caller.SetAbortFlag(1)  # stop default zoom

    def _on_wheel_backward(self, caller, evt):
        if self.actor:
            x, y, z = self.actor.GetPosition()
            self.set_actor_translation(x, y, z - self._wheel_step)
            caller.SetAbortFlag(1)  # stop default zoom

    # ---------- DICOM ----------
    def _resolve_dicom_path(self, path: str) -> str:
        """Allow either a DICOM file or a folder with one file."""
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                p = os.path.join(path, name)
                if os.path.isfile(p):
                    try:
                        with open(p, "rb") as f:
                            f.seek(128)
                            if f.read(4) == b"DICM":
                                return p
                    except Exception:
                        pass
                    return p
            raise FileNotFoundError(f"No files in folder: {path}")
        return path

    def load_dicom(self, path: str):
        file_path = self._resolve_dicom_path(path)
        ds = pydicom.dcmread(file_path)
        arr = ds.pixel_array
        if arr.ndim == 2:
            arr = arr[np.newaxis, ...]
        slope = float(getattr(ds, "RescaleSlope", 1.0))
        intercept = float(getattr(ds, "RescaleIntercept", 0.0))
        arr = arr.astype(np.float32) * slope + intercept
        wc = getattr(ds, "WindowCenter", None)
        ww = getattr(ds, "WindowWidth", None)
        if wc is not None and ww is not None:
            wc = float(wc[0]) if hasattr(wc, "__getitem__") else float(wc)
            ww = float(ww[0]) if hasattr(ww, "__getitem__") else float(ww)
            low, high = wc - ww / 2, wc + ww / 2
            arr = np.clip(arr, low, high)
        min_v, max_v = float(arr.min()), float(arr.max())
        if max_v > min_v:
            arr = (arr - min_v) / (max_v - min_v) * 255.0
        else:
            arr[:] = 0.0
        frames_u8 = arr.astype(np.uint8)
        self._frames_u8 = frames_u8
        self._num_frames = frames_u8.shape[0]
        self._frame = 0
        self._ensure_bg_pipeline(frames_u8.shape[1], frames_u8.shape[2])
        self._push_frame_to_vtk(frames_u8[0])
        cam = self.bg_renderer.GetActiveCamera()
        cam.ParallelProjectionOn()
        self.bg_renderer.ResetCamera()
        self.render_window.Render()
        self.frameChanged.emit(self._frame, self._num_frames)

    def show_frame(self, index: int):
        if self._frames_u8 is None:
            return
        self._frame = max(0, min(index, self._num_frames - 1))
        self._push_frame_to_vtk(self._frames_u8[self._frame])
        self.bg_renderer.ResetCameraClippingRange()
        self.render_window.Render()
        self.frameChanged.emit(self._frame, self._num_frames)

    def step_frame(self, delta: int):
        if self._frames_u8 is None or self._num_frames <= 1:
            return
        new_idx = (self._frame + delta) % self._num_frames
        self.show_frame(new_idx)

    def _ensure_bg_pipeline(self, H: int, W: int):
        size_changed = (self._last_shape != (H, W))
        if self._importer is None or size_changed:
            if self._bg_actor:
                self.bg_renderer.RemoveActor(self._bg_actor)
            importer = vtk.vtkImageImport()
            importer.SetDataScalarTypeToUnsignedChar()
            importer.SetNumberOfScalarComponents(1)
            importer.SetWholeExtent(0, W - 1, 0, H - 1, 0, 0)
            importer.SetDataExtentToWholeExtent()
            wl = vtkImageMapToWindowLevelColors()
            wl.SetInputConnection(importer.GetOutputPort())
            wl.SetWindow(255.0)
            wl.SetLevel(127.5)
            actor = vtkImageActor()
            actor.GetMapper().SetInputConnection(wl.GetOutputPort())
            self._importer = importer
            self._wl = wl
            self._bg_actor = actor
            self.bg_renderer.AddActor(actor)
            self._last_shape = (H, W)

    def _push_frame_to_vtk(self, frame_u8_2d: np.ndarray):
        H, W = frame_u8_2d.shape
        if self._importer is None or self._last_shape != (H, W):
            self._ensure_bg_pipeline(H, W)
        frame_u8_2d = np.flipud(frame_u8_2d)
        data = np.ascontiguousarray(frame_u8_2d)
        self._importer.CopyImportVoidPointer(data.data, data.nbytes)
        self._importer.Modified()
        if self._wl:
            self._wl.Modified()
        if self._bg_actor:
            self._bg_actor.Modified()

    def add_cube(self, size, color=(0.27, 0.51, 0.71)):
        cube = vtk.vtkCubeSource()
        cube.SetXLength(size)
        cube.SetYLength(size)
        cube.SetZLength(size)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(cube.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.PickableOn()
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.actor = actor
        self._emit_pose()
        self.render_window.Render()
        return actor

    def reset_camera(self):
        self.renderer.ResetCamera()
        self.render_window.Render()

    def set_actor_translation(self, x=0.0, y=0.0, z=0.0):
        if not self.actor:
            return
        self.actor.SetPosition(x, y, z)
        self.renderer.ResetCameraClippingRange()
        self._emit_pose()
        self.render_window.Render()

    def set_actor_rotation_euler(self, rx_deg=0.0, ry_deg=0.0, rz_deg=0.0):
        if not self.actor:
            return
        self.actor.SetOrientation(rx_deg, ry_deg, rz_deg)
        self.renderer.ResetCameraClippingRange()
        self._emit_pose()
        self.render_window.Render()

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
        if self._bg_actor:
            self.bg_renderer.RemoveActor(self._bg_actor)
            self._bg_actor = None
            self._wl = None
            self._importer = None
        self.render_window.Render()
        self._emit_pose()

    def _on_interaction(self, *_):
        self._sync_axes_to_actor_matrix()
        self.render_window.Render()
        self._emit_pose()

    def _emit_pose(self):
        if not self.actor:
            return
        self._sync_axes_to_actor_matrix()
        x, y, z = self.actor.GetPosition()
        rx, ry, rz = self.actor.GetOrientation()
        self.poseChanged.emit(x, y, z, rx, ry, rz)

    def _sync_axes_to_actor_matrix(self):
        if not (self._axes_widget and self._axes_actor and self._axes_follow == "actor" and self.actor):
            return
        m = vtk.vtkMatrix4x4()
        self.actor.GetMatrix(m)
        m.SetElement(0, 3, 0.0)
        m.SetElement(1, 3, 0.0)
        m.SetElement(2, 3, 0.0)
        m.SetElement(3, 0, 0.0)
        m.SetElement(3, 1, 0.0)
        m.SetElement(3, 2, 0.0)
        m.SetElement(3, 3, 1.0)
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
        self._fluoro_loaded = False

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

        # Collapsible help section
        self.ui.help_section.setVisible(False)
        self.ui.help_btn.clicked.connect(self._toggle_help)

        # Swap placeholder with our VTKView
        self.view = VTKView(self.ui.mainpanel, bg=(0.10, 0.12, 0.14))
        self.ui.horizontalLayout_2.replaceWidget(self.ui.VTK_display, self.view)
        self.ui.VTK_display.setParent(None)
        self.ui.VTK_display.deleteLater()

        # Use the QLineEdit from Designer as the frame indicator
        self.frame_field = self.ui.frame_indicator
        self.frame_field.setReadOnly(True)
        self.frame_field.setAlignment(Qt.AlignRight)
        self.frame_field.setText("0 / 0")

        # Scene
        self.view.add_cube(size=0.5, color=(0.27, 0.51, 0.71))
        self.view.add_axes_widget(size=0.18, follow="actor")
        self.view.reset_camera()

        # Inputs <-> cube
        self.ui.pos_x.textChanged.connect(self._on_pos_changed)
        self.ui.pos_y.textChanged.connect(self._on_pos_changed)
        self.ui.pos_z.textChanged.connect(self._on_pos_changed)
        self.ui.rotation_x.textChanged.connect(self._on_rot_changed)
        self.ui.rotation_y.textChanged.connect(self._on_rot_changed)
        self.ui.rotation_z.textChanged.connect(self._on_rot_changed)
        self.view.poseChanged.connect(self._update_fields_from_pose)

        # Frame stepping buttons
        if hasattr(self.ui, "next_frame"):
            self.ui.next_frame.clicked.connect(lambda: self.view.step_frame(-1))
        if hasattr(self.ui, "prev_frame"):
            self.ui.prev_frame.clicked.connect(lambda: self.view.step_frame(+1))

        # Update frame indicator
        self.view.frameChanged.connect(self._on_frame_changed)

        # Seed pose UI
        x, y, z = self.view.actor.GetPosition()
        rx, ry, rz = self.view.actor.GetOrientation()
        self._update_fields_from_pose(x, y, z, rx, ry, rz)

    def _on_frame_changed(self, idx: int, total: int):
        self.frame_field.setText(f"{idx+1} / {total}")

    def showEvent(self, event):
        super().showEvent(event)
        if not self._fluoro_loaded:
            self.load_fluoro()
            self._fluoro_loaded = True

    def load_fluoro(self):
        singleton = SingletonPatient.get_instance()
        patient = singleton.patient
        self.view.load_dicom(patient.fluoro)
        self.view.show_frame(0)

    def _update_fields_from_pose(self, x, y, z, rx, ry, rz):
        pairs = [
            (self.ui.pos_x, f"{x:.3f}"),
            (self.ui.pos_y, f"{y:.3f}"),
            (self.ui.pos_z, f"{z:.3f}"),
            (self.ui.rotation_x, f"{rx:.2f}"),
            (self.ui.rotation_y, f"{ry:.2f}"),
            (self.ui.rotation_z, f"{rz:.2f}"),
        ]
        for w, val in pairs:
            with QSignalBlocker(w):
                w.setText(val)

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

    def _toggle_help(self):
        if self.ui.help_section.isVisible():
            self.ui.help_section.setVisible(False)
        else:
            self.ui.help_section.setVisible(True)
