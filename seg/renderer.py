#!/usr/bin/env python3
"""
Simple single-view CT Slice Viewer using VTK with caching and slice scrolling

This minimal script will:
 1. Load a CT volume (DICOM folder or NIfTI file) via `totalseg.load_ct`, or from a cached MetaImage (.mha) if available.
 2. Convert it to `vtkImageData`.
 3. Show only one orthogonal view (axial) with custom mouse-wheel slice navigation, window/level adjustment, and an on-screen slice counter.

Usage:
    python axial_viewer.py <DICOM_dir|NIfTI_file>
"""
import sys
import os
import SimpleITK as sitk
import vtk
from vtkmodules.util import numpy_support
from totalseg import load_ct

CACHE_DIR = os.path.expanduser('~/.cache/renderer')
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)


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


def sitk_to_vtk(sitk_img):
    arr = sitk.GetArrayFromImage(sitk_img)  # (depth, height, width)
    depth, height, width = arr.shape
    vtk_img = vtk.vtkImageData()
    vtk_img.SetDimensions(width, height, depth)
    vtk_img.SetSpacing(sitk_img.GetSpacing())
    vtk_img.SetOrigin(sitk_img.GetOrigin())
    vtk_arr = numpy_support.numpy_to_vtk(
        num_array=arr.ravel(order='C'),
        deep=True,
        array_type=numpy_support.get_vtk_array_type(arr.dtype)
    )
    vtk_img.GetPointData().SetScalars(vtk_arr)
    return vtk_img, depth


def main(ct_source):
    # Load (or cache) CT volume
    ct_sitk = load_cached_ct(ct_source)
    vtk_img, num_slices = sitk_to_vtk(ct_sitk)
    initial_slice = num_slices // 2

    # Renderer and render window
    renderer = vtk.vtkRenderer()
    ren_win = vtk.vtkRenderWindow()
    ren_win.SetSize(600, 600)
    ren_win.AddRenderer(renderer)

    # Custom interactor style to intercept mouse wheel
    class SliceStyle(vtk.vtkInteractorStyleImage):
        def __init__(self, plane_widget, text_actor):
            super().__init__()
            self.plane = plane_widget
            self.text = text_actor
            self.slice_idx = initial_slice
            self.max_slices = num_slices
            self.AddObserver("MouseWheelForwardEvent", self.on_wheel_forward)
            self.AddObserver("MouseWheelBackwardEvent", self.on_wheel_backward)

        def on_wheel_forward(self, obj, event):
            if self.slice_idx < self.max_slices - 1:
                self.slice_idx += 1
                self.plane.SetSliceIndex(self.slice_idx)
                self.text.SetInput(f"Slice: {self.slice_idx+1}/{self.max_slices}")
                ren_win.Render()

        def on_wheel_backward(self, obj, event):
            if self.slice_idx > 0:
                self.slice_idx -= 1
                self.plane.SetSliceIndex(self.slice_idx)
                self.text.SetInput(f"Slice: {self.slice_idx+1}/{self.max_slices}")
                ren_win.Render()

    # Interactor and style
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(ren_win)

    # Text actor for slice counter
    text_actor = vtk.vtkTextActor()
    text_actor.GetTextProperty().SetFontSize(24)
    text_actor.GetTextProperty().BoldOn()
    text_actor.SetPosition(10, 10)
    renderer.AddActor2D(text_actor)

    # Plane widget for axial view
    plane = vtk.vtkImagePlaneWidget()
    plane.SetInteractor(iren)
    plane.SetDefaultRenderer(renderer)
    plane.SetInputData(vtk_img)
    plane.SetResliceInterpolateToLinear()
    plane.RestrictPlaneToVolumeOn()
    plane.DisplayTextOn()
    plane.SetWindowLevel(1000, 2000)
    plane.SetPlaneOrientationToZAxes()
    plane.On()
    plane.SetSliceIndex(initial_slice)

    # Initialize slice counter text
    text_actor.SetInput(f"Slice: {initial_slice+1}/{num_slices}")

    # Slider representation
    sliderRep = vtk.vtkSliderRepresentation2D()
    sliderRep.SetMinimumValue(0)
    sliderRep.SetMaximumValue(num_slices - 1)
    sliderRep.SetValue(initial_slice)
    sliderRep.SetTitleText("Slice")
    sliderRep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    sliderRep.GetPoint1Coordinate().SetValue(0.1, 0.05)
    sliderRep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    sliderRep.GetPoint2Coordinate().SetValue(0.9, 0.05)
    sliderRep.SetSliderLength(0.02)
    sliderRep.SetSliderWidth(0.03)
    sliderRep.SetEndCapLength(0.01)
    sliderRep.SetEndCapWidth(0.03)
    sliderRep.SetTubeWidth(0.005)

    sliderWidget = vtk.vtkSliderWidget()
    sliderWidget.SetInteractor(iren)
    sliderWidget.SetRepresentation(sliderRep)
    sliderWidget.SetAnimationModeToJump()
    sliderWidget.EnabledOn()

    # Slider callback
    def on_slider_interaction(obj, event):
        val = int(obj.GetRepresentation().GetValue())
        style.slice_idx = val
        plane.SetSliceIndex(val)
        text_actor.SetInput(f"Slice: {val+1}/{num_slices}")
        ren_win.Render()

    sliderWidget.AddObserver("InteractionEvent", on_slider_interaction)

    # Set custom style (after slider so slider events are not overridden)
    style = SliceStyle(plane, text_actor)
    iren.SetInteractorStyle(style)

    # Initialize and start
    iren.Initialize()
    ren_win.Render()
    print("Starting axial viewer with slice scrolling and slider...")
    iren.Start()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <DICOM_dir|NIfTI_file>")
        sys.exit(1)
    main(sys.argv[1])