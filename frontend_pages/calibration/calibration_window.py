"""
Fluoroscopy Calibration Module - Two-Layer Bead Detection

Corrects pincushion distortion using a two-layer calibration phantom.

X-ray projection geometry:
- Both layers have IDENTICAL (x,y) in 3D, differ only in z
- Front layer (RED): z=0, no magnification
- Back layer (BLUE): z=d, magnified radially from center
- Center bead: both layers project to SAME point
- Edge beads: back layer spreads outward

Controls (matching MATLAB reference):
- Scroll: Scale both layers uniformly (slow)
- Left-drag center: Translate
- Left-drag edges: In-plane rotation (Rz)
- Right-drag: Tilt phantom (Rx, Ry) - shifts blue layer relative to red

Based on: test_calibration.m MATLAB reference
"""

from __future__ import annotations
import os
import pickle
import numpy as np
from scipy.ndimage import map_coordinates
from skimage.transform import resize
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QImage, QPixmap, QPen, QBrush, QColor, QAction
from PySide6.QtWidgets import (
    QWidget, QFileDialog, QGraphicsScene, QGraphicsPixmapItem, 
    QGraphicsEllipseItem, QMessageBox, QGraphicsView, QInputDialog
)

from frontend_pages.calibration.ui_calibration_window import Ui_Form
from classes.objects import SingletonPatient, Context


# ============================================================================
# Constants
# ============================================================================

GRID_SIZE = 7
NUM_BEADS_PER_LAYER = GRID_SIZE * GRID_SIZE  # 49
NUM_BEADS_TOTAL = NUM_BEADS_PER_LAYER * 2     # 98

BEAD_SPACING_MM = 20.0
DEFAULT_LAYER_SEPARATION_MM = 200.0

STANDARD_SIZE = 512
SEARCH_WINDOW = 7

# Perspective projection: source-detector distance
DEFAULT_D1 = 1200.0

# Control sensitivity
SCALE_SCROLL_FACTOR = 1.005   # Very slow: 0.5% per scroll step
ROTATION_SENSITIVITY = 0.05   # Degrees per pixel of drag (very slow for right-drag)


# ============================================================================
# Image Loading
# ============================================================================

def find_dicom_directory(base_dir: str) -> Optional[str]:
    """Find directory containing DICOM files."""
    if _contains_dicom(base_dir):
        return base_dir
    try:
        for item in os.listdir(base_dir):
            path = os.path.join(base_dir, item)
            if os.path.isdir(path) and _contains_dicom(path):
                return path
    except:
        pass
    return None


def _contains_dicom(directory: str) -> bool:
    try:
        return any('.' not in f or f.endswith('.dcm') for f in os.listdir(directory))
    except:
        return False


def load_calibration_image(path: str) -> np.ndarray:
    """Load and preprocess calibration image to STANDARD_SIZE x STANDARD_SIZE."""
    if os.path.isdir(path):
        dicom_dir = find_dicom_directory(path)
        if not dicom_dir:
            raise ValueError(f"No DICOM files in: {path}")
        files = sorted([f for f in os.listdir(dicom_dir) if '.' not in f or f.endswith('.dcm')])
        if not files:
            raise ValueError(f"No DICOM files in: {dicom_dir}")
        path = os.path.join(dicom_dir, files[0])
    
    ext = os.path.splitext(path)[1].lower()
    
    if ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"]:
        import matplotlib.image as mpimg
        img = mpimg.imread(path).astype(np.float64)
    else:
        import pydicom
        ds = pydicom.dcmread(path)
        img = ds.pixel_array.astype(np.float64)
        if hasattr(ds, 'PhotometricInterpretation') and ds.PhotometricInterpretation == 'MONOCHROME1':
            img = img.max() - img
    
    if img.ndim == 3:
        img = np.mean(img, axis=2)
    
    img = (img - img.min()) * (255.0 / (img.max() - img.min() + 1e-10))
    
    if img.shape[0] != STANDARD_SIZE:
        img = resize(img, (STANDARD_SIZE, STANDARD_SIZE), order=5, anti_aliasing=True)
    
    return img


def numpy_to_qpixmap(arr: np.ndarray) -> QPixmap:
    """Convert numpy array to QPixmap."""
    arr = ((arr - arr.min()) / (arr.max() - arr.min() + 1e-10) * 255).astype(np.uint8)
    h, w = arr.shape
    return QPixmap.fromImage(QImage(arr.data, w, h, w, QImage.Format_Grayscale8).copy())


# ============================================================================
# 3D Grid and Perspective Projection
# ============================================================================

def create_3d_bead_grid(bead_spacing: float, layer_separation: float) -> np.ndarray:
    """
    Create 3D coordinates for 98 beads (2 layers x 49 beads).
    
    Both layers have IDENTICAL (x, y) positions relative to optical axis.
    Center bead (i=3, j=3) is at (0, 0) - projects to same point for both layers.
    """
    coords = np.zeros((NUM_BEADS_TOTAL, 4))
    
    idx = 0
    for k in range(2):  # k=0: front, k=1: back
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                x = (i - 3) * bead_spacing  # Relative to optical axis
                y = (j - 3) * bead_spacing

                z = (1 - k) * layer_separation

                coords[idx] = [x, y, z, 1]
                idx += 1
    
    return coords


def apply_perspective_projection(coords_3d: np.ndarray, d1: float, 
                                  image_center: float) -> np.ndarray:
    """
    Project 3D to 2D using conical X-ray projection.
    
    mag = d1 / (d1 - z)
    - z=0 (front): mag = 1.0
    - z=d (back): mag > 1.0, spreads outward from center
    """
    coords_2d = np.zeros((coords_3d.shape[0], 2))
    
    for i in range(coords_3d.shape[0]):
        x, y, z = coords_3d[i, :3]
        mag = d1 / (d1 - z)
        coords_2d[i, 0] = x * mag + image_center
        coords_2d[i, 1] = y * mag + image_center
    
    return coords_2d


def make_rotation_matrix(rx_deg: float, ry_deg: float, rz_deg: float) -> np.ndarray:
    """Create 3x3 rotation matrix from Euler angles (degrees)."""
    rx, ry, rz = np.radians([rx_deg, ry_deg, rz_deg])
    
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    
    return Rz @ Ry @ Rx


def transform_and_project(coords_3d: np.ndarray, 
                          tx: float, ty: float,
                          rx: float, ry: float, rz: float,
                          scale: float, d1: float,
                          image_center: float) -> np.ndarray:
    """
    Apply pose transformation and perspective projection.
    
    1. Apply 3D rotation around optical axis (tilts shift back layer relative to front)
    2. Apply perspective projection
    3. Apply 2D scale
    4. Apply 2D translation
    """
    # 3D rotation
    R = make_rotation_matrix(rx, ry, rz)
    xyz = coords_3d[:, :3].copy()
    xyz_rotated = (R @ xyz.T).T
    
    # Perspective projection
    coords_rotated = np.column_stack([xyz_rotated, np.ones(len(xyz_rotated))])
    coords_2d = apply_perspective_projection(coords_rotated, d1, image_center)
    
    # 2D scale around center
    coords_2d = (coords_2d - image_center) * scale + image_center
    
    # 2D translation
    coords_2d[:, 0] += tx
    coords_2d[:, 1] += ty
    
    return coords_2d


# ============================================================================
# Bead Detection
# ============================================================================

def snap_to_beads(img: np.ndarray, gpx: np.ndarray, gpy: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Detect beads and snap grid positions to bead centers."""
    n = len(gpx)
    bpx, bpy = np.zeros(n), np.zeros(n)
    minp = np.zeros(n)
    missing = np.zeros(n, dtype=bool)
    
    F = np.array(img)
    S = F.shape[0]
    
    for i in range(n):
        bx, by = int(round(gpx[i])), int(round(gpy[i]))
        
        if bx < SEARCH_WINDOW+1 or bx >= S-SEARCH_WINDOW-1 or by < SEARCH_WINDOW+1 or by >= S-SEARCH_WINDOW-1:
            bpx[i], bpy[i], missing[i] = gpx[i], gpy[i], True
            continue
        
        P = F[by-SEARCH_WINDOW:by+SEARCH_WINDOW+1, bx-SEARCH_WINDOW:bx+SEARCH_WINDOW+1]
        P_min, P_max = np.min(P), np.max(P)
        minp[i] = P_min
        threshold = P_min + 0.5 * (P_max - P_min)
        
        min_list = []
        for u in range(1, 2*SEARCH_WINDOW):
            for v in range(1, 2*SEARCH_WINDOW):
                if P[u, v] == np.min(P[u-1:u+2, v-1:v+2]) and P[u, v] < threshold:
                    min_list.append([u, v])
        
        if min_list:
            min_list = np.array(min_list)
            dist = np.sqrt((min_list[:, 1] - SEARCH_WINDOW)**2 + (min_list[:, 0] - SEARCH_WINDOW)**2)
            idx = np.argmin(dist)
            yo, xo = min_list[idx]
            
            bead_y, bead_x = by - SEARCH_WINDOW + yo, bx - SEARCH_WINDOW + xo
            
            if 1 <= bead_y < S-1 and 1 <= bead_x < S-1:
                vals = F[bead_y-1:bead_y+2, bead_x-1:bead_x+2].astype(np.float64)
                weights = -(vals.max() - vals)
                weights /= weights.sum() + 1e-10
                
                xc = np.sum(np.sum(weights, axis=0) * np.arange(3))
                yc = np.sum(np.sum(weights, axis=1) * np.arange(3))
                
                bpx[i] = bead_x - 1 + xc
                bpy[i] = bead_y - 1 + yc
            else:
                bpx[i], bpy[i] = bead_x, bead_y
        else:
            bpx[i], bpy[i], missing[i] = gpx[i], gpy[i], True
    
    # Outlier detection
    back_minp = minp[NUM_BEADS_PER_LAYER:][~missing[NUM_BEADS_PER_LAYER:]]
    if len(back_minp) > 5:
        med, std = np.median(back_minp), np.std(back_minp) + 1e-10
        for i in range(n):
            if not missing[i] and (minp[i] - med) / std > 1.5:
                bpx[i], bpy[i], missing[i] = gpx[i], gpy[i], True
    
    return bpx, bpy, missing


# ============================================================================
# Distortion Correction
# ============================================================================

def fit_polynomial_correction(gpx: np.ndarray, gpy: np.ndarray,
                               bpx: np.ndarray, bpy: np.ndarray,
                               missing: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Fit 4-term polynomial distortion correction."""
    S = STANDARD_SIZE
    ind = np.where(~missing)[0]
    
    if len(ind) < 10:
        raise ValueError(f"Only {len(ind)} valid beads, need at least 10")
    
    err_x = gpx[ind] - bpx[ind]
    err_y = gpy[ind] - bpy[ind]
    
    x = gpx[ind] - S/2
    y = gpy[ind] - S/2
    
    X = np.column_stack([x, x**3, x*(y**2), (x**3)*(y**2)])
    Y = np.column_stack([y, y**3, y*(x**2), (y**3)*(x**2)])
    
    ax, *_ = np.linalg.lstsq(X, err_x, rcond=None)
    ay, *_ = np.linalg.lstsq(Y, err_y, rcond=None)
    
    return ax, ay


def create_correction_maps(ax: np.ndarray, ay: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Create dense pixel-wise correction maps."""
    S = STANDARD_SIZE
    xx, yy = np.meshgrid(np.arange(S) - S/2, np.arange(S) - S/2)
    x, y = xx.ravel(), yy.ravel()
    
    X = np.column_stack([x, x**3, x*(y**2), (x**3)*(y**2)])
    Y = np.column_stack([y, y**3, y*(x**2), (y**3)*(x**2)])
    
    return (X @ ax).reshape(S, S), (Y @ ay).reshape(S, S)


def apply_correction(img: np.ndarray, adj_x: np.ndarray, adj_y: np.ndarray) -> np.ndarray:
    """Apply distortion correction."""
    S = img.shape[0]
    xx, yy = np.meshgrid(np.arange(S) - S/2, np.arange(S) - S/2)
    coords = np.array([yy - adj_y + S/2, xx - adj_x + S/2])
    return map_coordinates(img.astype(np.float64), coords, order=3, mode='constant', cval=0)


# ============================================================================
# Main Widget
# ============================================================================

class Calibration(QWidget):
    """Two-layer fluoroscopy calibration interface."""
    
    def __init__(self):
        super().__init__()
        
        # UI setup
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.titlebar.ui.title.setText("Calibration")
        self.ui.sidebar.ui.calibration.setStyleSheet(
            "QPushButton { color: white; background-color: #6f8ab7; border: none; padding: 10px 25px; }"
        )
        
        self.scene = QGraphicsScene(self)
        self.ui.VTK_display.setScene(self.scene)
        self.ui.VTK_display.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.ui.VTK_display.setMouseTracking(True)
        
        # Parameters
        self.layer_separation_mm = DEFAULT_LAYER_SEPARATION_MM
        self.d1 = DEFAULT_D1
        
        # State
        self.img_original: Optional[np.ndarray] = None
        self.img_display: Optional[np.ndarray] = None
        self.base_pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.overlay_items: list = []
        
        self.coords_3d: Optional[np.ndarray] = None
        self.gpx: Optional[np.ndarray] = None
        self.gpy: Optional[np.ndarray] = None
        self.bpx: Optional[np.ndarray] = None
        self.bpy: Optional[np.ndarray] = None
        self.bpx0: Optional[np.ndarray] = None
        self.bpy0: Optional[np.ndarray] = None
        self.missing: Optional[np.ndarray] = None
        
        self.grid_loaded = False
        self.invert = False
        
        # Pose parameters
        self.tx, self.ty = 0.0, 0.0
        self.rx, self.ry, self.rz = 0.0, 0.0, 0.0
        self.scale = 1.0
        
        # Correction
        self.ax, self.ay = None, None
        self.adj_x, self.adj_y = None, None
        
        # Mouse state
        self.mouse_pressed = False
        self.mouse_button = None
        self.mouse_start = (0, 0)
        self.mouse_prev = (0, 0)
        self.interaction_mode = None
        self.grid_center = (STANDARD_SIZE/2, STANDARD_SIZE/2)
        
        # Connect signals
        self.ui.pushButton.clicked.connect(self.load_calibration_grid)
        self.ui.pushButton_2.clicked.connect(self.invert_colors)
        self.ui.pushButton_3.clicked.connect(self.overlay_square_grid)
        self.ui.pushButton_4.clicked.connect(self.snap_to_beads)
        self.ui.pushButton_5.clicked.connect(self.correct_distortion)
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_correction)
        self.addAction(save_action)
        
        self.ui.VTK_display.viewport().installEventFilter(self)
    
    # =========================================================================
    # Mouse Events
    # =========================================================================
    
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj == self.ui.VTK_display.viewport():
            if event.type() == QEvent.MouseButtonPress:
                return self._on_press(event)
            elif event.type() == QEvent.MouseMove:
                return self._on_move(event)
            elif event.type() == QEvent.MouseButtonRelease:
                return self._on_release(event)
            elif event.type() == QEvent.Wheel:
                return self._on_wheel(event)
        return super().eventFilter(obj, event)
    
    def _on_press(self, event) -> bool:
        if self.gpx is None:
            return False
        
        self.mouse_pressed = True
        self.mouse_button = event.button()
        pos = self.ui.VTK_display.mapToScene(event.pos())
        self.mouse_start = self.mouse_prev = (pos.x(), pos.y())
        
        mx, my = self.grid_center
        if self.mouse_button == Qt.RightButton:
            # Right-drag: tilt phantom (shifts blue layer relative to red)
            self.interaction_mode = 'out_rotation'
        elif abs(pos.x() - mx) < 50 and abs(pos.y() - my) < 50:
            self.interaction_mode = 'translation'
        else:
            self.interaction_mode = 'in_rotation'
        
        return True
    
    def _on_move(self, event) -> bool:
        if not self.mouse_pressed or self.gpx is None:
            return False
        
        pos = self.ui.VTK_display.mapToScene(event.pos())
        x, y = pos.x(), pos.y()
        px, py = self.mouse_prev
        
        if self.interaction_mode == 'translation':
            self.tx += x - px
            self.ty += y - py
            
        elif self.interaction_mode == 'in_rotation':
            cx, cy = self.grid_center
            angle_curr = np.arctan2(y - cy, x - cx)
            angle_prev = np.arctan2(py - cy, px - cx)
            self.rz += np.degrees(angle_curr - angle_prev)
            
        elif self.interaction_mode == 'out_rotation':
            # Right-drag: VERY SLOW tilt to shift blue layer
            # Drag right → blue shifts right (positive Ry)
            # Drag up → blue shifts up (negative Rx, since Y is inverted in image coords)
            self.ry += (x - px) * ROTATION_SENSITIVITY
            self.rx -= (y - py) * ROTATION_SENSITIVITY
        
        self.mouse_prev = (x, y)
        self._update_grid()
        self._draw_overlay()
        return True
    
    def _on_release(self, event) -> bool:
        self.mouse_pressed = False
        return True
    
    def _on_wheel(self, event) -> bool:
        """Scroll: Scale both layers uniformly (slow)."""
        if self.gpx is None:
            return False
        
        delta = event.angleDelta().y()
        
        if delta > 0:
            self.scale *= SCALE_SCROLL_FACTOR
        else:
            self.scale /= SCALE_SCROLL_FACTOR
        
        self.scale = np.clip(self.scale, 0.1, 20.0)

        # if delta > 0:
        #     self.d1 *= SCALE_SCROLL_FACTOR
        # else:
        #     self.d1 /= SCALE_SCROLL_FACTOR

        # self.d1 = np.clip(self.d1, 500.0, 3000.0)
        
        self._update_grid()
        self._draw_overlay()
        return True
    
    # =========================================================================
    # Grid Update
    # =========================================================================
    
    def _update_grid(self):
        """Update 2D grid positions from 3D coords and current pose."""
        if self.coords_3d is None:
            return
        
        center = STANDARD_SIZE / 2
        projected = transform_and_project(
            self.coords_3d,
            self.tx, self.ty,
            self.rx, self.ry, self.rz,
            self.scale, self.d1,
            center
        )
        
        self.gpx = projected[:, 0]
        self.gpy = projected[:, 1]
        
        self.grid_center = (np.mean(self.gpx[:NUM_BEADS_PER_LAYER]), 
                           np.mean(self.gpy[:NUM_BEADS_PER_LAYER]))
    
    # =========================================================================
    # Button Handlers
    # =========================================================================
    
    def load_calibration_grid(self):
        """Load calibration image."""
        singleton = SingletonPatient.get_instance()
        path = singleton.patient.caligrid
        
        if not path or not os.path.exists(path):
            path = QFileDialog.getExistingDirectory(self, "Select Calibration Grid Folder")
            if not path:
                return
        
        try:
            self.img_original = load_calibration_image(path)
            self.img_display = self.img_original.copy()
            self.invert = False
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        
        self._reset_state()
        self._display_image(self.img_display)
        self.grid_loaded = True
        
        QMessageBox.information(self, "Loaded", 
            f"Calibration image loaded ({STANDARD_SIZE}x{STANDARD_SIZE}).")
    
    def invert_colors(self):
        """Toggle image inversion."""
        if self.img_original is None:
            return
        
        self.invert = not self.invert
        self.img_display = (255 - self.img_original) if self.invert else self.img_original.copy()
        self._display_image(self.img_display)
        self._draw_overlay()
    
    def overlay_square_grid(self):
        """Create and overlay two-layer grid."""
        if not self.grid_loaded:
            QMessageBox.information(self, "No Image", "Load calibration grid first.")
            return
        
        sep, ok = QInputDialog.getDouble(
            self, "Layer Separation",
            "Physical separation between layers (mm):",
            self.layer_separation_mm, 10, 500, 1
        )
        if not ok:
            return
        self.layer_separation_mm = sep
        
        self.coords_3d = create_3d_bead_grid(BEAD_SPACING_MM, self.layer_separation_mm)
        
        # Reset pose
        self.tx, self.ty = 0.0, 0.0
        self.rx, self.ry, self.rz = 0.0, 0.0, 0.0
        self.scale = 1.0
        self.d1 = DEFAULT_D1
        
        self._update_grid()
        self._draw_overlay()
    
    def snap_to_beads(self):
        """Detect beads and snap grid."""
        if self.gpx is None:
            QMessageBox.information(self, "No Grid", "Overlay grid first.")
            return
        
        self.bpx, self.bpy, self.missing = snap_to_beads(self.img_display, self.gpx, self.gpy)
        self.bpx0, self.bpy0 = self.bpx.copy(), self.bpy.copy()
        
        self.gpx, self.gpy = self.bpx.copy(), self.bpy.copy()
        self._draw_overlay()
        
        front_ok = np.sum(~self.missing[:NUM_BEADS_PER_LAYER])
        back_ok = np.sum(~self.missing[NUM_BEADS_PER_LAYER:])
        
        QMessageBox.information(self, "Snap Complete",
            f"Front (RED): {front_ok}/49\nBack (BLUE): {back_ok}/49")
    
    def correct_distortion(self):
        """Compute and apply distortion correction."""
        if self.bpx0 is None:
            QMessageBox.information(self, "Not Snapped", "Snap to beads first.")
            return
        
        try:
            self.ax, self.ay = fit_polynomial_correction(
                self.gpx, self.gpy, self.bpx0, self.bpy0, self.missing
            )
            self.adj_x, self.adj_y = create_correction_maps(self.ax, self.ay)
            
            self.img_display = apply_correction(self.img_display, self.adj_x, self.adj_y)
            self._display_image(self.img_display)
            
            self._update_grid()
            self._draw_overlay()
            
            QMessageBox.information(self, "Done", 
                "Distortion corrected.\nPress Ctrl+S to save.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", str(e))
    
    def save_correction(self):
        """Save correction parameters."""
        if self.adj_x is None:
            QMessageBox.information(self, "Nothing to Save", "Run correction first.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save", "fluoro_correction.pkl", "Pickle (*.pkl)")

        # Create context and set to SegmentState
        singleton = SingletonPatient.get_instance()
        context = singleton._state.context
        completed = context.request_process((path, self.adj_x, self.adj_y))

        if completed:
            QMessageBox.information(self, "Saved", f"Saved to:\n{os.path.basename(path)}")

        else:
            QMessageBox.information(self, "Unable to process request", "Please try again")
    
    # =========================================================================
    # Visualization
    # =========================================================================
    
    def _reset_state(self):
        self.coords_3d = None
        self.gpx = self.gpy = None
        self.bpx = self.bpy = None
        self.bpx0 = self.bpy0 = None
        self.missing = None
        self.tx = self.ty = 0.0
        self.rx = self.ry = self.rz = 0.0
        self.scale = 1.0
        self.d1 = DEFAULT_D1
        self.ax = self.ay = None
        self.adj_x = self.adj_y = None
        self.overlay_items.clear()
    
    def _display_image(self, img: np.ndarray):
        self.scene.clear()
        self.overlay_items.clear()
        self.base_pixmap_item = QGraphicsPixmapItem(numpy_to_qpixmap(img))
        self.scene.addItem(self.base_pixmap_item)
        self._fit_view()
    
    def _draw_overlay(self):
        for item in self.overlay_items:
            self.scene.removeItem(item)
        self.overlay_items.clear()
        
        if self.gpx is None:
            return
        
        r = 4
        for i in range(NUM_BEADS_TOTAL):
            color = QColor(255, 60, 60) if i < NUM_BEADS_PER_LAYER else QColor(60, 60, 255)
            if self.missing is not None and self.missing[i]:
                color.setAlpha(80)
            
            item = QGraphicsEllipseItem(QRectF(self.gpx[i]-r, self.gpy[i]-r, 2*r, 2*r))
            item.setPen(QPen(color, 1))
            item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            self.scene.addItem(item)
            self.overlay_items.append(item)
        
        self.scene.update()
    
    def _fit_view(self):
        self.ui.VTK_display.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_view()
    
    def showEvent(self, event):
        super().showEvent(event)
        if self.img_original is None:
            singleton = SingletonPatient.get_instance()
            path = singleton.patient.caligrid
            if path and os.path.exists(path):
                try:
                    self.img_original = load_calibration_image(path)
                    self.img_display = self.img_original.copy()
                    self.grid_loaded = True
                    self._display_image(self.img_display)
                except:
                    pass