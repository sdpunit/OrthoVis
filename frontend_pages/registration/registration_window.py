from PySide6.QtCore import Qt, Signal, QSignalBlocker, QEvent
from PySide6.QtGui import QSurfaceFormat, QQuaternion, QVector3D
from PySide6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout

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

# OUR EDGE GENERATOR
from frontend_pages.registration.edge_map import generate_edge_map_np


class VTKView(QWidget):
    """Shows a 2D DICOM frame as background and a foreground actor (our edge map)."""
    poseChanged = Signal(float, float, float, float, float, float)
    frameChanged = Signal(int, int)  # (current_index, total_frames)

    def _quaternion_to_euler(self, q):
        w, x, y, z = q.scalar(), q.x(), q.y(), q.z()
        import math
        t0 = 2.0 * (w * x + y * z)
        t1 = 1.0 - 2.0 * (x * x + y * y)
        roll_x = math.degrees(math.atan2(t0, t1))
        t2 = 2.0 * (w * y - z * x)
        t2 = max(-1.0, min(1.0, t2))
        pitch_y = math.degrees(math.asin(t2))
        t3 = 2.0 * (w * z + x * y)
        t4 = 1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.degrees(math.atan2(t3, t4))
        return roll_x, pitch_y, yaw_z

    def _get_actor_quaternion(self):
        if not self.actor:
            return QQuaternion()
        rx, ry, rz = self.actor.GetOrientation()
        return QQuaternion.fromEulerAngles(rx, ry, rz)

    def _set_actor_quaternion(self, q):
        rx, ry, rz = self._quaternion_to_euler(q)
        self.set_actor_rotation_euler(rx, ry, rz)

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
        self.render_window.SetAlphaBitPlanes(1)
        self.render_window.SetMultiSamples(0)

        # background renderer (fluoro)
        self.bg_renderer = vtk.vtkRenderer()
        self.bg_renderer.SetLayer(0)
        self.bg_renderer.SetInteractive(0)
        self.bg_renderer.SetErase(1)                 # clear color/depth
        self.bg_renderer.SetPreserveDepthBuffer(0)   # don't carry depth into next layer

        # foreground renderer (edge actor)
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetLayer(1)
        self.renderer.SetBackground(*bg)
        self.renderer.SetErase(0)                    # draw over background without clearing
        self.renderer.SetPreserveDepthBuffer(0)      # IGNORE background depth (no occlusion)

        self.render_window.SetNumberOfLayers(2)
        self.render_window.AddRenderer(self.bg_renderer)
        self.render_window.AddRenderer(self.renderer)

        # Share one camera between both renderers
        self.renderer.SetActiveCamera(self.bg_renderer.GetActiveCamera())

        # Interactor
        self.iren = self.vtk
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballActor())
        self.picker = vtk.vtkPropPicker()
        self.iren.SetPicker(self.picker)
        self.iren.AddObserver(vtk.vtkCommand.InteractionEvent, self._on_interaction)
        self.iren.AddObserver(vtk.vtkCommand.EndInteractionEvent, self._on_interaction)
        self.iren.Initialize()

        # wheel -> translate z
        self._wheel_step = 0.05
        self.iren.AddObserver("MouseWheelForwardEvent", self._on_wheel_forward, 1.0)
        self.iren.AddObserver("MouseWheelBackwardEvent", self._on_wheel_backward, 1.0)

        # State
        self.actor = None
        self._axes_widget = None
        self._axes_actor = None
        self._axes_follow = "actor"

        # DICOM/frame state
        self._frames_u8 = None
        self._num_frames = 0
        self._frame = 0

        self._importer = None
        self._wl = None
        self._bg_actor = None
        self._last_shape = None

        self.last_mouse_pos = None
        self.vtk.installEventFilter(self)  # intercept mouse events

    # ---------- show binary edge map as transparent RGBA image ----------
    def add_edge_map(self, edge_img: np.ndarray, color=(0, 0, 0)):
        # normalize to 0/255 uint8
        if edge_img.dtype != np.uint8:
            edge_u8 = (edge_img.astype(np.uint8) * 255) if edge_img.max() <= 1 else edge_img.astype(np.uint8)
        else:
            edge_u8 = edge_img
        edge_u8 = np.clip(edge_u8, 0, 255)

        H, W = edge_u8.shape
        rgba = np.zeros((H, W, 4), dtype=np.uint8)
        r, g, b = [int(c) for c in color]
        rgba[..., :3] = (r, g, b)
        rgba[..., 3] = edge_u8

        data = np.ascontiguousarray(np.flipud(rgba))

        importer = vtk.vtkImageImport()
        importer.CopyImportVoidPointer(data.data, data.nbytes)
        importer.SetDataScalarTypeToUnsignedChar()
        importer.SetNumberOfScalarComponents(4)
        importer.SetWholeExtent(0, W - 1, 0, H - 1, 0, 0)
        importer.SetDataExtentToWholeExtent()
        importer.Modified()

        actor = vtk.vtkImageActor()
        actor.GetMapper().SetInputConnection(importer.GetOutputPort())

        # rotate around image center
        actor.SetOrigin(W / 2.0, H / 2.0, 0.0)

        # overlay config
        prop = actor.GetProperty()
        prop.SetOpacity(1.0)
        prop.SetInterpolationTypeToNearest()

        if self.actor:
            self.renderer.RemoveActor(self.actor)

        self.renderer.AddActor(actor)
        self.actor = actor
        self.render_window.Render()
        return actor

        # ---------- interaction plumbing ----------
    def eventFilter(self, obj, event):
        if obj == self.vtk:
            if event.type() == QEvent.MouseButtonPress:
                self.last_mouse_pos = event.pos()
                return True

            if event.type() == QEvent.MouseMove:
                if self.last_mouse_pos is None or event.buttons() == Qt.NoButton:
                    return False

                dx = event.x() - self.last_mouse_pos.x()
                dy = event.y() - self.last_mouse_pos.y()
                self.last_mouse_pos = event.pos()

                if self.actor:
                    if event.modifiers() & Qt.ControlModifier:
                        # --- rotation with ctrl+drag ---
                        rx, ry, rz = self.actor.GetOrientation()
                        s = 0.4
                        new_rx = rx + dy * s   # pitch (X)
                        new_ry = ry            # (could also map dx to yaw if desired)
                        new_rz = rz + dx * s   # spin (Z)

                        if abs(new_rx) > 1e-3 or abs(new_ry) > 1e-3:
                            # recompute projection from CT
                            from classes.objects import SingletonPatient
                            singleton = SingletonPatient.get_instance()
                            patient = singleton.patient
                            dicom_dir = patient.CT
                            mask_path = os.path.join(patient.seg_masks_dir, "femur_right_otsu.nii.gz")

                            edge = generate_edge_map_np(
                                dicom_dir=dicom_dir,
                                mask_path=mask_path,
                                view="sagittal",
                                rx_deg=new_rx,
                                ry_deg=new_ry,
                                rz_deg=new_rz,
                                use_gradient_projection=True,
                                pre_smooth_sigma=0.8,
                                canny_sigma=1.6,
                                canny_perc_lo=60, canny_perc_hi=90,
                                clahe=False
                            )
                            self.add_edge_map(edge, color=(0, 0, 0))
                        else:
                            # pure Z spin: rotate 2D actor
                            self.set_actor_rotation_euler(rx, ry, new_rz)

                    else:
                        # --- translation ---
                        x, y, z = self.actor.GetPosition()
                        s = 0.4
                        self.set_actor_translation(x + dx * s, y - dy * s, z)
                return True

            if event.type() == QEvent.Wheel:
                if self.actor:
                    x, y, z = self.actor.GetPosition()
                    delta = event.angleDelta().y() / 120
                    self.set_actor_translation(x, y, z + 0.5 * delta)
                return True

            if event.type() == QEvent.MouseButtonRelease:
                self.last_mouse_pos = None
                return True

        return super().eventFilter(obj, event)

    def _on_wheel_forward(self, caller, evt):
        if self.actor:
            x, y, z = self.actor.GetPosition()
            self.set_actor_translation(x, y, z + self._wheel_step)
            caller.SetAbortFlag(1)

    def _on_wheel_backward(self, caller, evt):
        if self.actor:
            x, y, z = self.actor.GetPosition()
            self.set_actor_translation(x, y, z - self._wheel_step)
            caller.SetAbortFlag(1)

    # ---------- DICOM ----------
    def _resolve_dicom_path(self, path: str) -> str:
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                p = os.path.join(path, name)
                if os.path.isfile(p):
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
            low, high = wc - ww/2, wc + ww/2
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

        # CAMERA: perspective and wide clip range
        cam = self.bg_renderer.GetActiveCamera()
        cam.ParallelProjectionOff()
        self.bg_renderer.ResetCamera()          # fit background first
        cam.SetClippingRange(0.1, 10000.0)      # then force huge clip range
        self.render_window.Render()
        self.frameChanged.emit(self._frame, self._num_frames)

    def show_frame(self, index: int):
        if self._frames_u8 is None:
            return
        self._frame = max(0, min(index, self._num_frames - 1))
        self._push_frame_to_vtk(self._frames_u8[self._frame])
        # no ResetCameraClippingRange here
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

    # ---------- actor transforms ----------
    def reset_camera(self):
        cam = self.bg_renderer.GetActiveCamera()
        self.renderer.SetActiveCamera(cam)
        self.bg_renderer.ResetCamera()           # fit the fluoro
        cam.SetClippingRange(0.1, 10000.0)       # fixed, wide
        cam.SetPosition(0, 0, 800)
        cam.SetFocalPoint(0, 0, 0)
        cam.SetViewUp(0, 1, 0)
        cam.SetViewAngle(45)
        self.render_window.Render()

    def set_actor_translation(self, x=0.0, y=0.0, z=0.0):
        if not self.actor:
            return
        self.actor.SetPosition(x, y, z)
        # no ResetCameraClippingRange
        self._emit_pose()
        self.render_window.Render()

    def set_actor_rotation_euler(self, rx_deg=0.0, ry_deg=0.0, rz_deg=0.0):
        if not self.actor:
            return
        self.actor.SetOrientation(rx_deg, ry_deg, rz_deg)
        # no ResetCameraClippingRange
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
        m.SetElement(0, 3, 0.0); m.SetElement(1, 3, 0.0); m.SetElement(2, 3, 0.0)
        m.SetElement(3, 0, 0.0); m.SetElement(3, 1, 0.0); m.SetElement(3, 2, 0.0); m.SetElement(3, 3, 1.0)
        t = vtk.vtkTransform(); t.SetMatrix(m)
        self._axes_actor.SetUserTransform(t); self._axes_actor.Modified()


class Registration(QWidget):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self._fluoro_loaded = False

        self.ui.titlebar.ui.title.setText("Registration")
        self.ui.sidebar.ui.registration.setStyleSheet(
            "QPushButton { color: white; background-color: #6f8ab7; border: none; padding: 10px 25px; }"
        )

        self.ui.help_section.setVisible(False)
        self.ui.help_btn.clicked.connect(self._toggle_help)

        self.view = VTKView(self.ui.mainpanel, bg=(0.10, 0.12, 0.14))
        self.ui.horizontalLayout_2.replaceWidget(self.ui.VTK_display, self.view)
        self.ui.VTK_display.setParent(None)
        self.ui.VTK_display.deleteLater()

        self.frame_field = self.ui.frame_indicator
        self.frame_field.setReadOnly(True)
        self.frame_field.setAlignment(Qt.AlignRight)
        self.frame_field.setText("0 / 0")

        self.view.add_axes_widget(size=0.18, follow="actor")
        self.view.reset_camera()

        self.ui.pos_x.textEdited.connect(self._on_pos_changed)
        self.ui.pos_y.textEdited.connect(self._on_pos_changed)
        self.ui.pos_z.textEdited.connect(self._on_pos_changed)
        self.ui.rotation_x.textEdited.connect(self._on_rot_changed)
        self.ui.rotation_y.textEdited.connect(self._on_rot_changed)
        self.ui.rotation_z.textEdited.connect(self._on_rot_changed)
        self.view.poseChanged.connect(self._update_fields_from_pose)

        if hasattr(self.ui, "next_frame"):
            self.ui.next_frame.clicked.connect(lambda: self.view.step_frame(-1))
        if hasattr(self.ui, "prev_frame"):
            self.ui.prev_frame.clicked.connect(lambda: self.view.step_frame(+1))
        self.view.frameChanged.connect(self._on_frame_changed)

        if hasattr(self.ui, "pushButton"):
            self.ui.pushButton.clicked.connect(self._on_load_bone_mask)

        self._update_fields_from_pose(0, 0, 0, 0, 0, 0)

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

    def _on_load_bone_mask(self):
        singleton = SingletonPatient.get_instance()
        patient = singleton.patient

        dicom_dir = patient.CT
        mask_path = os.path.join(patient.seg_masks_dir, "femur_right_otsu.nii.gz")

        edge = generate_edge_map_np(
            dicom_dir=dicom_dir,
            mask_path=mask_path,
            view="sagittal",
            rx_deg=0.0, ry_deg=0.0,
            use_gradient_projection=True,
            pre_smooth_sigma=0.8,
            canny_sigma=1.6,
            canny_perc_lo=60, canny_perc_hi=90,
            clahe=False
        )

        self.view.add_edge_map(edge, color=(0, 0, 0))

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
            if not w.hasFocus():
                with QSignalBlocker(w):
                    w.setText(val)

    def _on_pos_changed(self):
        try:
            x = float(self.ui.pos_x.text()); y = float(self.ui.pos_y.text()); z = float(self.ui.pos_z.text())
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

        if abs(rx) > 1e-3 or abs(ry) > 1e-3:
            # recompute from CT
            singleton = SingletonPatient.get_instance()
            patient = singleton.patient
            edge = generate_edge_map_np(
                dicom_dir=patient.CT,
                mask_path=os.path.join(patient.seg_masks_dir, "femur_right_otsu.nii.gz"),
                view="sagittal",
                rx_deg=rx, ry_deg=ry, rz_deg=rz,
                use_gradient_projection=True,
                pre_smooth_sigma=0.8,
                canny_sigma=1.6,
                canny_perc_lo=60, canny_perc_hi=90,
                clahe=False
            )
            self.view.add_edge_map(edge, color=(0, 0, 0))
        else:
            # Z only → rotate 2D actor
            self.view.set_actor_rotation_euler(rx, ry, rz)

    def _toggle_help(self):
        self.ui.help_section.setVisible(not self.ui.help_section.isVisible())