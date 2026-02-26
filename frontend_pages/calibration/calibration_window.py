"""
Fluoroscopy Calibration Module - Two-Layer Bead Detection

Corrects pincushion distortion using a two-layer calibration phantom.

X-ray projection geometry:
- Both layers have IDENTICAL (x,y) in 3D, differ only in z
- Front layer (RED): z=0, no magnification
- Back layer (BLUE): z=d, magnified radially from centre
- Centre bead: both layers project to SAME point
- Edge beads: back layer spreads outward

Controls (matching MATLAB reference Calibrate_Fluoro.m):
- Scroll:            Scale both layers uniformly (slow)
- Left-drag centre:  Translate
- Left-drag edges:   In-plane rotation (Rz)
- Right-drag:        Tilt phantom (Rx, Ry) — shifts blue layer relative to red

Ground-truth reference: Calibrate_Fluoro.m / correct_fluoro.m
"""

from __future__ import annotations
import os
import pickle
import numpy as np
from scipy.ndimage import map_coordinates
from skimage.transform import resize
from typing import Optional, Tuple, List

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QImage, QPixmap, QPen, QBrush, QColor, QAction
from PySide6.QtWidgets import (
    QWidget, QFileDialog, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsEllipseItem, QMessageBox, QGraphicsView, QDialog, QFormLayout,
    QDoubleSpinBox, QDialogButtonBox
)

from frontend_pages.calibration.ui_calibration_window import Ui_Form
from classes.objects import SingletonPatient


# ============================================================================
# Constants
# ============================================================================

GRID_SIZE = 7
NUM_BEADS_PER_LAYER = GRID_SIZE * GRID_SIZE   # 49
NUM_BEADS_TOTAL     = NUM_BEADS_PER_LAYER * 2  # 98

BEAD_SPACING_MM          = 20.0
DEFAULT_LAYER_SEPARATION_MM = 200.0

STANDARD_SIZE = 512

# ---- Bead detection parameters -----------------------------------------------
#
# DETECT_HALF_WIN controls the search radius for the global-minimum bead finder.
# A 31-pixel radius comfortably tolerates manual positioning offsets of up to
# ~15 px while staying clear of neighbouring beads (typical spacing ≥ 25 px).
#
# DETECT_CENTROID_HALF controls the centroid-refinement patch size.
# A 7×7 patch (CH=3) averages over enough bead area to give stable sub-pixel
# localisation without being dominated by surrounding background.
#
DETECT_HALF_WIN      = 15  # search radius: patch = F[by-15:by+16, bx-15:bx+16]
DETECT_CENTROID_HALF = 3   # centroid patch half-width → 7×7

# ---- Perspective projection defaults ---------------------------------------
DEFAULT_D1 = 1200.0   # source-to-image-intensifier (mm)
DEFAULT_D2 =  960.0   # source-to-knee (mm)

# ---- Mouse control sensitivity --------------------------------------------
SCALE_SCROLL_FACTOR  = 1.005    # 0.5 % per scroll click
ROTATION_SENSITIVITY = 0.05     # degrees per pixel (right-drag tilt)


# ============================================================================
# Image Loading
# ============================================================================

def find_dicom_directory(base_dir: str) -> Optional[str]:
    if _contains_dicom(base_dir):
        return base_dir
    try:
        for item in os.listdir(base_dir):
            path = os.path.join(base_dir, item)
            if os.path.isdir(path) and _contains_dicom(path):
                return path
    except Exception:
        pass
    return None


def _contains_dicom(directory: str) -> bool:
    try:
        return any('.' not in f or f.endswith('.dcm') for f in os.listdir(directory))
    except Exception:
        return False


def load_calibration_image(path: str) -> np.ndarray:
    """Load and pre-process calibration image to STANDARD_SIZE × STANDARD_SIZE."""
    if os.path.isdir(path):
        dicom_dir = find_dicom_directory(path)
        if not dicom_dir:
            raise ValueError(f"No DICOM files found in: {path}")
        files = sorted(
            [f for f in os.listdir(dicom_dir) if '.' not in f or f.endswith('.dcm')]
        )
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
        if (hasattr(ds, 'PhotometricInterpretation')
                and ds.PhotometricInterpretation == 'MONOCHROME1'):
            img = img.max() - img

    if img.ndim == 3:
        img = np.mean(img, axis=2)

    img = (img - img.min()) * (255.0 / (img.max() - img.min() + 1e-10))

    if img.shape[0] != STANDARD_SIZE:
        img = resize(img, (STANDARD_SIZE, STANDARD_SIZE), order=5, anti_aliasing=True)

    return img


def numpy_to_qpixmap(arr: np.ndarray) -> QPixmap:
    arr8 = ((arr - arr.min()) / (arr.max() - arr.min() + 1e-10) * 255).astype(np.uint8)
    h, w = arr8.shape
    return QPixmap.fromImage(
        QImage(arr8.data, w, h, w, QImage.Format_Grayscale8).copy()
    )


# ============================================================================
# 3D Grid and Perspective Projection
# ============================================================================

def create_3d_bead_grid(bead_spacing_mm: float,
                         layer_separation_mm: float) -> np.ndarray:
    """
    Create homogeneous 3D coordinates for 98 beads (2 layers × 49 beads).

    Both layers have IDENTICAL (x, y) relative to the optical axis.
    The centre bead (i=3, j=3) sits at (0, 0) and projects identically
    for both layers regardless of magnification.

    Returns shape (98, 4): [x, y, z, 1].
    """
    coords = np.zeros((NUM_BEADS_TOTAL, 4))
    idx = 0
    for k in range(2):              # k=0: front (RED), k=1: back (BLUE)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                x = (i - 3) * bead_spacing_mm
                y = (j - 3) * bead_spacing_mm
                z = k * layer_separation_mm
                coords[idx] = [x, y, z, 1]
                idx += 1
    return coords


def apply_perspective_projection(coords_3d: np.ndarray,
                                  d1: float, d2: float,
                                  image_centre: float) -> np.ndarray:
    """
    Conical X-ray projection:  mag = d1 / (d2 + z)
    - z = 0 (front):  mag = d1/d2
    - z = d (back):   mag > d1/d2, spreads outward from centre

    Returns shape (N, 2): [col, row] in pixels.
    """
    n = coords_3d.shape[0]
    coords_2d = np.empty((n, 2))
    for i in range(n):
        x, y, z = coords_3d[i, :3]
        mag = d1 / (d2 + z)
        coords_2d[i, 0] = x * mag + image_centre   # column
        coords_2d[i, 1] = y * mag + image_centre   # row
    return coords_2d


def make_rotation_matrix(rx_deg: float, ry_deg: float, rz_deg: float) -> np.ndarray:
    rx, ry, rz = np.radians([rx_deg, ry_deg, rz_deg])
    Rx = np.array([[1, 0,           0          ],
                   [0, np.cos(rx), -np.sin(rx) ],
                   [0, np.sin(rx),  np.cos(rx) ]])
    Ry = np.array([[ np.cos(ry), 0, np.sin(ry)],
                   [ 0,          1, 0          ],
                   [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                   [np.sin(rz),  np.cos(rz), 0],
                   [0,           0,          1]])
    return Rz @ Ry @ Rx


def transform_and_project(coords_3d: np.ndarray,
                           tx: float, ty: float,
                           rx: float, ry: float, rz: float,
                           scale: float, d1: float, d2: float,
                           image_centre: float) -> np.ndarray:
    """
    Full pose → projection pipeline:
      1. 3-D rotation around the origin
      2. Perspective projection (conical X-ray)
      3. Uniform 2-D scale around image centre
      4. 2-D translation
    """
    R    = make_rotation_matrix(rx, ry, rz)
    xyz  = coords_3d[:, :3].copy()
    xyz  = (R @ xyz.T).T

    proj = np.column_stack([xyz, np.ones(len(xyz))])
    c2d  = apply_perspective_projection(proj, d1, d2, image_centre)

    # Scale around image centre
    c2d  = (c2d - image_centre) * scale + image_centre

    # 2-D translation
    c2d[:, 0] += tx
    c2d[:, 1] += ty

    return c2d


# ============================================================================
# Bead Detection  —  faithful port of snap_to_beads in Calibrate_Fluoro.m
# ============================================================================

def detect_beads(
    img:        np.ndarray,
    gpx:        np.ndarray,   # initial grid col positions  (N,)
    gpy:        np.ndarray,   # initial grid row positions  (N,)
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Detect bead centres and return sub-pixel positions.

    find_dark = False  (default, white beads on grey background):
        Searches for the global MAXIMUM in each patch interior.
        Use this when the original fluoroscopy has bright tantalum beads.
        This is the preferred mode — bright bead peaks are sharper and less
        contaminated by shot noise than dark-bead minima.

    find_dark = True  (black beads, i.e. after "Invert Grid"):
        Searches for the global MINIMUM in each patch interior.
        The MATLAB reference was hardcoded to this mode, which is why the
        "Invert Grid" button existed — to force white beads dark before
        snapping.  With this implementation inversion is no longer required.

    In both cases the centroid weighting favours the extreme-valued pixels
    (bright for white beads, dark for black beads) so that the sub-pixel
    estimate is pulled toward the bead centre.

    Parameters
    ----------
    img         : (S, S) float image  (row = y-axis, col = x-axis)
    gpx, gpy    : initial grid positions — col (x) and row (y)

    Returns
    -------
    bpx, bpy    : detected positions (fall back to gpx/gpy on failure)
    missing     : bool mask — outlier bead, excluded from polynomial fit
    outside     : bool mask — bead outside rectangular image boundary
    """
    HW = DETECT_HALF_WIN       # 15
    CH = DETECT_CENTROID_HALF  # 3  (→ 7×7 centroid patch)
    S  = img.shape[0]          # 512
    n  = len(gpx)

    F       = np.asarray(img, dtype=np.float64)
    bpx     = gpx.copy()
    bpy     = gpy.copy()
    missing = np.zeros(n, dtype=bool)
    outside = np.zeros(n, dtype=bool)

    valid_idx:  List[int]   = []
    valid_minp: List[float] = []

    for i in range(n):
        bx = int(round(gpx[i]))   # column
        by = int(round(gpy[i]))   # row

        # ------------------------------------------------------------------
        # Boundary check — patch F[by-HW:by+HW+1, bx-HW:bx+HW+1] must fit.
        # ------------------------------------------------------------------
        if not (HW <= bx <= S - HW - 1 and HW <= by <= S - HW - 1):
            outside[i] = True
            continue

        # ------------------------------------------------------------------
        # (2·HW+1) × (2·HW+1) search patch centred on circle position.
        # ------------------------------------------------------------------
        P     = F[by - HW : by + HW + 1,
                  bx - HW : bx + HW + 1]   # (31, 31)
        P_min = P.min()
        P_max = P.max()

        valid_idx.append(i)
        # Track the extreme intensity value for outlier detection.
        # For white beads this is the patch maximum.
        valid_minp.append(float(P_max))

        # ------------------------------------------------------------------
        # Find the brightest pixel in the patch interior.
        # Threshold: the extreme value must exceed the patch midpoint,
        # otherwise there is no clear bead feature in this patch.
        # ------------------------------------------------------------------
        interior  = P[1:-1, 1:-1]          # (29, 29)  1-px border excluded
        midpoint  = P_min + 0.5 * (P_max - P_min)

        extreme   = interior.max()
        no_feature = extreme <= midpoint   # not bright enough
        flat_idx  = int(interior.argmax())

        if no_feature:
            bpx[i] = gpx[i]
            bpy[i] = gpy[i]
            continue

        # Convert interior index back to full-patch coordinates (+1 border)
        y0 = flat_idx // interior.shape[1] + 1   # row in P
        x0 = flat_idx %  interior.shape[1] + 1   # col in P

        # Absolute image coordinates of the global minimum
        bead_row = by - HW + y0   # 0-based row in F
        bead_col = bx - HW + x0   # 0-based col in F

        # ------------------------------------------------------------------
        # (2·CH+1) × (2·CH+1) centroid-refinement patch centred on the
        # detected minimum.
        # Darkness-weighted centroid: w = (vals.max() – vals) / sum(...)
        # so that the darkest pixels (bead centre) get highest weight.
        # ------------------------------------------------------------------
        r0 = bead_row - CH
        r1 = bead_row + CH + 1
        c0 = bead_col - CH
        c1 = bead_col + CH + 1

        if r0 < 0 or r1 > S or c0 < 0 or c1 > S:
            # Centroid patch doesn't fit — accept integer position.
            bpx[i] = float(bead_col)
            bpy[i] = float(bead_row)
            continue

        vals     = F[r0:r1, c0:c1].copy()   # (7, 7)
        # Centroid weight: favour the extreme end that matches bead polarity.
        #   White bead → w = vals - min  (bright pixels get high weight)
        w = vals - vals.min()
        w_sum = w.sum()

        if w_sum == 0:
            # Completely uniform patch — accept integer position.
            bpx[i] = float(bead_col)
            bpy[i] = float(bead_row)
            continue

        w        /= w_sum                    # normalise → sums to 1
        idx_arr   = np.arange(2 * CH + 1, dtype=np.float64)  # [0..6]

        # Column centroid (x): marginalise over rows first
        f_col = w.sum(axis=0)               # (7,)
        xc    = float(np.dot(f_col, idx_arr))   # den = 1 after normalisation

        # Row centroid (y): marginalise over cols first
        f_row = w.sum(axis=1)               # (7,)
        yc    = float(np.dot(f_row, idx_arr))

        # Sub-pixel position: top-left corner of centroid patch + offset
        bpx[i] = c0 + xc
        bpy[i] = r0 + yc

    # -------------------------------------------------------------------------
    # Outlier detection on the tracked extreme intensity values.
    #   White beads: patch maxima — a weak (low) maximum → likely a missed bead
    #                → flag when value is MORE THAN 1.5 std BELOW the median
    # Statistics computed from the last 49 valid-bead values (≈ back layer).
    # -------------------------------------------------------------------------
    if len(valid_minp) > 0:
        vmp  = np.array(valid_minp)
        tail = vmp[-49:] if len(vmp) >= 49 else vmp
        med  = float(np.median(tail))
        std  = float(np.std(tail)) + 1e-10

        for j, i in enumerate(valid_idx):
            outlier = (med - vmp[j]) / std > 1.5   # max too low  → weak bright bead
            if outlier:
                bpx[i]     = gpx[i]
                bpy[i]     = gpy[i]
                missing[i] = True

    return bpx, bpy, missing, outside


# ============================================================================
# Distortion Correction  —  faithful port of correct_fluoro in Calibrate_Fluoro.m
# ============================================================================

def fit_polynomial_correction(
    gpx_detected: np.ndarray,   # snapped/detected col positions   (N,)
    gpy_detected: np.ndarray,   # snapped/detected row positions   (N,)
    gpx_ideal:    np.ndarray,   # ideal projected col positions    (N,)
    gpy_ideal:    np.ndarray,   # ideal projected row positions    (N,)
    missing:      np.ndarray,   # bool — outlier from detection
    outside:      np.ndarray,   # bool — out of rectangular bounds
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fit the 9-term polynomial distortion model from Calibrate_Fluoro.m:

    MATLAB correct_fluoro:
        err_x = gpx(ind) - bpx0(ind)   % projected_ideal  - detected
        err_y = gpy(ind) - bpy0(ind)

        x = gpx(ind) - S/2;   y = gpy(ind) - S/2;   (centred coordinates)

        X = [x  y  x²  x·y  y²  x³  x²·y  x·y²  y³]
        Y = [y  x  y²  y·x  x²  y³  y²·x  y·x²  x³]

        ax = lscov(X, err_x);    ay = lscov(Y, err_y);

    Both `missing` and `outside` are excluded, mirroring MATLAB's
        ind = find( (~missing) & (~outside) )
    """
    S   = STANDARD_SIZE
    ind = np.where(~missing & ~outside)[0]

    if len(ind) < 10:
        raise ValueError(
            f"Only {len(ind)} valid beads for fitting — need at least 10."
        )

    # Distortion errors: ideal projected position − detected position
    err_x = gpx_ideal[ind] - gpx_detected[ind]
    err_y = gpy_ideal[ind] - gpy_detected[ind]

    # Centred detected positions (matching MATLAB: x = gpx(ind)-S/2)
    x = gpx_detected[ind] - S / 2
    y = gpy_detected[ind] - S / 2

    # 9-term polynomial bases (identical to MATLAB)
    X = np.column_stack([x,    y,
                         x**2, x*y,   y**2,
                         x**3, (x**2)*y, x*(y**2), y**3])
    Y = np.column_stack([y,    x,
                         y**2, y*x,   x**2,
                         y**3, (y**2)*x, y*(x**2), x**3])

    ax, *_ = np.linalg.lstsq(X, err_x, rcond=None)
    ay, *_ = np.linalg.lstsq(Y, err_y, rcond=None)

    return ax, ay


def create_correction_maps(
    ax: np.ndarray,
    ay: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build dense pixel-wise correction maps using the identical 9-term basis.

    MATLAB correct_fluoro:
        [xx,yy] = meshgrid([1:S]-S/2,[1:S]-S/2);
        x = xx(:);  y = yy(:);
        XX = [x y x.^2 x.*y y.^2 x.^3 (x.^2).*y x.*(y.^2) y.^3];
        adj_x = reshape(XX*ax,[S S]);
    """
    S = STANDARD_SIZE
    # meshgrid matching MATLAB: meshgrid([1:S]-S/2, [1:S]-S/2)
    # = xx varies along cols,  yy varies along rows
    xx, yy = np.meshgrid(np.arange(1, S + 1) - S / 2,
                          np.arange(1, S + 1) - S / 2)
    x, y   = xx.ravel(), yy.ravel()

    XX = np.column_stack([x,    y,
                          x**2, x*y,   y**2,
                          x**3, (x**2)*y, x*(y**2), y**3])
    YY = np.column_stack([y,    x,
                          y**2, y*x,   x**2,
                          y**3, (y**2)*x, y*(x**2), x**3])

    adj_x = (XX @ ax).reshape(S, S)
    adj_y = (YY @ ay).reshape(S, S)

    return adj_x, adj_y


def apply_correction(img: np.ndarray,
                     adj_x: np.ndarray,
                     adj_y: np.ndarray) -> np.ndarray:
    """
    Apply distortion correction via bicubic interpolation.

    MATLAB correct_fluoro:
        Fc = interp2(xx, yy, double(F), xx-adj_x, yy-adj_y, 'bicubic', 0);

    scipy.ndimage.map_coordinates with order=3 is the equivalent.
    """
    S = img.shape[0]
    xx, yy = np.meshgrid(np.arange(1, S + 1) - S / 2,
                          np.arange(1, S + 1) - S / 2)
    # Sample positions in array-index space (row, col)
    # array row index = yy - adj_y + S/2 - 1  (−1 to convert 1-based → 0-based)
    sample_row = (yy - adj_y + S / 2) - 1
    sample_col = (xx - adj_x + S / 2) - 1
    coords     = np.array([sample_row, sample_col])
    return map_coordinates(img.astype(np.float64), coords,
                           order=3, mode='constant', cval=0.0)


# ============================================================================
# Main Widget
# ============================================================================

class Calibration(QWidget):
    """Two-layer fluoroscopy calibration interface."""

    def __init__(self):
        super().__init__()

        # ----- UI -----
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.titlebar.ui.title.setText("Calibration")
        self.ui.sidebar.ui.calibration.setStyleSheet(
            "QPushButton { color: white; background-color: #6f8ab7; "
            "border: none; padding: 10px 25px; }"
        )

        self.scene = QGraphicsScene(self)
        self.ui.VTK_display.setScene(self.scene)
        self.ui.VTK_display.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.ui.VTK_display.setMouseTracking(True)

        # ----- Imaging parameters -----
        self.layer_separation_mm = DEFAULT_LAYER_SEPARATION_MM
        self.d1 = DEFAULT_D1
        self.d2 = DEFAULT_D2

        # ----- Scene state -----
        self.img_original: Optional[np.ndarray] = None
        self.img_display:  Optional[np.ndarray] = None
        self.base_pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.overlay_items: list = []

        # ----- Bead grid state -----
        #
        # coords_3d           : (98, 4) homogeneous 3-D bead coordinates
        # gpx / gpy           : current 2-D grid positions (col, row)
        #                       AFTER snap_to_beads these are the DETECTED positions.
        # gpx_ideal / gpy_ideal: ideal projected positions saved BEFORE snapping —
        #                       used as the distortion-error reference in correction.
        # bpx / bpy           : raw output of detect_beads (alias for gpx/gpy post-snap)
        # missing             : bool — outlier, excluded from polynomial fit
        # outside             : bool — out of rectangular bounds, also excluded
        #
        self.coords_3d:   Optional[np.ndarray] = None
        self.gpx:         Optional[np.ndarray] = None
        self.gpy:         Optional[np.ndarray] = None
        self.bpx:         Optional[np.ndarray] = None
        self.bpy:         Optional[np.ndarray] = None
        self.gpx_ideal:   Optional[np.ndarray] = None   # saved pre-snap ideal positions
        self.gpy_ideal:   Optional[np.ndarray] = None
        self.missing:     Optional[np.ndarray] = None
        self.outside:     Optional[np.ndarray] = None

        self.grid_loaded = False

        # ----- Pose parameters -----
        self.tx,  self.ty  = 0.0, 0.0
        self.rx,  self.ry,  self.rz = 0.0, 0.0, 0.0
        self.scale = 1.0

        # ----- Correction results -----
        self.ax,    self.ay    = None, None
        self.adj_x, self.adj_y = None, None

        # ----- Mouse interaction -----
        self.mouse_pressed    = False
        self.mouse_button     = None
        self.mouse_start      = (0, 0)
        self.mouse_prev       = (0, 0)
        self.interaction_mode = None
        self.grid_centre      = (STANDARD_SIZE / 2, STANDARD_SIZE / 2)

        # ----- Signal connections -----
        self.ui.pushButton.clicked.connect(self.load_calibration_grid)
        self.ui.pushButton_2.clicked.connect(self.overlay_square_grid)
        self.ui.pushButton_3.clicked.connect(self.snap_to_beads)
        self.ui.pushButton_4.clicked.connect(self.correct_distortion)
        self.ui.pushButton_5.clicked.connect(self.save_correction)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_correction)
        self.addAction(save_action)

        self.ui.VTK_display.viewport().installEventFilter(self)

    # =========================================================================
    # Mouse / Wheel Events
    # =========================================================================

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj == self.ui.VTK_display.viewport():
            t = event.type()
            if   t == QEvent.MouseButtonPress:   return self._on_press(event)
            elif t == QEvent.MouseMove:           return self._on_move(event)
            elif t == QEvent.MouseButtonRelease:  return self._on_release(event)
            elif t == QEvent.Wheel:               return self._on_wheel(event)
        return super().eventFilter(obj, event)

    def _on_press(self, event) -> bool:
        if self.gpx is None:
            return False
        self.mouse_pressed = True
        self.mouse_button  = event.button()
        pos = self.ui.VTK_display.mapToScene(event.pos())
        self.mouse_start = self.mouse_prev = (pos.x(), pos.y())
        mx, my = self.grid_centre
        if self.mouse_button == Qt.RightButton:
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
        x, y   = pos.x(), pos.y()
        px, py = self.mouse_prev

        if self.interaction_mode == 'translation':
            self.tx += x - px
            self.ty += y - py
        elif self.interaction_mode == 'in_rotation':
            cx, cy = self.grid_centre
            self.rz += np.degrees(np.arctan2(y - cy, x - cx)
                                  - np.arctan2(py - cy, px - cx))
        elif self.interaction_mode == 'out_rotation':
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
        """Scroll wheel → uniform scale of both layers (very slow)."""
        if self.gpx is None:
            return False
        delta = event.angleDelta().y()
        self.scale *= SCALE_SCROLL_FACTOR if delta > 0 else 1.0 / SCALE_SCROLL_FACTOR
        self.scale  = float(np.clip(self.scale, 0.1, 20.0))
        self._update_grid()
        self._draw_overlay()
        return True

    # =========================================================================
    # Grid Update
    # =========================================================================

    def _update_grid(self):
        if self.coords_3d is None:
            return
        proj     = transform_and_project(
            self.coords_3d,
            self.tx, self.ty,
            self.rx, self.ry, self.rz,
            self.scale, self.d1, self.d2,
            STANDARD_SIZE / 2
        )
        self.gpx = proj[:, 0]
        self.gpy = proj[:, 1]
        self.grid_centre = (
            float(np.mean(self.gpx[:NUM_BEADS_PER_LAYER])),
            float(np.mean(self.gpy[:NUM_BEADS_PER_LAYER])),
        )

    # =========================================================================
    # Button Handlers
    # =========================================================================

    def load_calibration_grid(self):
        """Load and display the calibration image."""
        singleton = SingletonPatient.get_instance()
        path = singleton.patient.caligrid

        if not path or not os.path.exists(path):
            path = QFileDialog.getExistingDirectory(
                self, "Select Calibration Grid Folder"
            )
            if not path:
                return

        try:
            self.img_original = load_calibration_image(path)
            self.img_display  = self.img_original.copy()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        self._reset_state()
        self._display_image(self.img_display)
        self.grid_loaded = True
        QMessageBox.information(self, "Loaded",
            f"Calibration image loaded ({STANDARD_SIZE}×{STANDARD_SIZE}).")

    def overlay_square_grid(self):
        """Create two-layer 3-D bead grid and project onto the image."""
        if not self.grid_loaded:
            QMessageBox.information(self, "No Image",
                "Load calibration grid first.")
            return

        dlg    = QDialog(self)
        dlg.setWindowTitle("Calibration Parameters")
        layout = QFormLayout(dlg)

        sep_spin = QDoubleSpinBox(); sep_spin.setRange(10, 500);   sep_spin.setDecimals(1); sep_spin.setValue(self.layer_separation_mm)
        d1_spin  = QDoubleSpinBox(); d1_spin.setRange(0,  10000);  d1_spin.setDecimals(1);  d1_spin.setValue(self.d1)
        d2_spin  = QDoubleSpinBox(); d2_spin.setRange(0,  10000);  d2_spin.setDecimals(1);  d2_spin.setValue(self.d2)

        layout.addRow("Layer separation (mm):", sep_spin)
        layout.addRow("Source to II (mm):",     d1_spin)
        layout.addRow("Source to knee (mm):",   d2_spin)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if not dlg.exec():
            return

        self.layer_separation_mm = sep_spin.value()
        self.d1                  = d1_spin.value()
        self.d2                  = d2_spin.value()

        self.coords_3d = create_3d_bead_grid(BEAD_SPACING_MM,
                                              self.layer_separation_mm)
        self.tx = self.ty = 0.0
        self.rx = self.ry = self.rz = 0.0
        self.scale = 1.0

        self._update_grid()
        self._draw_overlay()

    def snap_to_beads(self):
        """
        Detect bead centres and snap the overlay grid to them.

        The ideal projected positions (self.gpx / self.gpy at the moment
        the button is pressed) are saved as gpx_ideal / gpy_ideal BEFORE
        detection runs.  These are the distortion-error reference for
        correct_distortion — i.e., they represent where the grid says each
        bead *should* be, and the detected positions show where it actually
        appears in the distorted image.

        After this call:
          self.gpx_ideal / self.gpy_ideal   — ideal (pre-snap) positions
          self.gpx       / self.gpy         — detected (post-snap) positions
          self.missing                       — outlier mask
          self.outside                       — out-of-bounds mask
        """
        if self.gpx is None:
            QMessageBox.information(self, "No Grid",
                "Overlay the square grid first.")
            return

        # --- Save ideal positions BEFORE detection (critical) ---
        self.gpx_ideal = self.gpx.copy()
        self.gpy_ideal = self.gpy.copy()

        # --- Run bead detection, polarity matched to current display state ---
        self.bpx, self.bpy, self.missing, self.outside = detect_beads(
            self.img_display, self.gpx_ideal, self.gpy_ideal
        )

        # --- Update displayed grid to detected positions ---
        self.gpx = self.bpx.copy()
        self.gpy = self.bpy.copy()

        self._draw_overlay()

        front_ok = int(np.sum(~self.missing[:NUM_BEADS_PER_LAYER]
                              & ~self.outside[:NUM_BEADS_PER_LAYER]))
        back_ok  = int(np.sum(~self.missing[NUM_BEADS_PER_LAYER:]
                              & ~self.outside[NUM_BEADS_PER_LAYER:]))
        QMessageBox.information(self, "Snap Complete",
            f"Front layer (RED):  {front_ok} / {NUM_BEADS_PER_LAYER} valid\n"
            f"Back layer  (BLUE): {back_ok}  / {NUM_BEADS_PER_LAYER} valid")

    def correct_distortion(self):
        """
        Fit 9-term polynomial distortion correction and apply to image.

        Mirrors MATLAB correct_fluoro() called from Cal_Correct_Distortion_Callback.
        Uses:
          gpx / gpy           — detected bead positions  (polynomial basis)
          gpx_ideal / gpy_ideal — ideal projections      (error reference)
          missing & outside   — exclusion masks (MATLAB: (~missing)&(~outside))
        """
        if self.gpx_ideal is None:
            QMessageBox.information(self, "Not Snapped",
                "Snap to beads first.")
            return

        try:
            self.ax, self.ay = fit_polynomial_correction(
                self.gpx,       self.gpy,
                self.gpx_ideal, self.gpy_ideal,
                self.missing,   self.outside,
            )
            self.adj_x, self.adj_y = create_correction_maps(self.ax, self.ay)

            self.img_display = apply_correction(
                self.img_display, self.adj_x, self.adj_y
            )
            self._display_image(self.img_display)
            self._update_grid()
            self._draw_overlay()

            QMessageBox.information(self, "Done",
                "Distortion corrected.\n"
                "Press Ctrl+S or 'Save Correction' to save.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", str(e))

    def save_correction(self):
        """
        Write correction maps to a pickle file, then advance to RegistrationState.

        File I/O is performed first.  The state transition only fires after a
        confirmed successful write (mirroring Cal_Save_Dis_Corr_Callback in MATLAB).
        """
        if self.adj_x is None:
            QMessageBox.information(self, "Nothing to Save",
                "Run 'Correct Distortion' first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Correction Parameters",
            "fluoro_correction.pkl", "Pickle files (*.pkl)"
        )
        if not path:
            return

        try:
            with open(path, 'wb') as f:
                pickle.dump([self.adj_x, self.adj_y], f)
        except Exception as e:
            QMessageBox.critical(self, "Save Error",
                f"Could not write file:\n{e}")
            return

        # Advance application state: CalibrationState → RegistrationState
        try:
            singleton = SingletonPatient.get_instance()
            if singleton._state is not None \
                    and hasattr(singleton._state, 'context'):
                singleton._state.context.request_process()
        except Exception as e:
            print(f"Warning: state transition failed after save: {e}")

        QMessageBox.information(self, "Saved",
            f"Saved to: {os.path.basename(path)}")

    # =========================================================================
    # Visualisation
    # =========================================================================

    def _reset_state(self):
        self.coords_3d  = None
        self.gpx        = self.gpy        = None
        self.bpx        = self.bpy        = None
        self.gpx_ideal  = self.gpy_ideal  = None
        self.missing    = self.outside    = None
        self.tx = self.ty = 0.0
        self.rx = self.ry = self.rz = 0.0
        self.scale      = 1.0
        self.d1         = DEFAULT_D1
        self.d2         = DEFAULT_D2
        self.ax         = self.ay         = None
        self.adj_x      = self.adj_y      = None
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
            color = (QColor(255, 60, 60) if i < NUM_BEADS_PER_LAYER
                     else QColor(60, 60, 255))
            dim = ((self.missing is not None and self.missing[i])
                   or (self.outside is not None and self.outside[i]))
            if dim:
                color.setAlpha(80)

            item = QGraphicsEllipseItem(
                QRectF(self.gpx[i] - r, self.gpy[i] - r, 2 * r, 2 * r)
            )
            item.setPen(QPen(color, 1))
            item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            self.scene.addItem(item)
            self.overlay_items.append(item)

        self.scene.update()

    def _fit_view(self):
        self.ui.VTK_display.fitInView(
            self.scene.itemsBoundingRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

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
                    self.img_display  = self.img_original.copy()
                    self.grid_loaded  = True
                    self._display_image(self.img_display)
                except Exception:
                    pass