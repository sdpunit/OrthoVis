#!/usr/bin/env python3
"""
Single-view CT Slice Viewer with caching, slice slider, wheel scrolling, and window/level controls

Features:
 1. Load CT (DICOM folder or NIfTI file) via `totalseg.load_ct`, cached as .mha for fast reloads.
 2. Display one axial slice in VTK.
 3. Slice navigation:
    - Mouse wheel scrolls through slices (no zoom).
    - Draggable slider reflects and controls the current slice.
    - On-screen "Slice: X/N" label.
 4. Window/Level control via two sliders (window width, level center).

Usage:
    python axial_viewer.py <DICOM_dir|NIfTI_file>
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
    name = os.path.basename(ct_source.rstrip(os.sep)).replace(' ', '_')
    return os.path.join(CACHE_DIR, f"{name}.mha")

def load_cached_ct(ct_source: str) -> sitk.Image:
    cache_path = get_cache_path(ct_source)
    if os.path.exists(cache_path):
        print(f"Loading CT from cache: {cache_path}")
        return sitk.ReadImage(cache_path)
    print(f"No cache found. Loading CT from source: {ct_source}")
    ct_img = load_ct(ct_source)
    print(f"Caching CT volume to: {cache_path}")
    sitk.WriteImage(ct_img, cache_path)
    return ct_img

# Convert SITK to VTK and set extent
def sitk_to_vtk(sitk_img):
    arr = sitk.GetArrayFromImage(sitk_img)  # (depth, height, width)
    depth, height, width = arr.shape
    vtk_img = vtk.vtkImageData()
    vtk_img.SetDimensions(width, height, depth)
    vtk_img.SetExtent(0, width-1, 0, height-1, 0, depth-1)
    vtk_img.SetSpacing(sitk_img.GetSpacing())
    vtk_img.SetOrigin(sitk_img.GetOrigin())
    vtk_arr = numpy_support.numpy_to_vtk(
        num_array=arr.ravel(order='C'),
        deep=True,
        array_type=numpy_support.get_vtk_array_type(arr.dtype)
    )
    vtk_img.GetPointData().SetScalars(vtk_arr)
    return vtk_img, arr

# Main function
def main(ct_source):
    # Load CT and cache
    ct_sitk = load_cached_ct(ct_source)
    vtk_img, arr = sitk_to_vtk(ct_sitk)
    num_slices = arr.shape[0]
    hu_min, hu_max = int(arr.min()), int(arr.max())
    # Initial parameters
    init_slice = num_slices // 2
    init_window = max(1, hu_max - hu_min)
    init_level = (hu_max + hu_min) / 2

    # VTK setup
    renderer = vtk.vtkRenderer()
    ren_win = vtk.vtkRenderWindow()
    ren_win.SetSize(600, 600)
    ren_win.AddRenderer(renderer)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(ren_win)

    # Slice counter text
    text_actor = vtk.vtkTextActor()
    tp = text_actor.GetTextProperty()
    tp.SetFontSize(24)
    tp.BoldOn()
    text_actor.SetPosition(10, 10)
    renderer.AddActor2D(text_actor)

    # Image plane widget
    plane = vtk.vtkImagePlaneWidget()
    plane.SetInteractor(iren)
    plane.SetDefaultRenderer(renderer)
    plane.SetInputData(vtk_img)
    plane.SetResliceInterpolateToLinear()
    plane.RestrictPlaneToVolumeOn()
    plane.DisplayTextOn()
    plane.SetWindowLevel(init_window, init_level)
    plane.SetPlaneOrientationToZAxes()
    plane.On()
    plane.SetSliceIndex(init_slice)

        # Slider representation builder
    def make_slider(title, minv, maxv, initv, p1, p2):
        rep = vtk.vtkSliderRepresentation2D()
        rep.SetMinimumValue(minv)
        rep.SetMaximumValue(maxv)
        rep.SetValue(initv)
        rep.SetTitleText(title)
        rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
        rep.GetPoint1Coordinate().SetValue(*p1)
        rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
        rep.GetPoint2Coordinate().SetValue(*p2)
        rep.SetSliderLength(0.02)
        rep.SetSliderWidth(0.03)
        rep.SetTubeWidth(0.005)
        return rep

    # Create slice slider
    slice_rep = make_slider("Slice", 0, num_slices-1, init_slice, (0.1,0.05), (0.9,0.05))
    slice_slider = vtk.vtkSliderWidget()
    slice_slider.SetInteractor(iren)
    slice_slider.SetRepresentation(slice_rep)
    slice_slider.SetAnimationModeToJump()
    slice_slider.EnabledOn()

    # Window/Level sliders
    win_rep = make_slider("Window", 1, hu_max-hu_min, init_window, (0.1,0.9), (0.4,0.9))
    lvl_rep = make_slider("Level", hu_min, hu_max, init_level, (0.6,0.9), (0.9,0.9))
    win_slider = vtk.vtkSliderWidget(); win_slider.SetInteractor(iren); win_slider.SetRepresentation(win_rep); win_slider.SetAnimationModeToJump(); win_slider.EnabledOn()
    lvl_slider = vtk.vtkSliderWidget(); lvl_slider.SetInteractor(iren); lvl_slider.SetRepresentation(lvl_rep); lvl_slider.SetAnimationModeToJump(); lvl_slider.EnabledOn()

    # Callbacks
    def update_slice(val):
        plane.SetSliceIndex(val)
        text_actor.SetInput(f"Slice: {val+1}/{num_slices}")
        ren_win.Render()
    def on_slice(obj, event):
        val = int(obj.GetRepresentation().GetValue())
        update_slice(val)
    slice_slider.AddObserver("EndInteractionEvent", on_slice)

    # Sync wheel with slider
    def wheel_forward(obj, event):
        val = min(slice_rep.GetMaximumValue(), slice_rep.GetValue()+1)
        slice_rep.SetValue(val)
        update_slice(val)
    def wheel_backward(obj, event):
        val = max(slice_rep.GetMinimumValue(), slice_rep.GetValue()-1)
        slice_rep.SetValue(val)
        update_slice(val)
    iren.AddObserver("MouseWheelForwardEvent", wheel_forward)
    iren.AddObserver("MouseWheelBackwardEvent", wheel_backward)

    # Window/Level callbacks
    def on_win(obj, event): plane.SetWindowLevel(obj.GetRepresentation().GetValue(), lvl_rep.GetValue()); ren_win.Render()
    def on_lvl(obj, event): plane.SetWindowLevel(win_rep.GetValue(), obj.GetRepresentation().GetValue()); ren_win.Render()
    win_slider.AddObserver("InteractionEvent", on_win)
    lvl_slider.AddObserver("InteractionEvent", on_lvl)

    # Initialize
    update_slice(init_slice)
    ren_win.Render()
    iren.Initialize()
    print("Starting axial CT viewer...")
    iren.Start()

# Entry point
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <DICOM_dir|NIfTI_file>")
        sys.exit(1)
    main(sys.argv[1])
