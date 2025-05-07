#!/usr/bin/env python3
"""
2D Axial CT Slice Viewer with Caching, Integer Slider, Fixed Plane, and Window/Level Controls

Features:
 1. Load CT (DICOM folder or NIfTI) via `totalseg.load_ct`, cached to `.mha` for fast reloads.
 2. Display axial (XY) slices in a 2D VTK viewer (vtkImageViewer2), keeping the image fixed in the plane.
 3. Slice navigation:
    - Mouse wheel scrolls through slices (no zoom out/in).
    - Draggable slider moves in integer steps, reflects and controls the current slice.
    - On-screen "Slice: X/N" label updates in real time.
 4. Window/Level control via two sliders (window width, level center) affecting the 2D viewer.

Usage:
    python axial_viewer2d.py <CT_source>
"""
import sys
import os
import SimpleITK as sitk
import vtk
from vtkmodules.util import numpy_support
from totalseg import load_ct

# --- Configuration ---
CACHE_DIR = os.path.expanduser('~/.cache/renderer')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)

# --- Helpers ---
def get_cache_path(ct_source: str) -> str:
    base = os.path.basename(ct_source.rstrip(os.sep)).replace(' ', '_')
    return os.path.join(CACHE_DIR, f"{base}.mha")

def load_cached_ct(ct_source: str) -> sitk.Image:
    cache = get_cache_path(ct_source)
    if os.path.exists(cache):
        print(f"Loading CT from cache: {cache}")
        return sitk.ReadImage(cache)
    print(f"Loading CT from source: {ct_source}")
    img = load_ct(ct_source)
    print(f"Caching CT to: {cache}")
    sitk.WriteImage(img, cache)
    return img

# Convert SimpleITK to vtkImageData
def sitk_to_vtk(sitk_img):
    arr = sitk.GetArrayFromImage(sitk_img)  # shape (Z, Y, X)
    Z, Y, X = arr.shape
    vtk_img = vtk.vtkImageData()
    vtk_img.SetDimensions(X, Y, Z)
    vtk_img.SetExtent(0, X-1, 0, Y-1, 0, Z-1)
    vtk_img.SetSpacing(sitk_img.GetSpacing())
    vtk_img.SetOrigin(sitk_img.GetOrigin())
    vtk_arr = numpy_support.numpy_to_vtk(arr.ravel(order='C'), deep=True,
        array_type=numpy_support.get_vtk_array_type(arr.dtype))
    vtk_img.GetPointData().SetScalars(vtk_arr)
    return vtk_img, arr

# Slider factory for 2D UI
def make_slider(title, mn, mx, init, p1, p2):
    rep = vtk.vtkSliderRepresentation2D()
    rep.SetTitleText(title)
    rep.SetMinimumValue(mn)
    rep.SetMaximumValue(mx)
    rep.SetValue(init)
    rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint1Coordinate().SetValue(*p1)
    rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint2Coordinate().SetValue(*p2)
    rep.SetSliderLength(0.02)
    rep.SetSliderWidth(0.03)
    rep.SetTubeWidth(0.005)
    return rep

# Main viewer
def main(ct_source):
    # Load and cache CT volume
    sitk_img = load_cached_ct(ct_source)
    vtk_img, arr = sitk_to_vtk(sitk_img)

    num_slices = arr.shape[0]
    hu_min, hu_max = int(arr.min()), int(arr.max())
    init_slice = num_slices // 2
    init_window = 5.7e3
    init_level = 1.98e3

    # VTK 2D viewer setup
    viewer = vtk.vtkImageViewer2()
    viewer.SetInputData(vtk_img)
    viewer.SetSlice(init_slice)
    ren_win = viewer.GetRenderWindow()
    ren = viewer.GetRenderer()
    iren = vtk.vtkRenderWindowInteractor()
    viewer.SetupInteractor(iren)

    ren.ResetCamera()
    ren_win.SetSize(600, 600)

    # On-screen slice counter
    text_actor = vtk.vtkTextActor()
    tp = text_actor.GetTextProperty()
    tp.SetFontSize(24)
    tp.BoldOn()
    text_actor.SetPosition(10, 10)
    ren.AddActor2D(text_actor)
    text_actor.SetInput(f"Slice: {init_slice+1}/{num_slices}")

    # Slider for slice index
    slice_rep = make_slider("Slice", 0, num_slices-1, init_slice, (0.1, 0.05), (0.9, 0.05))
    slice_slider = vtk.vtkSliderWidget()
    slice_slider.SetInteractor(iren)
    slice_slider.SetRepresentation(slice_rep)
    slice_slider.SetAnimationModeToJump()
    slice_slider.EnabledOn()

    def on_slice(obj, event):
        val = int(round(obj.GetRepresentation().GetValue()))
        viewer.SetSlice(val)
        text_actor.SetInput(f"Slice: {val+1}/{num_slices}")
        slice_rep.SetValue(val)
        ren_win.Render()
    slice_slider.AddObserver("EndInteractionEvent", on_slice)

    # Mouse wheel integration
    def wheel_forward(obj, event):
        current = viewer.GetSlice()
        val = min(num_slices-1, current+1)
        viewer.SetSlice(val)
        text_actor.SetInput(f"Slice: {val+1}/{num_slices}")
        slice_rep.SetValue(val)
        ren_win.Render()

    def wheel_backward(obj, event):
        current = viewer.GetSlice()
        val = max(0, current-1)
        viewer.SetSlice(val)
        text_actor.SetInput(f"Slice: {val+1}/{num_slices}")
        slice_rep.SetValue(val)
        ren_win.Render()

    iren.AddObserver("MouseWheelForwardEvent", wheel_forward)
    iren.AddObserver("MouseWheelBackwardEvent", wheel_backward)

    # Window/Level sliders
    win_rep = make_slider("Window", 1, hu_max - hu_min, init_window, (0.1, 0.9), (0.4, 0.9))
    lvl_rep = make_slider("Level", hu_min, hu_max, init_level, (0.6, 0.9), (0.9, 0.9))
    win_slider = vtk.vtkSliderWidget(); win_slider.SetInteractor(iren);
    win_slider.SetRepresentation(win_rep); win_slider.SetAnimationModeToJump(); win_slider.EnabledOn()
    lvl_slider = vtk.vtkSliderWidget(); lvl_slider.SetInteractor(iren);
    lvl_slider.SetRepresentation(lvl_rep); lvl_slider.SetAnimationModeToJump(); lvl_slider.EnabledOn()

    def on_win(obj, event):
        w = int(round(obj.GetRepresentation().GetValue()))
        l = int(round(lvl_rep.GetValue()))
        viewer.SetColorWindow(w)
        viewer.SetColorLevel(l)
        ren_win.Render()

    def on_lvl(obj, event):
        w = int(round(win_rep.GetValue()))
        l = int(round(obj.GetRepresentation().GetValue()))
        viewer.SetColorWindow(w)
        viewer.SetColorLevel(l)
        ren_win.Render()

    win_slider.AddObserver("InteractionEvent", on_win)
    lvl_slider.AddObserver("InteractionEvent", on_lvl)

    # Initialize and start
    ren_win.Render()
    iren.Initialize()
    print("Starting 2D axial CT viewer...")
    iren.Start()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <CT_source>")
        sys.exit(1)
    main(sys.argv[1])
