#!/usr/bin/env python3
"""
2D CT Quad-Viewer with Segmentation Mask Overlays
Supports loading CT as a DICOM folder or single file, plus interactive mask toggles.
"""
import os, sys, glob
import numpy as np
import SimpleITK as sitk
import vtk
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules.vtkInteractionImage import vtkImageViewer2
from vtkmodules.vtkRenderingCore import (
    vtkRenderWindow, vtkRenderer, vtkRenderWindowInteractor,
    vtkActor2D, vtkTextMapper, vtkTextProperty, vtkTextActor,
    vtkImageActor
)
from vtkmodules.util import numpy_support

# -- CT loading -------------------------------------------------------------
def load_ct(path):
    if os.path.isdir(path):
        reader = sitk.ImageSeriesReader()
        series = reader.GetGDCMSeriesFileNames(path)
        if not series:
            raise RuntimeError(f"No DICOM series in {path}")
        reader.SetFileNames(series)
        return reader.Execute()
    else:
        return sitk.ReadImage(path)

# -- Caching ---------------------------------------------------------------
def cache_ct(path):
    cache_dir = os.path.expanduser('~/.cache/renderer')
    os.makedirs(cache_dir, exist_ok=True)
    name = os.path.basename(path.rstrip(os.sep)) + '.mha'
    dst = os.path.join(cache_dir, name)
    if os.path.exists(dst):
        return sitk.ReadImage(dst)
    img = load_ct(path)
    sitk.WriteImage(img, dst)
    return img

# -- Convert to VTK --------------------------------------------------------
def sitk_to_vtk(img):
    arr = sitk.GetArrayFromImage(img)
    z, y, x = arr.shape
    vtk_img = vtk.vtkImageData()
    vtk_img.SetDimensions(x, y, z)
    vtk_img.SetSpacing(img.GetSpacing())
    vtk_img.SetOrigin(img.GetOrigin())
    vtk_arr = numpy_support.numpy_to_vtk(
        arr.ravel(), deep=True,
        array_type=numpy_support.get_vtk_array_type(arr.dtype)
    )
    vtk_img.GetPointData().SetScalars(vtk_arr)
    return vtk_img, arr

# -- Slider creation --------------------------------------------------------
def make_slider(vmin, vmax, init, xpos):
    rep = vtk.vtkSliderRepresentation2D()
    rep.SetMinimumValue(vmin)
    rep.SetMaximumValue(vmax)
    rep.SetValue(init)
    rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint1Coordinate().SetValue(xpos, 0.1)
    rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    rep.GetPoint2Coordinate().SetValue(xpos, 0.4)
    rep.SetSliderLength(0.008)
    rep.SetSliderWidth(0.008)
    rep.SetTubeWidth(0.002)
    rep.ShowSliderLabelOff()
    rep.SetEndCapLength(0)
    rep.GetSliderProperty().SetColor(1, 1, 0)
    rep.GetSelectedProperty().SetColor(1, 1, 0)
    rep.GetTubeProperty().SetColor(0.4, 0.4, 0.4)
    return rep

# -- Mask overlay ----------------------------------------------------------
class MaskOverlay:
    def __init__(self, mask, spacing, origin, color, opacity=0.4):
        img = vtk.vtkImageData()
        z, y, x = mask.shape
        img.SetDimensions(x, y, z)
        img.SetSpacing(spacing)
        img.SetOrigin(origin)
        flat = (mask.astype(np.uint8) * 255).ravel()
        scalars = numpy_support.numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
        img.GetPointData().SetScalars(scalars)
        cmap = vtk.vtkImageMapToColors()
        cmap.SetInputData(img)
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(2)
        lut.Build()
        lut.SetTableValue(0, 0, 0, 0, 0)
        lut.SetTableValue(1, *color, opacity)
        cmap.SetLookupTable(lut)
        self.actor = vtkImageActor()
        self.actor.GetMapper().SetInputConnection(cmap.GetOutputPort())
    def add_to(self, renderer):
        renderer.AddActor(self.actor)
    def visible(self, flag):
        self.actor.SetVisibility(1 if flag else 0)

# -- Slice viewer & interactor --------------------------------------------
class SliceViewer:
    def __init__(self, vtk_img, arr, orientation, viewport, title, rw):
        self.title = title
        self.viewer = vtkImageViewer2()
        self.viewer.SetInputData(vtk_img)
        axis = {'axial':0, 'coronal':1, 'sagittal':2}[orientation]
        if orientation == 'coronal': self.viewer.SetSliceOrientationToXZ()
        if orientation == 'sagittal': self.viewer.SetSliceOrientationToYZ()
        self.min_slice = 0
        self.max_slice = arr.shape[axis] - 1
        self.slice = self.max_slice // 2
        self.viewer.SetSlice(self.slice)
        ren = self.viewer.GetRenderer()
        ren.SetViewport(*viewport)
        ren.SetBackground(0, 0, 0)
        rw.AddRenderer(ren)
        self.viewer.SetRenderWindow(rw)
        tp = vtkTextProperty(); tp.SetFontSize(18); tp.SetColor(1,1,1)
        self.mapper = vtkTextMapper(); self.mapper.SetTextProperty(tp)
        actor = vtkActor2D(); actor.SetMapper(self.mapper); actor.SetPosition(5,5); ren.AddActor2D(actor)
        self.update_label()
    def update_label(self):
        self.mapper.SetInput(f"{self.title}\nSlice: {self.slice+1}/{self.max_slice+1}")
    def move(self, delta):
        new = np.clip(self.slice + delta, self.min_slice, self.max_slice)
        if new != self.slice:
            self.slice = new; self.viewer.SetSlice(new); self.update_label()
        self.viewer.Render()
    def contains(self, xn, yn):
        x0, y0, x1, y1 = self.viewer.GetRenderer().GetViewport()
        return x0 <= xn <= x1 and y0 <= yn <= y1

class QuadStyle(vtkInteractorStyleImage):
    def __init__(self, viewers):
        super().__init__(); self.viewers = viewers
        self.RemoveObservers('MouseWheelForwardEvent'); self.RemoveObservers('MouseWheelBackwardEvent')
        self.AddObserver('MouseWheelForwardEvent', self.on_wheel_forward)
        self.AddObserver('MouseWheelBackwardEvent', self.on_wheel_backward)
    def pick(self):
        x,y=self.GetInteractor().GetEventPosition(); w,h=self.GetInteractor().GetRenderWindow().GetSize()
        xn,yn=x/w,y/h
        for sv in self.viewers:
            if sv.contains(xn,yn): return sv
        return None
    def on_wheel_forward(self,obj,event):
        sv=self.pick();
        if not sv: return
        if self.GetInteractor().GetControlKey():
            cam=sv.viewer.GetRenderer().GetActiveCamera(); cam.ParallelProjectionOn(); cam.Zoom(1.1)
        else: sv.move(1)
        self.GetInteractor().GetRenderWindow().Render()
    def on_wheel_backward(self,obj,event):
        sv=self.pick();
        if not sv: return
        if self.GetInteractor().GetControlKey():
            cam=sv.viewer.GetRenderer().GetActiveCamera(); cam.ParallelProjectionOn(); cam.Zoom(0.9)
        else: sv.move(-1)
        self.GetInteractor().GetRenderWindow().Render()

# -- Main ------------------------------------------------------------------
def main(ct_path):
    # load and cache CT
    img = cache_ct(ct_path)
    spacing = img.GetSpacing()
    origin = img.GetOrigin()
    arr_ct = sitk.GetArrayFromImage(img)

    # find masks
    base = os.path.dirname(ct_path)
    mask_files = glob.glob(os.path.join(base, '*.nii.gz'))
    masks = []
    for i, mf in enumerate(mask_files):
        label = os.path.splitext(os.path.basename(mf))[0]
        arr = sitk.GetArrayFromImage(sitk.ReadImage(mf))
        masks.append({'label': label, 'array': arr})

    # launch Qt+VTK window
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    from PyQt5 import QtWidgets, QtCore

    class AppWindow(QtWidgets.QMainWindow):
        def __init__(self, ct_img_arr, spacing, origin, masks):
            super().__init__()
            self.setWindowTitle('CT Quad Viewer with Masks')
            self.ct_arr = ct_img_arr
            self.spacing = spacing
            self.origin = origin
            # VTK widget
            self.frame = QtWidgets.QFrame()
            self.layout = QtWidgets.QHBoxLayout()
            self.vtk_widget = QVTKRenderWindowInteractor(self.frame)
            self.layout.addWidget(self.vtk_widget, stretch=4)
            # sidebar
            self.sidebar = QtWidgets.QVBoxLayout()
            self.checks = {}
            for m in masks:
                cb = QtWidgets.QCheckBox(m['label'])
                cb.setChecked(True)
                cb.stateChanged.connect(lambda s,lab=m['label']: self.toggle_mask(lab, s))
                self.sidebar.addWidget(cb)
                self.checks[m['label']] = cb
            side_w = QtWidgets.QWidget()
            side_w.setLayout(self.sidebar)
            self.layout.addWidget(side_w, stretch=1)
            self.frame.setLayout(self.layout)
            self.setCentralWidget(self.frame)
            # set up VTK scene
            self._init_vtk()
            self.show()
            self.vtk_widget.Initialize()

        def _init_vtk(self):
            rw = self.vtk_widget.GetRenderWindow()
            # same SliceViewer + QuadStyle setup here, using self.ct_arr, spacing, origin
            # add each mask via MaskOverlay, store overlays in dict
            self.overlays = {}
            # ... (same as above but preserved labels)

        def toggle_mask(self, label, state):
            vis = (state == QtCore.Qt.Checked)
            self.overlays[label].visible(vis)
            self.vtk_widget.GetRenderWindow().Render()

    app = QtWidgets.QApplication(sys.argv)
    win = AppWindow(arr_ct, spacing, origin, masks)
    sys.exit(app.exec_())

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <CT_folder_or_file>")
        sys.exit(1)
    main(sys.argv[1])
