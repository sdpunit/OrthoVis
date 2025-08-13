#!/usr/bin/env python3
"""
2D CT Quad-Viewer

Features:
 1. Single RenderWindow split into 3 active viewports (axial, coronal, sagittal). 
 2. Mouse wheel scrolls slices in the quadrant under the cursor; Ctrl + wheel zooms.
 3. Slice count labels in each quadrant showing "<View> \n Slice: X/N".
 4. Legend for segmentation masks in the top-right quadrant; default mask opacity 0.9.
"""
import os, glob, argparse, vtk 
import SimpleITK as sitk
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules.vtkInteractionImage import vtkImageViewer2
from vtkmodules.vtkRenderingCore import (
    vtkRenderWindow,
    vtkRenderer,
    vtkRenderWindowInteractor,
    vtkActor2D,
    vtkTextMapper,
    vtkTextProperty,
    vtkTextActor
)
from vtkmodules.vtkRenderingAnnotation import vtkLegendBoxActor
from vtkmodules.util import numpy_support
from totalseg import load_ct

# Caching directory
CACHE_DIR = os.path.expanduser('~/.cache/renderer')
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_ct(path: str):
    cache_file = os.path.join(CACHE_DIR, os.path.basename(path.rstrip(os.sep)) + '.mha')
    if os.path.exists(cache_file):
        return sitk.ReadImage(cache_file)
    img = load_ct(path)
    sitk.WriteImage(img, cache_file)
    return img


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


class SliceViewer:
    def __init__(self, vtk_img, arr, orientation, viewport, name,
                 render_window, mask_colors_list, dims):

        self.name = name
        self.viewport = viewport
        self.dims = dims
        self.slice = 0
        self.min_slice = 0

        # 1) Create the viewer and immediately give it *your* rw
        self.viewer = vtkImageViewer2()
        self.viewer.SetRenderWindow(render_window)
        self.viewer.SetInputData(vtk_img)

        # 2) Set orientation & initial slice
        axis = 0
        if orientation == 'coronal':
            self.viewer.SetSliceOrientationToXZ()
            axis = 1
        elif orientation == 'sagittal':
            self.viewer.SetSliceOrientationToYZ()
            axis = 2

        self.min_slice, self.max_slice = 0, arr.shape[axis] - 1
        self.slice = arr.shape[axis] // 2
        self.viewer.SetSlice(self.slice)

        # 3) Hook the shared interactor in
        self.viewer.SetupInteractor(render_window.GetInteractor())

        # 4) Tweak the renderer that vtkImageViewer2 already registered
        renderer = self.viewer.GetRenderer()
        renderer.SetViewport(*viewport)
        renderer.SetBackground(0, 0, 0)

        # 5) Add your mask actors *into* that same renderer
        self.mask_actors = []
        for cmap in mask_colors_list:
            actor = vtk.vtkImageActor()
            actor.GetMapper().SetInputConnection(cmap.GetOutputPort())
            actor.GetProperty().SetOpacity(0.9)
            renderer.AddActor(actor)
            self.mask_actors.append(actor)
        self.update_mask_slice()

        # 6) Add your text label
        text_prop = vtkTextProperty()
        text_prop.SetFontSize(20)
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
            self.update_mask_slice()
        self.viewer.Render()

    def contains(self, xn, yn):
        x0, y0, x1, y1 = self.viewport
        return x0 <= xn <= x1 and y0 <= yn <= y1

    def update_mask_slice(self):
        X, Y, Z = self.dims
        if self.name == 'Axial':
            ext = (0, X-1, 0, Y-1, self.slice, self.slice)
        elif self.name == 'Coronal':
            ext = (0, X-1, self.slice, self.slice, 0, Z-1)
        else:
            ext = (self.slice, self.slice, 0, Y-1, 0, Z-1)
        for actor in self.mask_actors:
            actor.SetDisplayExtent(*ext)

    def set_mask_opacity(self, opacity):
        for actor in self.mask_actors:
            actor.GetProperty().SetOpacity(opacity)


class QuadStyle(vtkInteractorStyleImage):
    def __init__(self, viewers, label_actors):
        super().__init__()
        self.viewers = viewers
        self.label_actors = label_actors      # ✅ 添加这一行
        self.selected_idx = -1                 # ✅ 初始选中第一个 mask
        self.edit_mode = False  # 初始为浏览模式
        self.mode_button = None  # 用于引用按钮 actor
        self.update_selection_visuals()       # ✅ 初始化高亮显示

        self.RemoveObservers('MouseWheelForwardEvent')
        self.RemoveObservers('MouseWheelBackwardEvent')
        self.AddObserver('MouseWheelForwardEvent', self.wheel_forward)
        self.AddObserver('MouseWheelBackwardEvent', self.wheel_backward)

        # new pan‐with‐left‐drag state
        self.panning = False
        self.active_viewer = None

        # hook left‐button events
        self.AddObserver('LeftButtonPressEvent',   self.on_left_button_press)
        self.AddObserver('MouseMoveEvent',         self.on_mouse_move)
        self.AddObserver('LeftButtonReleaseEvent', self.on_left_button_release)

        self.mode_button = None  # 会在 main 里赋值

    
    def update_selection_visuals(self):
        for sv in self.viewers:
            if self.edit_mode == True:
                opacities = [1.0 if i == self.selected_idx else 0.1 for i in range(len(sv.mask_actors))]
            else:
                opacities = [0.9] * len(sv.mask_actors)
            for actor, op in zip(sv.mask_actors, opacities):
                actor.GetProperty().SetOpacity(op)

        for i, actor in enumerate(self.label_actors):
            tp = actor.GetTextProperty()
            if self.edit_mode:
                if i == self.selected_idx:
                    tp.SetColor(1, 1, 0)
                    tp.SetFontSize(24)
                else:
                    tp.SetColor(1, 1, 1)
                    tp.SetFontSize(18)
            else:
                tp.SetColor(1, 1, 1)
                tp.SetFontSize(18)
            actor.SetTextProperty(tp)


    def on_left_button_press(self, obj, event):
        x, y = self.GetInteractor().GetEventPosition()
        w, h = self.GetInteractor().GetRenderWindow().GetSize()
        xn, yn = x / w, y / h  # ← 使用归一化坐标判断

        # 点击切换按钮
        if self.mode_button:
            pos = self.mode_button.GetPosition()
            if pos[0] <= xn <= pos[0]+0.15 and pos[1] <= yn <= pos[1]+0.05:
                self.edit_mode = not self.edit_mode
                self.mode_button.SetInput("Mode: Edit" if self.edit_mode else "Mode: Browse")
                self.update_selection_visuals() 
                self.GetInteractor().GetRenderWindow().Render()
                return

        # 编辑模式下处理 mask label 点击
        if self.edit_mode:
            for idx, actor in enumerate(self.label_actors):
                pos = actor.GetPosition()
                if pos[0] <= xn <= pos[0]+0.2 and pos[1] <= yn <= pos[1]+0.05:
                    self.selected_idx = idx
                    self.update_selection_visuals()
                    self.GetInteractor().GetRenderWindow().Render()
                    return

        # 浏览逻辑
        sv = self.pick_viewer()
        if sv is None:
            return
        self.active_viewer = sv
        self.panning = True
        cam = sv.viewer.GetRenderer().GetActiveCamera()
        cam.ParallelProjectionOn()
        self.SetCurrentRenderer(sv.viewer.GetRenderer())
        self.StartPan()



    def pick_viewer(self):
        x, y = self.GetInteractor().GetEventPosition()
        w, h = self.GetInteractor().GetRenderWindow().GetSize()
        xn, yn = x / w, y / h
        for sv in self.viewers:
            if sv.contains(xn, yn):
                return sv
        return None
    
    # pan start
    # def on_left_button_press(self, obj, event):
    #     sv = self.pick_viewer()
    #     if sv is None:
    #         return
    #     self.active_viewer = sv
    #     self.panning = True

    #     # make sure we pan in parallel projection
    #     cam = sv.viewer.GetRenderer().GetActiveCamera()
    #     cam.ParallelProjectionOn()

    #     # direct all pan commands to that renderer
    #     self.SetCurrentRenderer(sv.viewer.GetRenderer())

    #     # begin the pan interaction
    #     self.StartPan()
    #     # consume the event
    #     return

    # pan motion
    def on_mouse_move(self, obj, event):
        if not self.panning or self.active_viewer is None:
            return
        # keep panning in the same renderer
        self.SetCurrentRenderer(self.active_viewer.viewer.GetRenderer())
        self.Pan()
        return

    # pan end
    def on_left_button_release(self, obj, event):
        if not self.panning or self.active_viewer is None:
            return
        self.SetCurrentRenderer(self.active_viewer.viewer.GetRenderer())
        self.EndPan()
        # reset state
        self.panning = False
        self.active_viewer = None
        return

    def wheel_forward(self, obj, event):
        sv = self.pick_viewer()
        if not sv:
            return
        if self.GetInteractor().GetControlKey():
            cam = sv.viewer.GetRenderer().GetActiveCamera()
            cam.ParallelProjectionOn()
            cam.Zoom(1.1)
            sv.viewer.Render()
        else:
            sv.move(1)
        self.GetInteractor().GetRenderWindow().Render()

    def wheel_backward(self, obj, event):
        sv = self.pick_viewer()
        if not sv:
            return
        if self.GetInteractor().GetControlKey():
            cam = sv.viewer.GetRenderer().GetActiveCamera()
            cam.ParallelProjectionOn()
            cam.Zoom(0.9)
            sv.viewer.Render()
        else:
            sv.move(-1)
        self.GetInteractor().GetRenderWindow().Render()


def main(ct_path: str, mask_dir: str):
    img = cache_ct(ct_path)
    vtk_img, arr = sitk_to_vtk(img)

    mask_paths = sorted(glob.glob(os.path.join(mask_dir, '*.nii.gz')))
    if not mask_paths:
        mask_paths = sorted(glob.glob(os.path.join(mask_dir, '*.nii')))
    if not mask_paths:
        raise ValueError(f"No mask files found in directory: {mask_dir}")

    mask_colors_list = []
    legend_labels = []
    colors = [
        (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
        (1.0, 1.0, 0.0), (0.0, 1.0, 1.0), (1.0, 0.0, 1.0),
    ]
    for idx, mask_path in enumerate(mask_paths):
        label_text = os.path.basename(mask_path).split('.')[0]
        label_text = label_text.replace('_', ' ').replace('otsu', '').strip().title()
        legend_labels.append(label_text)

        mask_sitk = sitk.ReadImage(mask_path)
        resampler = sitk.ResampleImageFilter()
        resampler.SetReferenceImage(img)
        resampler.SetInterpolator(sitk.sitkNearestNeighbor)
        resampler.SetOutputPixelType(mask_sitk.GetPixelID())
        mask_resampled = resampler.Execute(mask_sitk)

        mask_vtk, _ = sitk_to_vtk(mask_resampled)
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(2)
        lut.SetTableValue(0, 0, 0, 0, 0.0)
        r, g, b = colors[idx % len(colors)]
        lut.SetTableValue(1, r, g, b, 0.6)
        lut.Build()

        cmap = vtk.vtkImageMapToColors()
        cmap.SetLookupTable(lut)
        cmap.SetOutputFormatToRGBA()
        cmap.SetInputData(mask_vtk)
        cmap.Update()
        mask_colors_list.append(cmap)

    dims = (arr.shape[2], arr.shape[1], arr.shape[0])
    render_window = vtkRenderWindow()
    render_window.SetSize(900, 900)
    render_window.SetNumberOfLayers(2)
    # render_window.SetOffScreenRendering(True) # Suppress separate window pop-ups 

    # Create quadrant slice viewers for each orientation 
    quads = {
        'Axial':    (0.0, 0.5, 0.5, 1.0),
        'Coronal':  (0.0, 0.0, 0.5, 0.5),
        'Sagittal': (0.5, 0.0, 1.0, 0.5)
    }
    viewers = []
    for name, vp in quads.items():
        sv = SliceViewer(vtk_img, arr, name.lower(), vp, name,
                         render_window, mask_colors_list, dims)
        viewers.append(sv)

    # 1) Create a blank layer-0 renderer to clear the top-right quadrant
    blank_quad = vtkRenderer()
    blank_quad.SetLayer(0)                  # non-transparent base layer
    blank_quad.InteractiveOff()
    blank_quad.SetViewport(0.5, 0.5, 1.0, 1.0)  # exactly the unused quadrant
    blank_quad.SetBackground(0, 0, 0)       # same as your other viewports
    render_window.AddRenderer(blank_quad)

    # 2) Legend overlay on layer 1, full‐window viewport, no color‐clear
    legend_overlay = vtkRenderer()
    legend_overlay.SetLayer(1)
    legend_overlay.InteractiveOff()
    legend_overlay.SetViewport(0.0, 0.0, 1.0, 1.0)
    # IMPORTANT: keep the existing imagery
    legend_overlay.PreserveColorBufferOn()  
    legend_overlay.EraseOff()              
    render_window.AddRenderer(legend_overlay)

    # 3) Build your legend as before, using normalized coords
    legend = vtkLegendBoxActor()
    num    = len(legend_labels)
    margin = 0.03
    quad_h = 0.5 - 2*margin

    legend.SetNumberOfEntries(num)
    legend.SetWidth(0.15)
    legend.SetHeight(quad_h)
    legend.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
    legend.GetPositionCoordinate().SetValue(0.8-margin, 0.48+margin)
    legend.UseBackgroundOn()
    legend.SetBackgroundColor(0.1, 0.1, 0.1)
    legend.GetProperty().SetOpacity(0.6)
    legend.GetProperty().SetLineWidth(0)

    text_prop = legend.GetEntryTextProperty()
    text_prop.SetColor(1,1,1)
    text_prop.SetVerticalJustificationToBottom()

    cube_size = quad_h / 5.0
    for i, lbl in enumerate(legend_labels):
        cube = vtk.vtkCubeSource()
        cube.SetXLength(cube_size)
        cube.SetYLength(cube_size)
        cube.SetZLength(cube_size)
        cube.Update()
        legend.SetEntry(i, cube.GetOutput(), lbl, colors[i % len(colors)])

    legend_overlay.AddActor(legend)

    # 添加点击按钮文本
    label_actors = []
    width, height = render_window.GetSize()
    for i, lbl in enumerate(legend_labels):
        t = vtkTextActor()
        t.SetInput(lbl)
        prop = t.GetTextProperty()
        prop.SetFontSize(18)
        prop.SetColor(1,1,1)
        t.SetTextProperty(prop)
        pos_x = 0.5
        pos_y = 0.75 - 0.05 * i
        t.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        t.SetPosition(pos_x, pos_y)
        legend_overlay.AddActor(t)
        label_actors.append(t)
    
    # 添加模式切换按钮
    mode_btn = vtkTextActor()
    mode_btn.SetInput("Mode: Browse")
    mode_btn.GetTextProperty().SetFontSize(20)
    mode_btn.GetTextProperty().SetColor(0, 1, 1)
    mode_btn.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
    mode_btn.SetPosition(0.5, 0.85)  
    legend_overlay.AddActor(mode_btn)



    # Switch on visible rendering
    render_window.SetOffScreenRendering(False)
    render_window.Render()

    interactor = vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.SetInteractorStyle(QuadStyle(viewers, label_actors))
    style = QuadStyle(viewers, label_actors)
    style.mode_button = mode_btn  # 设置按钮 actor 引用
    interactor.SetInteractorStyle(style)
    interactor.Initialize()
    interactor.Start()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='CT Quad Viewer')
    parser.add_argument('ct_file', help='Path to CT directory or file')
    parser.add_argument('mask_dir', help='Directory of segmentation mask files')
    args = parser.parse_args()
    main(args.ct_file, args.mask_dir)
