#!/usr/bin/env python3
"""
2D Axial CT Viewer with Dedicated Mode-Based Mouse Control and Zoom/Window/Level/ Slice Sliders

Features:
 1. Caches CT volumes (DICOM folder or NIfTI) as .mha for fast reloads.
 2. Displays axial (XY) slices in a fixed 2D renderer (vtkImageViewer2).
 3. Four adjustable parameters, each with its own slider and exclusive mouse-wheel control:
    - Slice index (integer steps)
    - Zoom level (camera parallel scale)
    - Window width
    - Level center
 4. Click on a slider to select its mode; the mouse wheel then only affects that parameter.
 5. Click anywhere else to return to 'view' mode (mouse wheel does nothing).
 6. On-screen labels:
    - "Slice: i/N"
    - "Mode: <current_mode>"

Usage:
    python renderer2.py <CT_source>
"""
import sys, os
import SimpleITK as sitk
import vtk
from vtkmodules.util import numpy_support
from totalseg import load_ct

# --- Cache Setup ---
CACHE_DIR = os.path.expanduser('~/.cache/renderer')
if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(src):
    name = os.path.basename(src.rstrip(os.sep)).replace(' ','_')
    return os.path.join(CACHE_DIR, f"{name}.mha")

def load_cached(src):
    path = get_cache_path(src)
    if os.path.exists(path):
        print(f"Loading CT from cache: {path}")
        return sitk.ReadImage(path)
    print(f"Loading CT from source: {src}")
    img = load_ct(src)
    print(f"Caching CT to: {path}")
    sitk.WriteImage(img, path)
    return img

# Convert SITK image to vtkImageData
def sitk2vtk(img):
    arr = sitk.GetArrayFromImage(img)  # shape (Z,Y,X)
    Z,Y,X = arr.shape
    vtk_img = vtk.vtkImageData()
    vtk_img.SetDimensions(X,Y,Z)
    vtk_img.SetExtent(0,X-1,0,Y-1,0,Z-1)
    vtk_img.SetSpacing(img.GetSpacing())
    vtk_img.SetOrigin(img.GetOrigin())
    vtk_arr = numpy_support.numpy_to_vtk(arr.ravel('C'), deep=True,
        array_type=numpy_support.get_vtk_array_type(arr.dtype))
    vtk_img.GetPointData().SetScalars(vtk_arr)
    return vtk_img, arr

# Slider factory
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

# Main
def main(ct_src):
    # Load CT
    sitk_img = load_cached(ct_src)
    vtk_img, arr = sitk2vtk(sitk_img)
    num_slices = arr.shape[0]
    hu_min, hu_max = int(arr.min()), int(arr.max())
    # Initial values
    init_slice = num_slices//2
    init_window = max(1, hu_max - hu_min)
    init_level  = (hu_max + hu_min)/2

    # VTK ImageViewer2
    viewer = vtk.vtkImageViewer2()
    viewer.SetInputData(vtk_img)
    viewer.SetSlice(init_slice)
    viewer.SetColorWindow(init_window)
    viewer.SetColorLevel(init_level)
    ren = viewer.GetRenderer()
    ren_win = viewer.GetRenderWindow()
    ren_win.SetSize(600,600)

    # Initialize camera
    ren.ResetCamera()
    cam = ren.GetActiveCamera()
    init_zoom = cam.GetParallelScale()

    # Interactor
    iren = vtk.vtkRenderWindowInteractor()
    viewer.SetupInteractor(iren)

    # Mode state
    current_mode = 'view'

    # Labels
    slice_label = vtk.vtkTextActor()
    mp = slice_label.GetTextProperty(); mp.SetFontSize(24); mp.BoldOn()
    slice_label.SetPosition(10,10)
    ren.AddActor2D(slice_label)
    slice_label.SetInput(f"Slice: {init_slice+1}/{num_slices}")

    mode_label = vtk.vtkTextActor()
    mm = mode_label.GetTextProperty(); mm.SetFontSize(18); mm.BoldOn()
    mode_label.SetPosition(10,50)
    ren.AddActor2D(mode_label)
    mode_label.SetInput(f"Mode: {current_mode}")

    # Sliders
    slice_rep = make_slider('Slice', 0, num_slices-1, init_slice, (0.1,0.05),(0.3,0.05))
    zoom_rep  = make_slider('Zoom', init_zoom*0.5, init_zoom*2, init_zoom,      (0.35,0.05),(0.55,0.05))
    win_rep   = make_slider('Window',1,hu_max-hu_min,init_window,               (0.6,0.05),(0.8,0.05))
    lvl_rep   = make_slider('Level', hu_min, hu_max, init_level,                (0.85,0.05),(0.95,0.05))

    slice_sl = vtk.vtkSliderWidget(); slice_sl.SetInteractor(iren); slice_sl.SetRepresentation(slice_rep); slice_sl.EnabledOn()
    zoom_sl  = vtk.vtkSliderWidget(); zoom_sl .SetInteractor(iren); zoom_sl .SetRepresentation(zoom_rep);  zoom_sl .EnabledOn()
    win_sl   = vtk.vtkSliderWidget(); win_sl .SetInteractor(iren); win_sl .SetRepresentation(win_rep);   win_sl .EnabledOn()
    lvl_sl   = vtk.vtkSliderWidget(); lvl_sl .SetInteractor(iren); lvl_sl .SetRepresentation(lvl_rep);   lvl_sl .EnabledOn()

    # Mode updater
    def set_mode(mode):
        nonlocal current_mode
        current_mode = mode
        mode_label.SetInput(f"Mode: {current_mode}")
        ren_win.Render()

    # Callbacks per slider
    def on_slice(obj,evt): val=int(round(obj.GetRepresentation().GetValue())); viewer.SetSlice(val); slice_label.SetInput(f"Slice: {val+1}/{num_slices}"); set_mode('slice')
    slice_sl.AddObserver('EndInteractionEvent', on_slice)

    def on_zoom(obj,evt): val=obj.GetRepresentation().GetValue(); cam.SetParallelScale(val); set_mode('zoom')
    zoom_sl .AddObserver('EndInteractionEvent', on_zoom)

    def on_win(obj,evt): val=int(round(obj.GetRepresentation().GetValue())); viewer.SetColorWindow(val); set_mode('window')
    win_sl  .AddObserver('InteractionEvent', on_win)

    def on_lvl(obj,evt): val=int(round(obj.GetRepresentation().GetValue())); viewer.SetColorLevel(val); set_mode('level')
    lvl_sl  .AddObserver('InteractionEvent', on_lvl)

    # Mouse wheel handler
    def on_wheel(obj,evt,forward):
        if current_mode=='slice':
            cur = viewer.GetSlice(); new = min(num_slices-1, cur + (1 if forward else -1)); viewer.SetSlice(new); slice_label.SetInput(f"Slice: {new+1}/{num_slices}"); slice_rep.SetValue(new)
        elif current_mode=='zoom':
            cur = cam.GetParallelScale(); new = cur + ( -cam.GetParallelScale()*0.1 if forward else cam.GetParallelScale()*0.1 ) * ( -1 if forward else 1 )
            cam.SetParallelScale(new); zoom_rep.SetValue(new)
        elif current_mode=='window':
            cur = viewer.GetColorWindow(); new = max(1, cur + (1 if forward else -1)); viewer.SetColorWindow(new); win_rep.SetValue(new)
        elif current_mode=='level':
            cur = viewer.GetColorLevel(); new = cur + (1 if forward else -1); viewer.SetColorLevel(new); lvl_rep.SetValue(new)
        ren_win.Render()
    iren.AddObserver('MouseWheelForwardEvent', lambda o,e: on_wheel(o,e,True))
    iren.AddObserver('MouseWheelBackwardEvent',lambda o,e: on_wheel(o,e,False))

    # Click outside resets to 'view'
    iren.AddObserver('LeftButtonPressEvent', lambda o,e: set_mode('view'))

    # Start
    ren_win.Render(); iren.Initialize(); print('Starting axial viewer with modes...'); iren.Start()

if __name__=='__main__':
    if len(sys.argv)!=2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <CT_source>")
        sys.exit(1)
    main(sys.argv[1])
