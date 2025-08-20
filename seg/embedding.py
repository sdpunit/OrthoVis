#!/usr/bin/env python3
"""
VTK Pipeline for Qt Integration with Editing Features
Extracted and adapted from renderer.py to work with Qt widgets
"""
import os, glob
import vtk 
import SimpleITK as sitk
import numpy as np
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules.vtkInteractionImage import vtkImageViewer2
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkActor2D,
    vtkTextMapper,
    vtkTextProperty,
    vtkTextActor
)
from vtkmodules.vtkRenderingAnnotation import vtkLegendBoxActor
from vtkmodules.util import numpy_support
from seg.totalseg import load_ct

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


class EditableMask:
    """Wrapper for mask data that supports editing operations"""
    def __init__(self, mask_sitk, mask_path, color, cmap):
        self.original_sitk = mask_sitk
        self.path = mask_path
        self.color = color
        self.cmap = cmap
        
        # Convert to numpy for easy editing
        self.data = sitk.GetArrayFromImage(mask_sitk)
        self.modified = False
        
        # Keep reference to VTK image data for faster updates
        self.vtk_data = self.cmap.GetInput()
        
    def update_vtk_data(self):
        """Update VTK visualization after editing - FAST version"""
        # Instead of updating the entire array, just mark as modified
        # and let VTK handle the update efficiently
        vtk_scalars = self.vtk_data.GetPointData().GetScalars()
        
        # CRITICAL: Only mark as modified, don't update individual values
        vtk_scalars.Modified()
        self.vtk_data.Modified()
        self.cmap.Modified()
        
        # Force immediate pipeline update
        self.cmap.Update()
        self.modified = True
    
    def save_mask(self, output_path=None):
        """Save the edited mask"""
        if not self.modified:
            return
            
        if output_path is None:
            output_path = self.path
            
        # Convert back to SimpleITK
        edited_sitk = sitk.GetImageFromArray(self.data)
        edited_sitk.CopyInformation(self.original_sitk)
        sitk.WriteImage(edited_sitk, output_path)
        print(f"Saved edited mask: {output_path}")


class SliceViewer:
    def __init__(self, vtk_img, arr, orientation, viewport, name,
                 render_window, mask_data=None, dims=None, enable_editing=False):

        self.name = name
        self.viewport = viewport
        self.dims = dims
        self.slice = 0
        self.min_slice = 0
        self.enable_editing = enable_editing

        # Store mask data for editing (either EditableMask objects or color maps)
        if enable_editing and mask_data:
            self.editable_masks = mask_data  # List of EditableMask objects
            self.mask_actors = []
        else:
            self.mask_colors_list = mask_data  # List of color maps for browse-only
            self.mask_actors = []

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

        # 5) Add your mask actors *into* that same renderer (if masks exist)
        if mask_data is not None:
            if enable_editing:
                # For editing mode, use EditableMask objects
                for emask in self.editable_masks:
                    actor = vtk.vtkImageActor()
                    actor.GetMapper().SetInputConnection(emask.cmap.GetOutputPort())
                    actor.GetProperty().SetOpacity(0.9)
                    renderer.AddActor(actor)
                    self.mask_actors.append(actor)
            else:
                # For browse-only mode, use color maps directly
                for cmap in self.mask_colors_list:
                    actor = vtk.vtkImageActor()
                    actor.GetMapper().SetInputConnection(cmap.GetOutputPort())
                    actor.GetProperty().SetOpacity(0.9)
                    renderer.AddActor(actor)
                    self.mask_actors.append(actor)
            self.update_mask_slice()

        # 6) Add your text label
        text_prop = vtkTextProperty()
        text_prop.SetFontSize(16 if not enable_editing else 20)
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
            if self.mask_actors:  # Only update masks if they exist
                self.update_mask_slice()
        self.viewer.Render()

    def contains(self, xn, yn):
        x0, y0, x1, y1 = self.viewport
        return x0 <= xn <= x1 and y0 <= yn <= y1

    def update_mask_slice(self):
        if not self.mask_actors or not self.dims:  # Skip if no masks or dims
            return
            
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

    def add_masks(self, mask_data, dims, enable_editing=False):
        """Add masks to existing viewer"""
        self.dims = dims
        self.enable_editing = enable_editing
        renderer = self.viewer.GetRenderer()
        
        # Remove existing mask actors
        for actor in self.mask_actors:
            renderer.RemoveActor(actor)
        self.mask_actors.clear()
        
        # Store mask data based on editing mode
        if enable_editing:
            self.editable_masks = mask_data
        else:
            self.mask_colors_list = mask_data
        
        # Add new mask actors
        if enable_editing:
            for emask in self.editable_masks:
                actor = vtk.vtkImageActor()
                actor.GetMapper().SetInputConnection(emask.cmap.GetOutputPort())
                actor.GetProperty().SetOpacity(0.9)
                renderer.AddActor(actor)
                self.mask_actors.append(actor)
        else:
            for cmap in self.mask_colors_list:
                actor = vtk.vtkImageActor()
                actor.GetMapper().SetInputConnection(cmap.GetOutputPort())
                actor.GetProperty().SetOpacity(0.9)
                renderer.AddActor(actor)
                self.mask_actors.append(actor)
        
        self.update_mask_slice()
        self.viewer.Render()

    # EDITING METHODS (only active when enable_editing=True)
    def world_to_image_coords(self, world_pos):
        """Convert world coordinates to image array indices"""
        if not self.enable_editing:
            return None
            
        # Get the image data from viewer
        img_data = self.viewer.GetInput()
        spacing = img_data.GetSpacing()
        origin = img_data.GetOrigin()
        
        # Convert world to continuous image coordinates
        x_img = (world_pos[0] - origin[0]) / spacing[0]
        y_img = (world_pos[1] - origin[1]) / spacing[1] 
        z_img = (world_pos[2] - origin[2]) / spacing[2]
        
        # Convert to integer indices
        i = int(round(x_img))  # X coordinate
        j = int(round(y_img))  # Y coordinate
        k = int(round(z_img))  # Z coordinate
        
        return i, j, k
    
    def edit_pixel(self, world_pos, mask_idx, operation, brush_size=1):
        """Edit pixels in the mask at world position - OPTIMIZED version
        operation: 'paint' to set to 1, 'erase' to set to 0
        """
        if not self.enable_editing or mask_idx >= len(self.editable_masks):
            return False
            
        i, j, k = self.world_to_image_coords(world_pos)
        mask = self.editable_masks[mask_idx]
        
        # Get mask dimensions (Z, Y, X) - numpy ordering
        Z, Y, X = mask.data.shape
        
        # Collect all changes before updating VTK
        changed_pixels = []
        
        # Apply brush in 2D slice
        for di in range(-brush_size, brush_size + 1):
            for dj in range(-brush_size, brush_size + 1):
                if di*di + dj*dj <= brush_size*brush_size:  # circular brush
                    
                    # Calculate target coordinates based on view orientation
                    if self.name == 'Axial':
                        ni, nj, nk = i + di, j + dj, self.slice
                    elif self.name == 'Coronal':
                        ni, nj, nk = i + di, self.slice, k + dj  
                    elif self.name == 'Sagittal':
                        ni, nj, nk = self.slice, j + dj, k + di
                    else:
                        continue
                        
                    # Check bounds and update
                    if 0 <= ni < X and 0 <= nj < Y and 0 <= nk < Z:
                        old_val = mask.data[nk, nj, ni]  # [Z, Y, X]
                        new_val = 1 if operation == 'paint' else 0
                        
                        if old_val != new_val:
                            # Update numpy array
                            mask.data[nk, nj, ni] = new_val
                            
                            # Calculate flat index for VTK
                            flat_idx = nk * Y * X + nj * X + ni
                            changed_pixels.append((flat_idx, new_val))
        
        # Update VTK efficiently - batch update
        if changed_pixels:
            vtk_scalars = mask.vtk_data.GetPointData().GetScalars()
            
            # Update only changed pixels
            for flat_idx, value in changed_pixels:
                vtk_scalars.SetValue(flat_idx, value)
            
            # Single Modified() call for all changes
            vtk_scalars.Modified()
            mask.vtk_data.Modified()
            mask.cmap.Modified()
            mask.cmap.Update()
            mask.modified = True
            
            # Force immediate render - just this viewer
            self.viewer.Render()
            
        return len(changed_pixels) > 0


class QuadStyle(vtkInteractorStyleImage):
    def __init__(self, viewers, arr, origin, spacing, enable_editing=False, 
                 label_actors=None, editable_masks=None):
        super().__init__()
        self.viewers = viewers
        self.arr = arr
        self.origin = origin
        self.spacing = spacing
        self.enable_editing = enable_editing
        
        # Editing-specific attributes
        if enable_editing:
            self.label_actors = label_actors or []
            self.editable_masks = editable_masks or []
            self.selected_idx = 0
            self.edit_mode = False
            self.mode_button = None
            self.brush_size = 1
            self.brush_label = None
            self.editing = False
            self.last_edit_pos = None
            self.update_selection_visuals()
            
            # Add editing event observers
            self.AddObserver('KeyPressEvent', self.on_key_press)
        
        # Common observers
        self.RemoveObservers('MouseWheelForwardEvent')
        self.RemoveObservers('MouseWheelBackwardEvent')
        self.AddObserver('MouseWheelForwardEvent', self.wheel_forward)
        self.AddObserver('MouseWheelBackwardEvent', self.wheel_backward)

        # Pan state
        self.panning = False
        self.active_viewer = None

        # Hook left button events
        self.AddObserver('LeftButtonPressEvent',   self.on_left_button_press)
        self.AddObserver('MouseMoveEvent',         self.on_mouse_move)
        self.AddObserver('LeftButtonReleaseEvent', self.on_left_button_release)

    def pick_viewer(self):
        x, y = self.GetInteractor().GetEventPosition()
        w, h = self.GetInteractor().GetRenderWindow().GetSize()
        xn, yn = x / w, y / h
        for sv in self.viewers:
            if sv.contains(xn, yn):
                return sv
        return None

    def get_world_position(self, viewer):
        """Get world position under mouse cursor"""
        if not self.enable_editing:
            return None
            
        x, y = self.GetInteractor().GetEventPosition()
        
        # Use the same coordinate conversion approach that worked in the test
        renderer = viewer.viewer.GetRenderer()
        
        # Convert window coordinates to world coordinates
        renderer.SetDisplayPoint(x, y, 0)
        renderer.DisplayToWorld()
        world_pos = renderer.GetWorldPoint()
        
        # Return the 3D world position
        return world_pos[:3]

    def update_selection_visuals(self):
        """Update visual feedback for editing mode"""
        if not self.enable_editing:
            return
            
        for sv in self.viewers:
            if self.edit_mode:
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
        xn, yn = x / w, y / h

        # Editing mode handling
        if self.enable_editing:
            # Click mode toggle button
            if self.mode_button:
                pos = self.mode_button.GetPosition()
                if pos[0] <= xn <= pos[0]+0.15 and pos[1] <= yn <= pos[1]+0.05:
                    self.edit_mode = not self.edit_mode
                    self.mode_button.SetInput("Mode: Edit" if self.edit_mode else "Mode: Browse")
                    self.update_selection_visuals() 
                    self.GetInteractor().GetRenderWindow().Render()
                    return

            # Edit mode: handle mask label clicks
            if self.edit_mode:
                for idx, actor in enumerate(self.label_actors):
                    pos = actor.GetPosition()
                    if pos[0] <= xn <= pos[0]+0.2 and pos[1] <= yn <= pos[1]+0.05:
                        self.selected_idx = idx
                        self.update_selection_visuals()
                        self.GetInteractor().GetRenderWindow().Render()
                        return

        # Get viewer under cursor
        sv = self.pick_viewer()
        if sv is None:
            return

        # Check modifier keys for editing
        if self.enable_editing:
            ctrl_key = self.GetInteractor().GetControlKey()
            shift_key = self.GetInteractor().GetShiftKey()

            if ctrl_key and shift_key:
                # Ctrl+Shift+Left drag = Pan
                self.start_pan(sv)
            elif self.edit_mode:
                # Edit mode: start editing
                world_pos = self.get_world_position(sv)
                if world_pos:
                    operation = 'erase' if ctrl_key else 'paint'
                    sv.edit_pixel(world_pos, self.selected_idx, operation, self.brush_size)
                    self.editing = True
                    self.last_edit_pos = world_pos
            else:
                # Browse mode with no modifiers: start panning
                self.start_pan(sv)
        else:
            # Non-editing mode: always pan
            self.start_pan(sv)

    def start_pan(self, sv):
        """Start panning operation"""
        self.active_viewer = sv
        self.panning = True

        # make sure we pan in parallel projection
        cam = sv.viewer.GetRenderer().GetActiveCamera()
        cam.ParallelProjectionOn()

        # direct all pan commands to that renderer
        self.SetCurrentRenderer(sv.viewer.GetRenderer())

        # begin the pan interaction
        self.StartPan()

    def on_mouse_move(self, obj, event):
        # Handle panning
        if self.panning and self.active_viewer is not None:
            self.SetCurrentRenderer(self.active_viewer.viewer.GetRenderer())
            self.Pan()
            return
        
        # Handle editing (only in editing mode)
        if self.enable_editing and self.editing and self.edit_mode:
            sv = self.pick_viewer()
            if sv:
                world_pos = self.get_world_position(sv)
                if world_pos:
                    # Determine operation based on modifier keys
                    ctrl_key = self.GetInteractor().GetControlKey()
                    operation = 'erase' if ctrl_key else 'paint'
                    
                    # Edit immediately for smooth editing
                    sv.edit_pixel(world_pos, self.selected_idx, operation, self.brush_size)

    def on_left_button_release(self, obj, event):
        if self.panning and self.active_viewer is not None:
            self.SetCurrentRenderer(self.active_viewer.viewer.GetRenderer())
            self.EndPan()
            self.panning = False
            self.active_viewer = None
        
        if self.enable_editing and self.editing:
            self.editing = False
            self.last_edit_pos = None

    def on_key_press(self, obj, event):
        """Handle keyboard shortcuts for editing"""
        if not self.enable_editing:
            return
            
        key = self.GetInteractor().GetKeySym()
        
        if key == 'plus' or key == 'equal':
            self.brush_size = min(self.brush_size + 1, 10)
            self.update_brush_label()
        elif key == 'minus':
            self.brush_size = max(self.brush_size - 1, 1)
            self.update_brush_label()
        elif key == 's':
            # Save all modified masks
            self.save_masks()
        elif key == 'r':
            # Reset current mask to original
            if self.edit_mode and self.selected_idx < len(self.editable_masks):
                self.reset_mask(self.selected_idx)

    def update_brush_label(self):
        """Update brush size display"""
        if self.brush_label:
            self.brush_label.SetInput(f"Brush Size: {self.brush_size}")
            self.GetInteractor().GetRenderWindow().Render()

    def save_masks(self):
        """Save all modified masks"""
        if not self.enable_editing:
            return
            
        saved_count = 0
        for mask in self.editable_masks:
            if mask.modified:
                mask.save_mask()
                saved_count += 1
        
        if saved_count > 0:
            print(f"Saved {saved_count} modified masks")
        else:
            print("No masks were modified")

    def reset_mask(self, idx):
        """Reset mask to original state"""
        if not self.enable_editing or idx >= len(self.editable_masks):
            return
            
        mask = self.editable_masks[idx]
        mask.data = sitk.GetArrayFromImage(mask.original_sitk).copy()
        mask.update_vtk_data()
        mask.modified = False
        
        # Force render update
        if self.viewers:
            render_window = self.viewers[0].viewer.GetRenderWindow()
            render_window.Render()
        
        print(f"Reset mask {idx} to original state")

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


def create_vtk_pipeline(ct_path: str, mask_dir: str = None, render_window=None, enable_editing=False):
    """
    Create the VTK pipeline for the quad viewer.
    Returns the interactor style that should be attached to the render window's interactor.
    
    Args:
        ct_path: Path to CT directory
        mask_dir: Optional path to mask directory. If None, only CT will be displayed
        render_window: Qt render window to use
        enable_editing: Enable mask editing features
    """
    # Suppress VTK warnings and prevent automatic window creation
    vtk.vtkObject.GlobalWarningDisplayOff()
    
    # Ensure we have a render window
    if render_window is None:
        raise ValueError("render_window must be provided for Qt integration")
    
    img = cache_ct(ct_path)
    vtk_img, arr = sitk_to_vtk(img)

    # Handle optional mask processing
    mask_data = []
    editable_masks = []
    legend_labels = []
    colors = [
        (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
        (1.0, 1.0, 0.0), (0.0, 1.0, 1.0), (1.0, 0.0, 1.0),
    ]
    
    if mask_dir is not None:
        mask_paths = sorted(glob.glob(os.path.join(mask_dir, '*.nii.gz')))
        if not mask_paths:
            mask_paths = sorted(glob.glob(os.path.join(mask_dir, '*.nii')))
        
        if mask_paths:  # Only process if masks found
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

                if enable_editing:
                    # Create EditableMask objects for editing
                    editable_mask = EditableMask(mask_resampled, mask_path, colors[idx % len(colors)], cmap)
                    editable_masks.append(editable_mask)
                    mask_data.append(editable_mask)
                else:
                    # Just store color maps for browsing
                    mask_data.append(cmap)

    dims = (arr.shape[2], arr.shape[1], arr.shape[0])
    
    # Configure the provided render window
    render_window.SetNumberOfLayers(2 if legend_labels else 1)  # Only use 2 layers if we have legends

    # Create quadrant slice viewers for each orientation 
    quads = {
        'Axial':    (0.0, 0.5, 0.5, 1.0),
        'Coronal':  (0.0, 0.0, 0.5, 0.5),
        'Sagittal': (0.5, 0.0, 1.0, 0.5)
    }
    viewers = []
    for name, vp in quads.items():
        sv = SliceViewer(vtk_img, arr, name.lower(), vp, name,
                         render_window, 
                         mask_data if mask_data else None, 
                         dims if mask_data else None,
                         enable_editing=enable_editing)
        viewers.append(sv)

    label_actors = []
    
    # Only create legend and UI if we have masks
    if legend_labels:
        # 1) Create a blank layer-0 renderer to clear the top-right quadrant
        blank_quad = vtkRenderer()
        blank_quad.SetLayer(0)                  # non-transparent base layer
        blank_quad.InteractiveOff()
        blank_quad.SetViewport(0.5, 0.5, 1.0, 1.0)  # exactly the unused quadrant
        blank_quad.SetBackground(0, 0, 0)       # same as your other viewports
        render_window.AddRenderer(blank_quad)

        # 2) Legend overlay on layer 1, full window viewport, no color clear
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
        num = len(legend_labels)
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

        # Add editing UI elements if editing is enabled
        if enable_editing:
            # Add clickable mask labels
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

            # Add mode toggle button
            mode_btn = vtkTextActor()
            mode_btn.SetInput("Mode: Browse")
            mode_btn.GetTextProperty().SetFontSize(20)
            mode_btn.GetTextProperty().SetColor(0, 1, 1)
            mode_btn.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            mode_btn.SetPosition(0.5, 0.85)
            legend_overlay.AddActor(mode_btn)

            # Add brush size indicator
            brush_label = vtkTextActor()
            brush_label.SetInput("Brush Size: 1")
            brush_label.GetTextProperty().SetFontSize(16)
            brush_label.GetTextProperty().SetColor(1, 0.5, 0)
            brush_label.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            brush_label.SetPosition(0.5, 0.9)
            legend_overlay.AddActor(brush_label)

    # Create and return the interactor style
    interactor_style = QuadStyle(viewers, arr, img.GetOrigin(), img.GetSpacing(), 
                                enable_editing=enable_editing,
                                label_actors=label_actors if enable_editing else None,
                                editable_masks=editable_masks if enable_editing else None)
    
    # Set UI references for editing mode
    if enable_editing and legend_labels:
        interactor_style.mode_button = mode_btn
        interactor_style.brush_label = brush_label
    
    return interactor_style


def add_masks_to_pipeline(viewers, img, mask_dir, render_window, enable_editing=False):
    """
    Add masks to an existing VTK pipeline.
    This function can be called after initial CT-only visualization.
    
    Args:
        viewers: List of SliceViewer objects
        img: SimpleITK image object (CT)
        mask_dir: Directory containing mask files
        render_window: VTK render window
        enable_editing: Enable mask editing features
    
    Returns:
        tuple: (success_boolean, editable_masks_list_or_None)
    """
    try:
        mask_paths = sorted(glob.glob(os.path.join(mask_dir, '*.nii.gz')))
        if not mask_paths:
            mask_paths = sorted(glob.glob(os.path.join(mask_dir, '*.nii')))
        
        if not mask_paths:
            print(f"No mask files found in directory: {mask_dir}")
            return False, None

        mask_data = []
        editable_masks = []
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

            if enable_editing:
                # Create EditableMask objects for editing
                editable_mask = EditableMask(mask_resampled, mask_path, colors[idx % len(colors)], cmap)
                editable_masks.append(editable_mask)
                mask_data.append(editable_mask)
            else:
                # Just store color maps for browsing
                mask_data.append(cmap)

        # Get array dimensions for mask positioning
        vtk_img, arr = sitk_to_vtk(img)
        dims = (arr.shape[2], arr.shape[1], arr.shape[0])
        
        # Add masks to each viewer
        for viewer in viewers:
            viewer.add_masks(mask_data, dims, enable_editing=enable_editing)
        
        # Update render window to use 2 layers and add legend
        render_window.SetNumberOfLayers(2)
        
        # Create blank quad and legend (same as in create_vtk_pipeline)
        blank_quad = vtkRenderer()
        blank_quad.SetLayer(0)
        blank_quad.InteractiveOff()
        blank_quad.SetViewport(0.5, 0.5, 1.0, 1.0)
        blank_quad.SetBackground(0, 0, 0)
        render_window.AddRenderer(blank_quad)

        legend_overlay = vtkRenderer()
        legend_overlay.SetLayer(1)
        legend_overlay.InteractiveOff()
        legend_overlay.SetViewport(0.0, 0.0, 1.0, 1.0)
        legend_overlay.PreserveColorBufferOn()
        legend_overlay.EraseOff()
        render_window.AddRenderer(legend_overlay)

        legend = vtkLegendBoxActor()
        num = len(legend_labels)
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
        
        # Add editing UI elements if editing is enabled
        if enable_editing:
            # Add clickable mask labels
            label_actors = []
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

            # Add mode toggle button
            mode_btn = vtkTextActor()
            mode_btn.SetInput("Mode: Browse")
            mode_btn.GetTextProperty().SetFontSize(20)
            mode_btn.GetTextProperty().SetColor(0, 1, 1)
            mode_btn.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            mode_btn.SetPosition(0.5, 0.85)
            legend_overlay.AddActor(mode_btn)

            # Add brush size indicator
            brush_label = vtkTextActor()
            brush_label.SetInput("Brush Size: 1")
            brush_label.GetTextProperty().SetFontSize(16)
            brush_label.GetTextProperty().SetColor(1, 0.5, 0)
            brush_label.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            brush_label.SetPosition(0.5, 0.9)
            legend_overlay.AddActor(brush_label)
        
        # Render the updated window
        render_window.Render()
        
        return True, (editable_masks if enable_editing else None)
        
    except Exception as e:
        print(f"Error adding masks to pipeline: {e}")
        return False, None


def update_interactor_style_for_editing(interactor_style, label_actors, editable_masks, 
                                       mode_button, brush_label):
    """
    Update an existing interactor style to enable editing features.
    Call this after add_masks_to_pipeline when editing is enabled.
    
    Args:
        interactor_style: Existing QuadStyle instance
        label_actors: List of label text actors
        editable_masks: List of EditableMask objects
        mode_button: Mode toggle button actor
        brush_label: Brush size label actor
    """
    if not hasattr(interactor_style, 'enable_editing'):
        return
        
    interactor_style.enable_editing = True
    interactor_style.label_actors = label_actors
    interactor_style.editable_masks = editable_masks
    interactor_style.mode_button = mode_button
    interactor_style.brush_label = brush_label
    interactor_style.selected_idx = 0
    interactor_style.edit_mode = False
    interactor_style.brush_size = 1
    interactor_style.editing = False
    interactor_style.last_edit_pos = None
    
    # Add editing event observers if not already present
    if not hasattr(interactor_style, '_editing_observers_added'):
        interactor_style.AddObserver('KeyPressEvent', interactor_style.on_key_press)
        interactor_style._editing_observers_added = True
    
    # Update visual state
    interactor_style.update_selection_visuals()