"""
Fluoroscopy Calibration Module

Purpose:
    Corrects pincushion distortion in fluoroscopy images caused by X-ray beam 
    projection onto the curved input surface of the image intensifier.

Workflow:
    1. Load fluoroscopy image of calibration grid (perspex cube with tantalum beads)
    2. Overlay ideal grid where beads should be without distortion
    3. Detect actual bead positions in distorted image
    4. Snap ideal grid points to detected beads (establish correspondence)
    5. Fit cubic polynomial warp from distorted → undistorted coordinates
    6. Preview corrected image and save correction maps for later use

Usage:
    - Load Calibration Grid: Import fluoroscopy image of calibration frame
    - Overlay Square Grid: Place ideal grid over image (adjust rows/cols as needed)
    - Snap to Beads: Auto-detect beads and match to grid points
    - Correct Distortion: Fit warp model and preview corrected image
    - Save (Ctrl+S): Export correction maps as .npz file
"""

from __future__ import annotations
import os
import json
import numpy as np
import cv2
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QImage, QPixmap, QPen, QBrush, QColor, QAction
from PySide6.QtWidgets import (
    QWidget, QFileDialog, QGraphicsScene, QGraphicsPixmapItem, 
    QGraphicsEllipseItem, QMessageBox, QGraphicsView
)

from frontend_pages.calibration.ui_calibration_window import Ui_Form


# ============================================================================
# Image Processing Utilities
# ============================================================================

def find_dicom_directory(base_dir: str) -> Optional[str]:
    """
    Find directory containing DICOM files.
    First checks base directory, then searches subdirectories.
    """
    if contains_dicom_files(base_dir):
        return base_dir
    
    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and contains_dicom_files(item_path):
                return item_path
    except Exception as e:
        print(f"Error searching for DICOM files: {e}")
    
    return None


def contains_dicom_files(directory: str) -> bool:
    """Check if directory contains DICOM files (files without extension or .dcm)"""
    try:
        files = os.listdir(directory)
        # DICOM files typically have no extension or .dcm extension
        dicom_files = [f for f in files if '.' not in f or f.endswith('.dcm')]
        return len(dicom_files) > 0
    except:
        return False


def get_first_dicom_file(directory: str) -> Optional[str]:
    """Get the first DICOM file from a directory"""
    try:
        files = os.listdir(directory)
        dicom_files = [f for f in files if '.' not in f or f.endswith('.dcm')]
        if dicom_files:
            return os.path.join(directory, dicom_files[0])
    except:
        pass
    return None


def load_image(path: str) -> np.ndarray:
    """
    Load image from various formats (PNG, JPG, TIFF, DICOM).
    If path is a directory, searches for DICOM files inside.
    
    Returns:
        Grayscale image as uint8 numpy array
    """
    # If path is a directory, find DICOM directory and get first file
    if os.path.isdir(path):
        dicom_dir = find_dicom_directory(path)
        if dicom_dir is None:
            raise ValueError(f"No DICOM files found in folder: {path}")
        
        dicom_file = get_first_dicom_file(dicom_dir)
        if dicom_file is None:
            raise ValueError(f"No DICOM files found in directory: {dicom_dir}")
        
        path = dicom_file
        print(f"Loading DICOM file: {path}")
    
    ext = os.path.splitext(path)[1].lower()
    
    # Standard image formats
    if ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"]:
        img = cv2.imread(path, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
        if img is None:
            raise ValueError(f"Failed to load image: {path}")
        
        # Convert to grayscale if needed
        if img.ndim == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Normalize to uint8
        if img.dtype != np.uint8:
            img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        return img
    
    # Try DICOM format (for .dcm files or no extension)
    try:
        import pydicom
        print(f"Reading DICOM file: {path}")
        ds = pydicom.dcmread(path)
        
        # Get pixel array and ensure it's a proper numpy array
        arr = ds.pixel_array
        print(f"DICOM pixel array shape: {arr.shape}, dtype: {arr.dtype}")
        
        # Convert to float32 for processing
        arr = np.array(arr, dtype=np.float32)
        
        # Handle different DICOM photometric interpretations
        if hasattr(ds, 'PhotometricInterpretation'):
            print(f"Photometric interpretation: {ds.PhotometricInterpretation}")
            if ds.PhotometricInterpretation == 'MONOCHROME1':
                # Invert for MONOCHROME1 (lower values = brighter)
                arr = arr.max() - arr
        
        # Normalize to 0-255 range
        arr_min = arr.min()
        arr_max = arr.max()
        print(f"Array range: {arr_min} to {arr_max}")
        
        if arr_max > arr_min:
            arr = ((arr - arr_min) / (arr_max - arr_min) * 255.0).astype(np.uint8)
        else:
            arr = np.zeros_like(arr, dtype=np.uint8)
        
        print(f"Final array shape: {arr.shape}, dtype: {arr.dtype}")
        return arr
        
    except ImportError:
        raise ValueError("DICOM support requires pydicom package")
    except Exception as e:
        print(f"DICOM loading error details: {e}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Failed to load DICOM: {e}")


def numpy_to_qpixmap(arr: np.ndarray) -> QPixmap:
    """Convert grayscale numpy array to QPixmap for display."""
    if arr.dtype != np.uint8:
        arr = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    h, w = arr.shape[:2]
    qimg = QImage(arr.data, w, h, w, QImage.Format_Grayscale8)
    return QPixmap.fromImage(qimg.copy())


def detect_beads(img: np.ndarray) -> np.ndarray:
    """
    Detect circular bead centers using blob detection.
    
    Returns:
        Nx2 array of (x, y) coordinates
    """
    params = cv2.SimpleBlobDetector_Params()
    
    # Filter by circularity (beads should be round)
    params.filterByCircularity = True
    params.minCircularity = 0.65
    
    # Filter by area (adjust based on your image resolution)
    params.filterByArea = True
    params.minArea = 10
    params.maxArea = 5000
    
    # Filter by inertia ratio (roundness)
    params.filterByInertia = True
    params.minInertiaRatio = 0.2
    
    # Threshold settings
    params.minThreshold = 10
    params.maxThreshold = 220
    params.thresholdStep = 10
    
    detector = cv2.SimpleBlobDetector_create(params)
    keypoints = detector.detect(img)
    
    if not keypoints:
        return np.zeros((0, 2), dtype=np.float32)
    
    return np.array([kp.pt for kp in keypoints], dtype=np.float32)


def match_points_greedy(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """
    Match each target point to nearest unique source point (greedy assignment).
    
    Args:
        source: Nx2 array of available points (e.g., detected beads)
        target: Mx2 array of points to match (e.g., ideal grid)
    
    Returns:
        Array of indices where source[match[i]] is matched to target[i]
        Returns -1 for unmatched targets
    """
    if len(source) == 0 or len(target) == 0:
        return np.array([], dtype=int)
    
    available = list(range(len(source)))
    matches = []
    
    for tgt in target:
        if not available:
            matches.append(-1)
            continue
        
        # Find nearest available source point
        candidates = source[available]
        distances = np.sum((candidates - tgt)**2, axis=1)
        nearest_idx = int(np.argmin(distances))
        
        matches.append(available[nearest_idx])
        del available[nearest_idx]
    
    return np.array(matches, dtype=int)


# ============================================================================
# Cubic Warp Model
# ============================================================================

def cubic_design_matrix(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Create design matrix for 2D cubic polynomial (10 terms).
    Terms: [1, x, y, x², xy, y², x³, x²y, xy², y³]
    """
    return np.column_stack([
        np.ones_like(x),
        x, y,
        x*x, x*y, y*y,
        x*x*x, x*x*y, x*y*y, y*y*y
    ])


def fit_cubic_warp(distorted: np.ndarray, undistorted: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fit cubic polynomial warp from distorted to undistorted coordinates.
    
    Args:
        distorted: Nx2 array of distorted (x, y) positions
        undistorted: Nx2 array of corresponding undistorted (x, y) positions
    
    Returns:
        (coeff_x, coeff_y): Coefficients for x and y transformations (10 each)
    """
    X = cubic_design_matrix(distorted[:, 0], distorted[:, 1])
    
    # Solve for x and y transformations separately
    coeff_x, *_ = np.linalg.lstsq(X, undistorted[:, 0], rcond=None)
    coeff_y, *_ = np.linalg.lstsq(X, undistorted[:, 1], rcond=None)
    
    return coeff_x.astype(np.float32), coeff_y.astype(np.float32)


def create_remap_arrays(coeff_x: np.ndarray, coeff_y: np.ndarray, 
                        width: int, height: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create dense remap arrays for cv2.remap() using cubic warp coefficients.
    
    Returns:
        (mapx, mapy): Arrays for remapping distorted → undistorted
    """
    yy, xx = np.meshgrid(
        np.arange(height, dtype=np.float32),
        np.arange(width, dtype=np.float32),
        indexing='ij'
    )
    
    # Evaluate polynomial at each pixel
    x, y = xx, yy
    
    def eval_poly(c):
        return (c[0] + c[1]*x + c[2]*y + c[3]*x*x + c[4]*x*y + c[5]*y*y +
                c[6]*x*x*x + c[7]*x*x*y + c[8]*x*y*y + c[9]*y*y*y)
    
    mapx = eval_poly(coeff_x).astype(np.float32)
    mapy = eval_poly(coeff_y).astype(np.float32)
    
    return mapx, mapy


def apply_distortion_correction(img: np.ndarray, mapx: np.ndarray, 
                                mapy: np.ndarray) -> np.ndarray:
    """Apply distortion correction using precomputed remap arrays."""
    return cv2.remap(img, mapx, mapy, 
                     interpolation=cv2.INTER_LINEAR, 
                     borderMode=cv2.BORDER_CONSTANT)


# ============================================================================
# Main Calibration Widget
# ============================================================================

class Calibration(QWidget):
    """
    Fluoroscopy calibration interface for correcting image distortion.
    
    Attributes:
        img_original: Original loaded image
        img_display: Current display image (may be corrected)
        grid_ideal: Ideal grid positions before snapping (Nx2 array)
        grid_snapped: Grid positions after snapping to beads (Nx2 array)
        beads_detected: Detected bead positions (Mx2 array)
        warp_coeff_x, warp_coeff_y: Cubic warp coefficients
        remap_x, remap_y: Dense remap arrays for distortion correction
    """
    
    # Grid configuration (adjust based on your calibration frame)
    GRID_ROWS = 7
    GRID_COLS = 9
    GRID_MARGIN = 0.10  # 10% margin from image edges
    
    def __init__(self):
        super().__init__()
        
        # Setup UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.titlebar.ui.title.setText("Calibration")
        
        # Highlight calibration in sidebar
        self.ui.sidebar.ui.calibration.setStyleSheet("""
            QPushButton {
                color: white; 
                background-color: #6f8ab7; 
                border: none; 
                padding: 10px 25px;
            }
        """)
        
        # Setup graphics view for image display
        self.scene = QGraphicsScene(self)
        self.ui.VTK_display.setScene(self.scene)
        self.ui.VTK_display.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Internal state
        self.img_original: Optional[np.ndarray] = None
        self.img_display: Optional[np.ndarray] = None
        self.base_pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.overlay_items: list[QGraphicsEllipseItem] = []
        
        self.grid_ideal: Optional[np.ndarray] = None
        self.grid_snapped: Optional[np.ndarray] = None
        self.beads_detected: Optional[np.ndarray] = None
        
        self.warp_coeff_x: Optional[np.ndarray] = None
        self.warp_coeff_y: Optional[np.ndarray] = None
        self.remap_x: Optional[np.ndarray] = None
        self.remap_y: Optional[np.ndarray] = None
        
        # Connect button signals
        self.ui.pushButton.clicked.connect(self.load_calibration_grid)
        self.ui.pushButton_2.clicked.connect(self.invert_colors)
        self.ui.pushButton_3.clicked.connect(self.overlay_grid)
        self.ui.pushButton_4.clicked.connect(self.snap_to_beads)
        self.ui.pushButton_5.clicked.connect(self.correct_distortion)
        
        # Add keyboard shortcut for save
        save_action = QAction("Save Correction", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_correction)
        self.addAction(save_action)
    
    # ========================================================================
    # Button Handlers
    # ========================================================================
    
    def load_calibration_grid(self):
        """Load fluoroscopy image of calibration frame (folder with DICOM)."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Fluoroscopy DICOM Files",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not path:
            return
        
        try:
            print(f"Selected path: {path}")
            print(f"Path is directory: {os.path.isdir(path)}")
            
            img = load_image(path)
            print(f"Successfully loaded image: {img.shape}, dtype: {img.dtype}")
        except Exception as e:
            print(f"Error loading image: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Load Error", str(e))
            return
        
        # Reset state
        self.img_original = img.copy()
        self.img_display = img.copy()
        self.grid_ideal = None
        self.grid_snapped = None
        self.beads_detected = None
        self.warp_coeff_x = None
        self.warp_coeff_y = None
        self.remap_x = None
        self.remap_y = None
        
        self._display_image(self.img_display)
        self._clear_overlay()
    
    def invert_colors(self):
        """Invert image colors for better visibility of beads."""
        if self.img_display is None:
            QMessageBox.information(self, "No Image", "Load a calibration frame first.")
            return
        
        self.img_display = cv2.bitwise_not(self.img_display)
        self._display_image(self.img_display)
        self._redraw_overlay()
    
    def overlay_grid(self):
        """Overlay ideal square grid over image."""
        if self.img_original is None:
            QMessageBox.information(self, "No Image", "Load a calibration frame first.")
            return
        
        h, w = self.img_original.shape[:2]
        
        # Calculate grid bounds (with margins)
        margin_x = int(self.GRID_MARGIN * w)
        margin_y = int(self.GRID_MARGIN * h)
        x0, y0 = margin_x, margin_y
        x1, y1 = w - margin_x, h - margin_y
        
        # Create regular grid
        xs = np.linspace(x0, x1, self.GRID_COLS, dtype=np.float32)
        ys = np.linspace(y0, y1, self.GRID_ROWS, dtype=np.float32)
        gx, gy = np.meshgrid(xs, ys)
        
        self.grid_ideal = np.column_stack([gx.ravel(), gy.ravel()])
        self.grid_snapped = self.grid_ideal.copy()
        
        self._draw_overlay()
    
    def snap_to_beads(self):
        """Detect beads and snap grid points to nearest beads."""
        if self.img_original is None:
            QMessageBox.information(self, "No Image", "Load a calibration frame first.")
            return
        
        if self.grid_ideal is None:
            QMessageBox.information(self, "No Grid", "Overlay a grid first.")
            return
        
        # Detect beads
        self.beads_detected = detect_beads(self.img_display)
        
        if len(self.beads_detected) == 0:
            QMessageBox.warning(
                self, 
                "No Beads Detected",
                "No beads found. Try inverting the image or adjusting lighting."
            )
            return
        
        # Match grid points to beads
        matches = match_points_greedy(self.beads_detected, self.grid_ideal)
        
        # Count successful matches
        valid_matches = matches >= 0
        match_rate = valid_matches.sum() / len(matches)
        
        if match_rate < 0.6:
            QMessageBox.warning(
                self,
                "Poor Match",
                f"Only {match_rate*100:.0f}% of grid points matched to beads.\n"
                "Consider adjusting grid size or image quality."
            )
        
        # Update snapped positions
        self.grid_snapped = self.grid_ideal.copy()
        self.grid_snapped[valid_matches] = self.beads_detected[matches[valid_matches]]
        
        self._draw_overlay()
        
        QMessageBox.information(
            self,
            "Snap Complete",
            f"Matched {valid_matches.sum()} of {len(matches)} grid points to beads."
        )
    
    def correct_distortion(self):
        """Fit cubic warp and preview corrected image."""
        if self.img_original is None:
            QMessageBox.information(self, "No Image", "Load a calibration frame first.")
            return
        
        if self.grid_ideal is None or self.grid_snapped is None:
            QMessageBox.information(
                self, 
                "No Grid",
                "Overlay and snap the grid first."
            )
            return
        
        # Fit warp: distorted (snapped) → undistorted (ideal)
        self.warp_coeff_x, self.warp_coeff_y = fit_cubic_warp(
            self.grid_snapped, 
            self.grid_ideal
        )
        
        # Create remap arrays
        h, w = self.img_original.shape[:2]
        self.remap_x, self.remap_y = create_remap_arrays(
            self.warp_coeff_x, 
            self.warp_coeff_y,
            w, h
        )
        
        # Apply correction
        corrected = apply_distortion_correction(
            self.img_display,
            self.remap_x,
            self.remap_y
        )
        
        self.img_display = corrected
        self._display_image(corrected)
        
        # Reset overlay to ideal positions
        self.grid_snapped = self.grid_ideal.copy()
        self._draw_overlay()
        
        # Calculate and display fit quality
        rms_error = self._calculate_rms_error()
        QMessageBox.information(
            self,
            "Correction Applied",
            f"Distortion correction applied.\n"
            f"RMS error: {rms_error:.2f} pixels\n\n"
            f"Press Ctrl+S to save correction maps."
        )
    
    def save_correction(self):
        """Save distortion correction maps and coefficients."""
        if self.remap_x is None or self.remap_y is None:
            QMessageBox.information(
                self,
                "Nothing to Save",
                "Run distortion correction first."
            )
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Distortion Correction",
            "distortion_correction.npz",
            "NumPy Archive (*.npz)"
        )
        
        if not path:
            return
        
        # Save maps and metadata
        np.savez(
            path,
            mapx=self.remap_x,
            mapy=self.remap_y,
            coeff_x=self.warp_coeff_x,
            coeff_y=self.warp_coeff_y,
            grid_ideal=self.grid_ideal,
            grid_snapped=self.grid_snapped,
            metadata=json.dumps({
                "model": "cubic_polynomial",
                "version": 1,
                "grid_rows": self.GRID_ROWS,
                "grid_cols": self.GRID_COLS
            })
        )
        
        QMessageBox.information(
            self,
            "Saved",
            f"Distortion correction saved:\n{os.path.basename(path)}"
        )
    
    # ========================================================================
    # Visualization
    # ========================================================================
    
    def _display_image(self, img: np.ndarray):
        """Display image in graphics view."""
        self.scene.clear()
        self.overlay_items.clear()
        
        pixmap = numpy_to_qpixmap(img)
        self.base_pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.base_pixmap_item)
        
        self._fit_view()
    
    def _clear_overlay(self):
        """Remove all overlay items from scene."""
        for item in self.overlay_items:
            self.scene.removeItem(item)
        self.overlay_items.clear()
        self.scene.update()
    
    def _draw_overlay(self):
        """Draw grid overlay on image."""
        self._clear_overlay()
        
        if self.grid_snapped is None:
            return
        
        # Draw markers at grid positions
        color = QColor(220, 50, 50)  # Red
        pen = QPen(color, 2)
        brush = QBrush(Qt.BrushStyle.NoBrush)
        radius = 6
        
        for x, y in self.grid_snapped:
            item = QGraphicsEllipseItem(QRectF(x - radius, y - radius, 2*radius, 2*radius))
            item.setPen(pen)
            item.setBrush(brush)
            self.scene.addItem(item)
            self.overlay_items.append(item)
        
        self.scene.update()
    
    def _redraw_overlay(self):
        """Redraw overlay (after image changes)."""
        if self.base_pixmap_item is not None:
            self._draw_overlay()
    
    def _fit_view(self):
        """Fit scene to view."""
        self.ui.VTK_display.fitInView(
            self.scene.itemsBoundingRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )
    
    def _calculate_rms_error(self) -> float:
        """Calculate RMS error of warp fit."""
        if self.grid_snapped is None or self.grid_ideal is None:
            return float('nan')
        
        # Transform snapped points through warp
        X = cubic_design_matrix(self.grid_snapped[:, 0], self.grid_snapped[:, 1])
        pred_x = X @ self.warp_coeff_x
        pred_y = X @ self.warp_coeff_y
        predicted = np.column_stack([pred_x, pred_y])
        
        # Calculate error
        errors = np.linalg.norm(predicted - self.grid_ideal, axis=1)
        return float(np.sqrt(np.mean(errors**2)))
    
    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    def resizeEvent(self, event):
        """Handle window resize."""
        super().resizeEvent(event)
        self._fit_view()