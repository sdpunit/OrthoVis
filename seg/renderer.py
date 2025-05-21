#!/usr/bin/env python3
"""
2D CT Quad-Viewer (Axial/Coronal/Sagittal) with Per-Quadrant Scrolling, Ctrl-Zoom,
Gold Crosshair, and Modern Window/Level Sliders

Features:
 1. Single RenderWindow split into 3 active viewports (axial, coronal, sagittal) and
    crosshair overlay in a reserved top-right quadrant.
 2. Mouse wheel scrolls slices in the quadrant under the cursor; Ctrl + wheel zooms.
 3. Persistent slice count labels in each quadrant showing "<View>\nSlice: X/N".
 4. Gold crosshair overlay across all quadrants.
 5. Global Window/Level sliders rendered on the right edge with slim bars and jump mode.
"""
import os
import sys
import SimpleITK as sitk
import vtk
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules.vtkInteractionImage import vtkImageViewer2
from vtkmodules.vtkRenderingCore import (
    vtkRenderWindow,
    vtkRenderer,
    vtkRenderWindowInteractor,
    vtkActor2D,
    vtkTextMapper,
    vtkTextProperty,
    vtkPolyDataMapper2D
)
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkCellArray
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.util import numpy_support
from totalseg import load_ct

# Caching directory
CACHE_DIR = os.path.expanduser('~/.cache/renderer')
os.makedirs(CACHE_DIR, exist_ok=True)

# Helper: cache or load CT image

def cache_ct(path: str):
    cache_file = os.path.join(CACHE_DIR, os.path.basename(path.rstrip(os.sep)) + '.mha')
    if os.path.exists(cache_file):
        return sitk.ReadImage(cache_file)
    img = load_ct(path)
    sitk.WriteImage(img, cache_file)
    return img

# Convert SimpleITK image to vtkImageData

def sitk_to_vtk(img):
    arr = sitk.GetArrayFromImage(img)
    Z, Y, X = arr.shape
    vtk_img = vtk.vtkImageData()
    vtk_img.SetDimensions(X, Y, Z)
    vtk_img.SetSpacing(img.GetSpacing())
    vtk_img.SetOrigin(img.GetOrigin())
    vtk_arr = numpy_support.numpy_to_vtk(
        arr.ravel(), deep=True,
        array_type=numpy_support.get_vtk_array_type(arr.dtype)
    )
    vtk_img.GetPointData().SetScalars(vtk_arr)
    return vtk_img, arr

# Create a thin vertical slider with jump animation

def make_slider(label, vmin, vmax, init, xpos):
    rep = vtk.vtkSliderRepresentation2D()
    rep.SetMinimumValue(vmin)
    rep.SetMaximumValue(vmax)
    rep.SetValue(init)
    
    # Slider positioning (vertical line)
    rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint1Coordinate().SetValue(xpos, 0.15)  # Bottom position
    rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint2Coordinate().SetValue(xpos, 0.85)  # Top position
    
    # Slider appearance
    rep.SetSliderLength(0.008)  # Slider handle size
    rep.SetSliderWidth(0.008)   # Slider handle size 
    rep.SetTubeWidth(0.002)     # Track line thickness
    
    # Remove all decorations
    rep.ShowSliderLabelOff()    # Remove value text
    rep.SetEndCapLength(0.0)    # Remove end caps
    
    # Label properties (positioned above slider)
    rep.SetTitleText(label)
    title_prop = rep.GetTitleProperty()
    title_prop.SetFontSize(12)
    title_prop.SetColor(1, 1, 1)  # White
    title_prop.SetJustificationToCentered()
    title_prop.SetVerticalJustificationToBottom()
    rep.SetTitleHeight(0.03)  # Text size 
    
    # Critical: Disable all highlighting that causes traces
    rep.GetSliderProperty().SetColor(1, 1, 0)  # Yellow slider
    rep.GetSelectedProperty().SetColor(1, 1, 0)  # Same yellow when selected
    rep.GetTubeProperty().SetColor(0.4, 0.4, 0.4)  # Dark gray track
    
    # Eliminate trace artifacts completely
    rep.GetSliderProperty().SetOpacity(1.0)
    rep.GetSelectedProperty().SetOpacity(1.0)
    rep.GetTubeProperty().SetOpacity(1.0)
    
    return rep

# Wrapper for each quadrant viewer
class SliceViewer:
    def __init__(self, vtk_img, arr, orientation, viewport, name, render_window):
        self.name = name
        self.viewport = viewport
        # Set up vtkImageViewer2
        self.viewer = vtkImageViewer2()
        self.viewer.SetInputData(vtk_img)
        # Choose orientation
        axis = 0
        if orientation == 'coronal':
            self.viewer.SetSliceOrientationToXZ()
            axis = 1
        elif orientation == 'sagittal':
            self.viewer.SetSliceOrientationToYZ()
            axis = 2
        # Slice range
        self.min_slice, self.max_slice = 0, arr.shape[axis] - 1
        self.slice = arr.shape[axis] // 2
        self.viewer.SetSlice(self.slice)
        # Renderer configuration
        renderer = self.viewer.GetRenderer()
        renderer.SetViewport(*viewport)
        renderer.SetBackground(0, 0, 0)
        render_window.AddRenderer(renderer)
        self.viewer.SetRenderWindow(render_window)
        # Slice counter text
        text_prop = vtkTextProperty()
        text_prop.SetFontSize(14)
        text_prop.SetColor(1, 1, 1)
        self.mapper = vtkTextMapper()
        self.mapper.SetTextProperty(text_prop)
        self.actor = vtkActor2D()
        self.actor.SetMapper(self.mapper)
        self.actor.SetPosition(5, 5)
        renderer.AddActor2D(self.actor)
        self.update_label()

    def update_label(self):
        self.mapper.SetInput(f"{self.name}\nSlice: {self.slice+1}/{self.max_slice+1}")

    def move(self, delta):
        new_slice = min(max(self.min_slice, self.slice + delta), self.max_slice)
        if new_slice != self.slice:
            self.slice = new_slice
            self.viewer.SetSlice(self.slice)
            self.update_label()
        self.viewer.Render()

    def contains(self, xn, yn):
        x0, y0, x1, y1 = self.viewport
        return x0 <= xn <= x1 and y0 <= yn <= y1

# Draw gold crosshair overlay

def add_crosshair(render_window):
    overlay = vtkRenderer()
    overlay.SetLayer(1)
    overlay.InteractiveOff()
    overlay.SetViewport(0.0, 0.0, 1.0, 1.0)
    pts = vtkPoints()
    pts.InsertNextPoint(0, 0.5, 0)
    pts.InsertNextPoint(1, 0.5, 0)
    pts.InsertNextPoint(0.5, 0, 0)
    pts.InsertNextPoint(0.5, 1, 0)
    lines = vtkCellArray()
    lines.InsertNextCell(2)
    lines.InsertCellPoint(0)
    lines.InsertCellPoint(1)
    lines.InsertNextCell(2)
    lines.InsertCellPoint(2)
    lines.InsertCellPoint(3)
    pd = vtkPolyData()
    pd.SetPoints(pts)
    pd.SetLines(lines)
    mapper = vtkPolyDataMapper2D()
    mapper.SetInputData(pd)
    actor = vtkActor2D()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(1, 0.84, 0)
    actor.GetProperty().SetLineWidth(1)
    overlay.AddActor2D(actor)
    render_window.AddRenderer(overlay)
    return overlay

class QuadStyle(vtkInteractorStyleImage):
    def __init__(self, viewers):
        super().__init__()
        self.viewers = viewers
        # Remove default wheel observers
        self.RemoveObservers('MouseWheelForwardEvent')
        self.RemoveObservers('MouseWheelBackwardEvent')
        # Add our custom wheel handlers
        self.AddObserver('MouseWheelForwardEvent', self.wheel_forward)
        self.AddObserver('MouseWheelBackwardEvent', self.wheel_backward)

    def pick_viewer(self):
        x, y = self.GetInteractor().GetEventPosition()
        w, h = self.GetInteractor().GetRenderWindow().GetSize()
        xn, yn = x / w, y / h
        for sv in self.viewers:
            if sv.contains(xn, yn):
                return sv
        return None

    def wheel_forward(self, obj, event):
        sv = self.pick_viewer()
        if not sv:
            return

        if self.GetInteractor().GetControlKey():
            # —— ZOOM IN ——
            cam = sv.viewer.GetRenderer().GetActiveCamera()
            cam.ParallelProjectionOn()
            cam.Zoom(1.1)
            sv.viewer.Render()
        else:
            # —— SLICE UP ——
            sv.move(1)

        self.GetInteractor().GetRenderWindow().Render()

    def wheel_backward(self, obj, event):
        sv = self.pick_viewer()
        if not sv:
            return

        if self.GetInteractor().GetControlKey():
            # —— ZOOM OUT ——
            cam = sv.viewer.GetRenderer().GetActiveCamera()
            cam.ParallelProjectionOn()
            cam.Zoom(0.9)
            sv.viewer.Render()
        else:
            # —— SLICE DOWN ——
            sv.move(-1)

        self.GetInteractor().GetRenderWindow().Render()

# Main entrypoint

def main(ct_path: str):
    img = cache_ct(ct_path)
    vtk_img, arr = sitk_to_vtk(img)

    render_window = vtkRenderWindow()
    render_window.SetSize(900, 900)
    render_window.SetNumberOfLayers(2)

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

    # Add crosshair overlay
    overlay_renderer = add_crosshair(render_window)

    # Create interactor and style
    interactor = vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.SetInteractorStyle(QuadStyle(viewers))

    # Window/Level sliders on right
    hu_min, hu_max = int(arr.min()), int(arr.max())
    win_rep = make_slider('W', 1, hu_max - hu_min, hu_max - hu_min, 0.96)
    lvl_rep = make_slider('L', hu_min, hu_max, (hu_max + hu_min)//2, 0.92)

    win_wid = vtk.vtkSliderWidget()
    lvl_wid = vtk.vtkSliderWidget()

    for wid, rep in ((win_wid, win_rep), (lvl_wid, lvl_rep)):
        wid.SetInteractor(interactor)
        wid.SetRepresentation(rep)
        wid.SetAnimationModeToJump()
        wid.SetCurrentRenderer(overlay_renderer)
        wid.EnabledOn()

    def wl_callback(obj, event):
        w = int(round(win_rep.GetValue()))
        l = int(round(lvl_rep.GetValue()))
        for sv in viewers:
            sv.viewer.SetColorWindow(w)
            sv.viewer.SetColorLevel(l)
        render_window.Render()

    win_wid.AddObserver('InteractionEvent', wl_callback)
    lvl_wid.AddObserver('InteractionEvent', wl_callback)

    # Start interaction
    render_window.Render()
    interactor.Initialize()
    interactor.Start()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <CT_directory_or_file>")
        sys.exit(1)
    main(sys.argv[1])