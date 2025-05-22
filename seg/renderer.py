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
    vtkPolyDataMapper2D,
    vtkTextActor
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

def make_slider(vmin, vmax, init, xpos):
    rep = vtk.vtkSliderRepresentation2D()
    rep.SetMinimumValue(vmin)
    rep.SetMaximumValue(vmax)
    rep.SetValue(init)
    
    # Slider positioning (vertical)
    rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint1Coordinate().SetValue(xpos, 0.1)  # Bottom position
    rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint2Coordinate().SetValue(xpos, 0.4)  # Top position
    
    # Slider appearance
    rep.SetSliderLength(0.008)  # Slider handle size
    rep.SetSliderWidth(0.008)   # Slider handle size 
    rep.SetTubeWidth(0.002)     # Track line thickness
    
    # Remove all decorations
    rep.ShowSliderLabelOff()    # Remove value text
    rep.SetEndCapLength(0.0)    # Remove end caps
    
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
        text_prop.SetFontSize(18)
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

# Main entry point

def main(ct_path: str):
    img = cache_ct(ct_path)
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


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <CT_directory_or_file>")
        sys.exit(1)
    main(sys.argv[1])