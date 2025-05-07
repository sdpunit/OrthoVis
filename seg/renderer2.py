#!/usr/bin/env python3
"""
Dual-view CT Slice Viewer with caching, independent slice controls, and global window/level sliders

Features:
 1. Load CT (DICOM folder or NIfTI file) via `totalseg.load_ct`, cached as .mha for fast reloads.
 2. Display axial and coronal orthogonal slices side by side.
 3. Slice navigation per view:
    - Mouse wheel over each view changes its slice (no zoom).
    - Draggable slider below each view reflects and controls its slice.
    - On-screen "Axial: X/N" and "Coronal: X/N" labels.
 4. Global Window/Level sliders at top adjust contrast/brightness for both views simultaneously.

Usage:
    python dual_viewer.py <DICOM_dir|NIfTI_file>
"""
import sys, os
import SimpleITK as sitk
import vtk
from vtkmodules.util import numpy_support
from totalseg import load_ct

# Caching directory
CACHE_DIR = os.path.expanduser('~/.cache/renderer')
if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(source: str) -> str:
    name = os.path.basename(source.rstrip(os.sep)).replace(' ', '_')
    return os.path.join(CACHE_DIR, f"{name}.mha")

def load_cached_ct(source: str) -> sitk.Image:
    cache = get_cache_path(source)
    if os.path.exists(cache):
        print(f"Loading CT from cache: {cache}")
        return sitk.ReadImage(cache)
    print(f"Loading CT from source: {source}")
    img = load_ct(source)
    print(f"Caching CT to: {cache}")
    sitk.WriteImage(img, cache)
    return img

# Convert SITK image to VTK
def sitk_to_vtk(img: sitk.Image):
    arr = sitk.GetArrayFromImage(img)  # (z,y,x)
    z,y,x = arr.shape
    vtk_img = vtk.vtkImageData()
    vtk_img.SetDimensions(x, y, z)
    vtk_img.SetExtent(0, x-1, 0, y-1, 0, z-1)
    vtk_img.SetSpacing(img.GetSpacing())
    vtk_img.SetOrigin(img.GetOrigin())
    vtk_arr = numpy_support.numpy_to_vtk(arr.ravel('C'), deep=True,
        array_type=numpy_support.get_vtk_array_type(arr.dtype))
    vtk_img.GetPointData().SetScalars(vtk_arr)
    return vtk_img, arr

# Slider helper
def make_slider(title, mn, mx, init, p1, p2):
    rep = vtk.vtkSliderRepresentation2D()
    rep.SetTitleText(title)
    rep.SetMinimumValue(mn)
    rep.SetMaximumValue(mx)
    rep.SetValue(init)
    rep.SetResolution(1)  # integer steps only
    rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint1Coordinate().SetValue(*p1)
    rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint2Coordinate().SetValue(*p2)
    rep.SetSliderLength(0.02)
    rep.SetSliderWidth(0.03)
    rep.SetTubeWidth(0.005)
    return rep
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
    # Load and convert
    sitk_img = load_cached_ct(ct_source)
    vtk_img, arr = sitk_to_vtk(sitk_img)
    na, nc = arr.shape[0], arr.shape[1]
    hu_min, hu_max = int(arr.min()), int(arr.max())
    init_a, init_c = na//2, nc//2
    init_w = max(1, hu_max - hu_min)
    init_l = (hu_max + hu_min)/2

    # Window setup
    ren_win = vtk.vtkRenderWindow(); ren_win.SetSize(1200,600)
    ax_ren = vtk.vtkRenderer(); ax_ren.SetViewport(0,0,0.5,1); ren_win.AddRenderer(ax_ren)
    co_ren = vtk.vtkRenderer(); co_ren.SetViewport(0.5,0,1,1); ren_win.AddRenderer(co_ren)
    iren = vtk.vtkRenderWindowInteractor(); iren.SetRenderWindow(ren_win)

    # Plane widgets
    def make_plane(renderer, orient, init_slice):
        pw = vtk.vtkImagePlaneWidget(); pw.SetInteractor(iren); pw.SetDefaultRenderer(renderer)
        pw.SetInputData(vtk_img)
        if orient=='axial': pw.SetPlaneOrientationToZAxes()
        else: pw.SetPlaneOrientationToYAxes()
        pw.SetResliceInterpolateToLinear(); pw.RestrictPlaneToVolumeOn(); pw.DisplayTextOn()
        pw.SetWindowLevel(init_w, init_l); pw.On(); pw.SetSliceIndex(init_slice)
        pw.UpdatePlacement(); return pw

    axial_pw   = make_plane(ax_ren, 'axial', init_a)
    # reset camera to properly view axial slice
    ax_ren.ResetCamera()
    coronal_pw = make_plane(co_ren, 'coronal', init_c)
    # reset camera to properly view coronal slice
    co_ren.ResetCamera()

    # Text actors
    def make_text(renderer, label):
        ta=vtk.vtkTextActor(); tp=ta.GetTextProperty(); tp.SetFontSize(20); tp.BoldOn()
        ta.SetPosition(10,10); renderer.AddActor2D(ta); return ta
    axial_text   = make_text(ax_ren, 'Axial')
    coronal_text = make_text(co_ren, 'Coronal')

    # Update functions
    def upd_ax(v): axial_pw.SetSliceIndex(v); axial_text.SetInput(f"Axial: {v+1}/{na}"); ren_win.Render()
    def upd_co(v): coronal_pw.SetSliceIndex(v); coronal_text.SetInput(f"Coronal: {v+1}/{nc}"); ren_win.Render()
    upd_ax(init_a); upd_co(init_c)

    # Sliders
    a_rep = make_slider('Axial',0,na-1,init_a,(0.1,0.05),(0.4,0.05)); a_sl=vtk.vtkSliderWidget(); a_sl.SetInteractor(iren); a_sl.SetRepresentation(a_rep); a_sl.EnabledOn(); a_sl.AddObserver('EndInteractionEvent', lambda o,e: upd_ax(int(o.GetRepresentation().GetValue())))
    c_rep = make_slider('Coronal',0,nc-1,init_c,(0.6,0.05),(0.9,0.05)); c_sl=vtk.vtkSliderWidget(); c_sl.SetInteractor(iren); c_sl.SetRepresentation(c_rep); c_sl.EnabledOn(); c_sl.AddObserver('EndInteractionEvent', lambda o,e: upd_co(int(o.GetRepresentation().GetValue())))

    # Window/Level sliders
    w_rep = make_slider('Window',1,hu_max-hu_min,init_w,(0.1,0.9),(0.45,0.9)); w_sl=vtk.vtkSliderWidget(); w_sl.SetInteractor(iren); w_sl.SetRepresentation(w_rep); w_sl.EnabledOn()
    l_rep = make_slider('Level',hu_min,hu_max,init_l,(0.55,0.9),(0.9,0.9)); l_sl=vtk.vtkSliderWidget(); l_sl.SetInteractor(iren); l_sl.SetRepresentation(l_rep); l_sl.EnabledOn()
    w_sl.AddObserver('InteractionEvent', lambda o,e: [axial_pw.SetWindowLevel(o.GetRepresentation().GetValue(),l_rep.GetValue()), coronal_pw.SetWindowLevel(o.GetRepresentation().GetValue(),l_rep.GetValue()), ren_win.Render()])
    l_sl.AddObserver('InteractionEvent', lambda o,e: [axial_pw.SetWindowLevel(w_rep.GetValue(),o.GetRepresentation().GetValue()), coronal_pw.SetWindowLevel(w_rep.GetValue(),o.GetRepresentation().GetValue()), ren_win.Render()])

    # Custom interactor for wheel
    class DualStyle(vtk.vtkInteractorStyleImage):
        def __init__(self): super().__init__(); self.AddObserver('MouseWheelForwardEvent',self.fwd); self.AddObserver('MouseWheelBackwardEvent',self.back)
        def fwd(self,obj,evt): x,y=iren.GetEventPosition(); w,h=ren_win.GetSize(); (upd_ax if x<w*0.5 else upd_co)(int((a_rep if x<w*0.5 else c_rep).GetValue()+1))
        def back(self,obj,evt): x,y=iren.GetEventPosition(); w,h=ren_win.GetSize(); (upd_ax if x<w*0.5 else upd_co)(int((a_rep if x<w*0.5 else c_rep).GetValue()-1))
    iren.SetInteractorStyle(DualStyle())

    # Start
    iren.Initialize(); ren_win.Render(); print('Starting dual-view viewer...'); iren.Start()

if __name__=='__main__':
    if len(sys.argv)!=2: print(f"Usage: {os.path.basename(sys.argv[0])} <CT_source>"); sys.exit(1)
    main(sys.argv[1])
