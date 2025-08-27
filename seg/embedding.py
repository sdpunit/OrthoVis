#!/usr/bin/env python3
"""
VTK Pipeline for Qt Integration with editing features
Updated: remove coloured legend squares; when edit mode toggles on, the
currently selected mask's label enlarges and adopts that mask's colour.
"""
import os, glob
import vtk
import SimpleITK as sitk
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules.vtkInteractionImage import vtkImageViewer2
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkActor2D,
    vtkTextMapper,
    vtkTextProperty,
    vtkTextActor,
    vtkActor
)
from vtkmodules.vtkFiltersSources import vtkDiskSource
from vtkmodules.util import numpy_support
from seg.totalseg import load_ct

# Legend horizontal position inside the upper-right quadrant (0 = left edge, 1 = right edge)
LEGEND_X_FRACTION_IN_URQ = 0.4

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

class BrushCursor:
    """Dynamic brush cursor that changes size with brush size"""
    def __init__(self, render_window):
        self.render_window = render_window
        self.cursor_actors = {}  # One cursor actor per viewer
        self.visible = False
        self.current_size = 1
        
    def create_cursor_for_viewer(self, viewer):
        """Create a cursor actor for a specific viewer"""
        # Create a circle geometry
        disk = vtkDiskSource()
        disk.SetInnerRadius(0)
        disk.SetOuterRadius(1.0)  # Will be scaled
        disk.SetRadialResolution(1)
        disk.SetCircumferentialResolution(16)
        disk.Update()
        
        # Create mapper and actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(disk.GetOutputPort())
        
        actor = vtkActor()
        actor.SetMapper(mapper)
        
        # Set cursor properties - semi-transparent white circle
        actor.GetProperty().SetColor(0.5, 0.5, 0.5)
        actor.GetProperty().SetOpacity(0.8)
        actor.GetProperty().SetRepresentationToWireframe()
        actor.GetProperty().SetLineWidth(3)
        
        # Set orientation based on view
        if viewer.name == 'Axial':
            # Axial view: circle lies in X-Y plane. No rotation needed.
            actor.SetOrientation(0, 0, 0)
        elif viewer.name == 'Coronal':
            # Coronal view: circle lies in X-Z plane. Rotate 90° around X-axis.
            actor.SetOrientation(90, 0, 0)
        elif viewer.name == 'Sagittal':
            # Sagittal view: circle lies in Y-Z plane. Rotate 90° around Y-axis.
            actor.SetOrientation(0, 90, 0)
        
        # Initially hide the cursor
        actor.SetVisibility(False)
        
        # Add to renderer
        viewer.viewer.GetRenderer().AddActor(actor)
        
        return actor
    
    def update_cursor_size(self, brush_size):
        """Update cursor size for all viewers"""
        self.current_size = brush_size
        
        for viewer, actor in self.cursor_actors.items():
            # Get image spacing to calculate world size
            img_data = viewer.viewer.GetInput()
            spacing = img_data.GetSpacing()
            
            # Calculate radius in world coordinates based on view orientation
            if viewer.name == 'Axial':
                min_spacing = min(spacing[0], spacing[1])
            elif viewer.name == 'Coronal':
                min_spacing = min(spacing[0], spacing[2])
            elif viewer.name == 'Sagittal':
                min_spacing = min(spacing[1], spacing[2])
            else:
                min_spacing = min(spacing[:3])
            
            world_radius = brush_size * min_spacing
            
            # The vtkDiskSource is in its local XY plane. We scale it uniformly
            # in X and Y. The actor's orientation handles placing this scaled
            # circle into the correct view plane.
            actor.SetScale(world_radius, world_radius, 1.0)
    
    def update_cursor_position(self, viewer, world_pos):
        """Update cursor position for a specific viewer"""
        if viewer not in self.cursor_actors:
            self.cursor_actors[viewer] = self.create_cursor_for_viewer(viewer)
            self.update_cursor_size(self.current_size)
        
        actor = self.cursor_actors[viewer]
        
        # Position cursor based on the slice plane
        if viewer.name == 'Axial':
            img_data = viewer.viewer.GetInput()
            spacing, origin = img_data.GetSpacing(), img_data.GetOrigin()
            slice_z = origin[2] + viewer.slice * spacing[2]
            actor.SetPosition(world_pos[0], world_pos[1], slice_z)
        elif viewer.name == 'Coronal':
            img_data = viewer.viewer.GetInput()
            spacing, origin = img_data.GetSpacing(), img_data.GetOrigin()
            slice_y = origin[1] + viewer.slice * spacing[1]
            actor.SetPosition(world_pos[0], slice_y, world_pos[2])
        elif viewer.name == 'Sagittal':
            img_data = viewer.viewer.GetInput()
            spacing, origin = img_data.GetSpacing(), img_data.GetOrigin()
            slice_x = origin[0] + viewer.slice * spacing[0]
            actor.SetPosition(slice_x, world_pos[1], world_pos[2])
        
        if not self.visible:
            self.show_cursor()
    
    def show_cursor(self):
        """Show cursor in all viewers"""
        self.visible = True
        for actor in self.cursor_actors.values():
            actor.SetVisibility(True)
        self.render_window.Render()
    
    def hide_cursor(self):
        """Hide cursor in all viewers"""
        self.visible = False
        for actor in self.cursor_actors.values():
            actor.SetVisibility(False)
        self.render_window.Render()
    
    def show_cursor_in_viewer(self, viewer):
        """Show cursor only in a specific viewer"""
        for v, actor in self.cursor_actors.items():
            actor.SetVisibility(v == viewer)
        self.render_window.Render()


class EditableMask:
    """Wrapper for mask data that supports editing operations"""
    def __init__(self, mask_sitk, mask_path, color, cmap):
        self.original_sitk = mask_sitk
        self.path = mask_path
        self.color = color  # (r,g,b)
        self.cmap = cmap

        # Convert to numpy for easy editing
        self.data = sitk.GetArrayFromImage(mask_sitk)
        self.modified = False

        # Keep reference to VTK image data for faster updates
        self.vtk_data = self.cmap.GetInput()

    def update_vtk_data(self):
        """Update VTK visualization after editing - FAST version"""
        vtk_scalars = self.vtk_data.GetPointData().GetScalars()
        vtk_scalars.Modified()
        self.vtk_data.Modified()
        self.cmap.Modified()
        self.cmap.Update()
        self.modified = True

    def save_mask(self, output_path=None):
        """Save the edited mask"""
        if not self.modified:
            return
        if output_path is None:
            output_path = self.path
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

        if enable_editing and mask_data:
            self.editable_masks = mask_data
            self.mask_actors = []
        else:
            self.mask_colors_list = mask_data
            self.mask_actors = []

        self.viewer = vtkImageViewer2()
        self.viewer.SetRenderWindow(render_window)
        self.viewer.SetInputData(vtk_img)

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
        self.viewer.SetupInteractor(render_window.GetInteractor())
        renderer = self.viewer.GetRenderer()
        renderer.SetViewport(*viewport)
        renderer.SetBackground(0, 0, 0)

        if mask_data is not None:
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
            if self.mask_actors:
                self.update_mask_slice()
        self.viewer.Render()

    def contains(self, xn, yn):
        x0, y0, x1, y1 = self.viewport
        return x0 <= xn <= x1 and y0 <= yn <= y1

    def update_mask_slice(self):
        if not self.mask_actors or not self.dims:
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
        self.dims = dims
        self.enable_editing = enable_editing
        renderer = self.viewer.GetRenderer()
        for actor in self.mask_actors:
            renderer.RemoveActor(actor)
        self.mask_actors.clear()
        if enable_editing:
            self.editable_masks = mask_data
        else:
            self.mask_colors_list = mask_data
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

    def world_to_image_coords(self, world_pos):
        if not self.enable_editing: return None
        img_data = self.viewer.GetInput()
        spacing, origin = img_data.GetSpacing(), img_data.GetOrigin()
        x_img = (world_pos[0] - origin[0]) / spacing[0]
        y_img = (world_pos[1] - origin[1]) / spacing[1]
        z_img = (world_pos[2] - origin[2]) / spacing[2]
        return int(round(x_img)), int(round(y_img)), int(round(z_img))

    def edit_pixel(self, world_pos, mask_idx, operation, brush_size=1):
        """Edit pixels in the mask at world position with proper spacing compensation"""
        if mask_idx >= len(self.editable_masks):
            return False
            
        i, j, k = self.world_to_image_coords(world_pos)
        mask = self.editable_masks[mask_idx]
        
        # Get mask dimensions (Z, Y, X) - numpy ordering
        Z, Y, X = mask.data.shape
        
        # Get image spacing for proper circular brush scaling
        img_data = self.viewer.GetInput()
        spacing = img_data.GetSpacing()
        
        # Calculate brush radius in world units
        if self.name == 'Axial':
            # X-Y plane
            min_spacing = min(spacing[0], spacing[1])
            world_radius = brush_size * min_spacing
            dx = world_radius / spacing[0]
            dy = world_radius / spacing[1]
        elif self.name == 'Coronal':
            # X-Z plane
            min_spacing = min(spacing[0], spacing[2])
            world_radius = brush_size * min_spacing
            dx = world_radius / spacing[0]
            dy = world_radius / spacing[2]
        elif self.name == 'Sagittal':
            # Y-Z plane
            min_spacing = min(spacing[1], spacing[2])
            world_radius = brush_size * min_spacing
            dx = world_radius / spacing[1]
            dy = world_radius / spacing[2]
        
        # Convert to integer pixel radius, ensuring at least 1 pixel
        rx = max(1, int(round(dx)))
        ry = max(1, int(round(dy)))
        
        # Collect all changes before updating VTK
        changed_pixels = []
        
        # Apply brush in 2D slice
        for di in range(-rx, rx + 1):
            for dj in range(-ry, ry + 1):
                # Calculate normalized distance for circular brush
                normalized_di = di * (spacing[0] if self.name in ['Axial', 'Coronal'] else spacing[1]) / world_radius
                normalized_dj = dj * (spacing[1] if self.name == 'Axial' else spacing[2]) / world_radius
                
                if normalized_di**2 + normalized_dj**2 <= 1.0:  # circular brush
                    
                    # Calculate target coordinates based on view orientation
                    if self.name == 'Axial':
                        ni, nj, nk = i + di, j + dj, self.slice
                    elif self.name == 'Coronal':
                        ni, nj, nk = i + di, self.slice, k + dj
                    elif self.name == 'Sagittal':
                        ni, nj, nk = self.slice, j + di, k + dj  # Changed from j + dj, k + di
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
                 label_actors=None, editable_masks=None, save_callback=None):
        super().__init__()
        self.viewers = viewers
        self.arr = arr
        self.origin = origin
        self.spacing = spacing
        self.enable_editing = enable_editing
        self.save_callback = save_callback
        
        # Cursor functionality
        self.brush_cursor = None

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
            self.AddObserver('KeyPressEvent', self.on_key_press)

        self.RemoveObservers('MouseWheelForwardEvent')
        self.RemoveObservers('MouseWheelBackwardEvent')
        self.AddObserver('MouseWheelForwardEvent', self.wheel_forward)
        self.AddObserver('MouseWheelBackwardEvent', self.wheel_backward)
        self.panning = False
        self.active_viewer = None
        self.AddObserver('LeftButtonPressEvent',   self.on_left_button_press)
        self.AddObserver('MouseMoveEvent',         self.on_mouse_move)
        self.AddObserver('LeftButtonReleaseEvent', self.on_left_button_release)
        self.AddObserver('EnterEvent', self.on_enter)
        self.AddObserver('LeaveEvent', self.on_leave)

    def set_brush_cursor(self, brush_cursor):
        self.brush_cursor = brush_cursor

    def pick_viewer(self):
        x, y = self.GetInteractor().GetEventPosition()
        w, h = self.GetInteractor().GetRenderWindow().GetSize()
        xn, yn = x / w, y / h
        for sv in self.viewers:
            if sv.contains(xn, yn): return sv
        return None

    def get_world_position(self, viewer):
        """Get world position under mouse cursor - Fixed for all orientations"""
        if not self.enable_editing: return None
        x, y = self.GetInteractor().GetEventPosition()
        renderer = viewer.viewer.GetRenderer()
        coordinate = vtk.vtkCoordinate()
        coordinate.SetCoordinateSystemToDisplay()
        coordinate.SetValue(x, y)
        world_pos = coordinate.GetComputedWorldValue(renderer)
        img_data = viewer.viewer.GetInput()
        spacing, origin = img_data.GetSpacing(), img_data.GetOrigin()
        if viewer.name == 'Axial':
            slice_z = origin[2] + viewer.slice * spacing[2] 
            return (world_pos[0], world_pos[1], slice_z)
        elif viewer.name == 'Coronal':
            slice_y = origin[1] + viewer.slice * spacing[1]
            return (world_pos[0], slice_y, world_pos[2])
        elif viewer.name == 'Sagittal':
            slice_x = origin[0] + viewer.slice * spacing[0]
            return (slice_x, world_pos[1], world_pos[2])
        return world_pos[:3]

    def _apply_label_style(self, idx, selected: bool):
        if idx >= len(self.label_actors): return
        actor = self.label_actors[idx]
        tp = actor.GetTextProperty()
        if selected and self.edit_mode:
            mask_colour = self.editable_masks[idx].color if idx < len(self.editable_masks) else (1.0, 1.0, 0.0)
            tp.SetColor(*mask_colour)
            tp.SetFontSize(24)
        else:
            tp.SetColor(1, 1, 1)
            tp.SetFontSize(16)
        actor.SetTextProperty(tp)

    def update_selection_visuals(self):
        if not self.enable_editing: return
        for sv in self.viewers:
            if hasattr(sv, 'mask_actors') and sv.mask_actors:
                for i, actor in enumerate(sv.mask_actors):
                    actor.GetProperty().SetOpacity(1.0 if i == self.selected_idx and self.edit_mode else 0.9)
        for i in range(len(self.label_actors)):
            self._apply_label_style(i, selected=(i == self.selected_idx))

    def on_enter(self, obj, event):
        if self.edit_mode and self.brush_cursor:
            sv = self.pick_viewer()
            if sv:
                world_pos = self.get_world_position(sv)
                if world_pos:
                    self.brush_cursor.update_cursor_position(sv, world_pos)
                    self.brush_cursor.show_cursor_in_viewer(sv)

    def on_leave(self, obj, event):
        if self.brush_cursor: self.brush_cursor.hide_cursor()

    def on_left_button_press(self, obj, event):
        x, y = self.GetInteractor().GetEventPosition()
        w, h = self.GetInteractor().GetRenderWindow().GetSize()
        xn, yn = x / w, y / h
        if self.enable_editing:
            if self.mode_button:
                pos = self.mode_button.GetPosition()
                if pos[0] <= xn <= pos[0]+0.2 and pos[1] <= yn <= pos[1]+0.05:
                    self.edit_mode = not self.edit_mode
                    self.mode_button.SetInput("Mode: Edit" if self.edit_mode else "Mode: Browse")
                    self.update_selection_visuals()
                    if self.brush_cursor:
                        if self.edit_mode:
                            sv = self.pick_viewer()
                            if sv and (world_pos := self.get_world_position(sv)):
                                self.brush_cursor.update_cursor_position(sv, world_pos)
                                self.brush_cursor.show_cursor_in_viewer(sv)
                        else: self.brush_cursor.hide_cursor()
                    self.GetInteractor().GetRenderWindow().Render()
                    return
            if self.edit_mode and len(self.label_actors) > 0:
                for idx, actor in enumerate(self.label_actors):
                    pos = actor.GetPosition()
                    if pos[0]-0.01 <= xn <= pos[0]+0.35 and pos[1]-0.02 <= yn <= pos[1]+0.06:
                        self.selected_idx = idx
                        self.update_selection_visuals()
                        self.GetInteractor().GetRenderWindow().Render()
                        return
        sv = self.pick_viewer()
        if sv is None: return
        if self.enable_editing:
            ctrl, shift = self.GetInteractor().GetControlKey(), self.GetInteractor().GetShiftKey()
            if ctrl and shift: self.start_pan(sv)
            elif self.edit_mode:
                if world_pos := self.get_world_position(sv):
                    op = 'erase' if ctrl else 'paint'
                    sv.edit_pixel(world_pos, self.selected_idx, op, self.brush_size)
                    self.editing = True
                    self.last_edit_pos = world_pos
            else: self.start_pan(sv)
        else: self.start_pan(sv)

    def start_pan(self, sv):
        self.active_viewer = sv
        self.panning = True
        cam = sv.viewer.GetRenderer().GetActiveCamera()
        cam.ParallelProjectionOn()
        self.SetCurrentRenderer(sv.viewer.GetRenderer())
        self.StartPan()

    def on_mouse_move(self, obj, event):
        if self.panning and self.active_viewer is not None:
            self.SetCurrentRenderer(self.active_viewer.viewer.GetRenderer())
            self.Pan()
            return
            
        sv = self.pick_viewer()
        if not sv:
            if self.brush_cursor: self.brush_cursor.hide_cursor()
            return
            
        if self.edit_mode and (world_pos := self.get_world_position(sv)):
            if self.brush_cursor:
                self.brush_cursor.update_cursor_position(sv, world_pos)
                self.brush_cursor.show_cursor_in_viewer(sv)
            if self.editing:
                op = 'erase' if self.GetInteractor().GetControlKey() else 'paint'
                sv.edit_pixel(world_pos, self.selected_idx, op, self.brush_size)

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
        if not self.enable_editing: return
        key = self.GetInteractor().GetKeySym()
        if key in ('plus', 'equal'):
            self.brush_size = min(self.brush_size + 1, 10)
            if self.brush_cursor: self.brush_cursor.update_cursor_size(self.brush_size)
            self.update_brush_label()
        elif key == 'minus':
            self.brush_size = max(self.brush_size - 1, 1)
            if self.brush_cursor: self.brush_cursor.update_cursor_size(self.brush_size)
            self.update_brush_label()
        elif key == 's': self.save_masks()

    def update_brush_label(self):
        if self.brush_label:
            self.brush_label.SetInput(f"Brush Size: {self.brush_size}")
            self.GetInteractor().GetRenderWindow().Render()

    def save_masks(self):
        if not self.enable_editing: return
        for mask in self.editable_masks:
            if mask.modified: mask.save_mask()
        print("Saved edits to masks")
        if self.save_callback:
            try: self.save_callback()
            except Exception as e: print(f"Error calling save callback: {e}")

    def wheel_forward(self, obj, event):
        sv = self.pick_viewer()
        if not sv: return
        if self.GetInteractor().GetControlKey():
            cam = sv.viewer.GetRenderer().GetActiveCamera()
            cam.ParallelProjectionOn()
            cam.Zoom(1.1)
            sv.viewer.Render()
        else: sv.move(1)
        self.GetInteractor().GetRenderWindow().Render()

    def wheel_backward(self, obj, event):
        sv = self.pick_viewer()
        if not sv: return
        if self.GetInteractor().GetControlKey():
            cam = sv.viewer.GetRenderer().GetActiveCamera()
            cam.ParallelProjectionOn()
            cam.Zoom(0.9)
            sv.viewer.Render()
        else: sv.move(-1)
        self.GetInteractor().GetRenderWindow().Render()


def create_vtk_pipeline(ct_path: str, mask_dir: str = None, render_window=None, enable_editing=False, save_callback=None):
    """
    Create the VTK pipeline for the quad viewer.
    Returns the interactor style that should be attached to the render window's interactor.
    """
    vtk.vtkObject.GlobalWarningDisplayOff()
    if render_window is None:
        raise ValueError("render_window must be provided for Qt integration")

    img = cache_ct(ct_path)
    vtk_img, arr = sitk_to_vtk(img)

    mask_data, editable_masks, legend_labels = [], [], []
    colors = [(1,0,0), (0,1,0), (0,0,1), (1,1,0), (0,1,1), (1,0,1)]

    if mask_dir is not None:
        mask_paths = sorted(glob.glob(os.path.join(mask_dir, '*.nii.gz'))) or \
                     sorted(glob.glob(os.path.join(mask_dir, '*.nii')))
        for idx, mask_path in enumerate(mask_paths):
            label_text = os.path.basename(mask_path).split('.')[0].replace('_', ' ').replace('otsu', '').strip().title()
            legend_labels.append(label_text)
            mask_sitk = sitk.ReadImage(mask_path)
            resampler = sitk.ResampleImageFilter()
            resampler.SetReferenceImage(img)
            resampler.SetInterpolator(sitk.sitkNearestNeighbor)
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
                editable_mask = EditableMask(mask_resampled, mask_path, (r, g, b), cmap)
                editable_masks.append(editable_mask)
                mask_data.append(editable_mask)
            else:
                mask_data.append(cmap)

    dims = (arr.shape[2], arr.shape[1], arr.shape[0])
    render_window.SetNumberOfLayers(2 if legend_labels else 1)
    
    # Create the brush cursor
    brush_cursor = BrushCursor(render_window)

    quads = {
        'Axial':    (0.0, 0.5, 0.5, 1.0),
        'Coronal':  (0.0, 0.0, 0.5, 0.5),
        'Sagittal': (0.5, 0.0, 1.0, 0.5)
    }
    viewers = [SliceViewer(vtk_img, arr, name.lower(), vp, name, render_window, mask_data, dims, enable_editing)
               for name, vp in quads.items()]

    label_actors, mode_btn, brush_label = [], None, None
    if legend_labels:
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
        render_window.AddRenderer(legend_overlay)

        num_masks = len(legend_labels)
        line_spacing = min(0.05, 0.35 / (num_masks + 1)) if num_masks > 0 else 0.05
        font_size = max(14, min(18, int(20 - num_masks))) if num_masks > 0 else 18
        start_x = 0.5 + LEGEND_X_FRACTION_IN_URQ * 0.5

        brush_label = vtkTextActor()
        brush_label.SetInput("Brush Size: 1")
        brush_label.GetTextProperty().SetFontSize(16)
        brush_label.GetTextProperty().SetColor(1, 0.5, 0)
        brush_label.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        brush_label.SetPosition(start_x, 0.9)
        legend_overlay.AddActor(brush_label)

        mode_btn = vtkTextActor()
        mode_btn.SetInput("Mode: Browse")
        mode_btn.GetTextProperty().SetFontSize(20)
        mode_btn.GetTextProperty().SetColor(0, 1, 1)
        mode_btn.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        mode_btn.SetPosition(start_x, 0.85)
        legend_overlay.AddActor(mode_btn)

        for i, lbl in enumerate(legend_labels):
            mask_text = vtkTextActor()
            mask_text.SetInput(lbl)
            mask_text.GetTextProperty().SetFontSize(font_size)
            mask_text.GetTextProperty().SetColor(1, 1, 1)
            mask_text.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            mask_text.SetPosition(start_x, 0.75 - (i * line_spacing))
            legend_overlay.AddActor(mask_text)
            label_actors.append(mask_text)

    interactor_style = QuadStyle(viewers, arr, img.GetOrigin(), img.GetSpacing(),
                                 enable_editing=enable_editing,
                                 label_actors=label_actors if legend_labels else None,
                                 editable_masks=editable_masks if enable_editing else None,
                                 save_callback=save_callback)

    if legend_labels:
        interactor_style.mode_button = mode_btn
        interactor_style.brush_label = brush_label
        
    # Connect the brush cursor to the style
    interactor_style.set_brush_cursor(brush_cursor)

    return interactor_style



def add_masks_to_pipeline(viewers, img, mask_dir, render_window, enable_editing=False, save_callback=None):
    """Add masks to an existing VTK pipeline (legend without coloured squares)."""
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
                editable_mask = EditableMask(mask_resampled, mask_path, (r, g, b), cmap)
                editable_masks.append(editable_mask)
                mask_data.append(editable_mask)
            else:
                mask_data.append(cmap)

        vtk_img, arr = sitk_to_vtk(img)
        dims = (arr.shape[2], arr.shape[1], arr.shape[0])
        for viewer in viewers:
            viewer.add_masks(mask_data, dims, enable_editing=enable_editing)

        render_window.SetNumberOfLayers(2)
        # clear top-right quad
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

        num_masks = len(legend_labels)
        available_height = 0.35
        line_spacing = min(0.05, available_height / (num_masks + 1)) if num_masks > 0 else 0.05
        font_size = max(14, min(18, int(20 - num_masks))) if num_masks > 0 else 18
        start_x = 0.5 + LEGEND_X_FRACTION_IN_URQ * 0.5

        brush_label = vtkTextActor()
        brush_label.SetInput("Brush Size: 1")
        brush_label.GetTextProperty().SetFontSize(16)
        brush_label.GetTextProperty().SetColor(1, 0.5, 0)
        brush_label.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        brush_label.SetPosition(start_x, 0.9)
        legend_overlay.AddActor(brush_label)

        mode_btn = vtkTextActor()
        mode_btn.SetInput("Mode: Browse")
        mode_btn.GetTextProperty().SetFontSize(20)
        mode_btn.GetTextProperty().SetColor(0, 1, 1)
        mode_btn.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        mode_btn.SetPosition(start_x, 0.85)
        legend_overlay.AddActor(mode_btn)

        # Mask labels only
        label_actors = []
        for i, lbl in enumerate(legend_labels):
            pos_y = 0.75 - (i * line_spacing)
            mask_text = vtkTextActor()
            mask_text.SetInput(lbl)
            mask_text.GetTextProperty().SetFontSize(font_size)
            mask_text.GetTextProperty().SetColor(1, 1, 1)
            mask_text.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
            mask_text.SetPosition(start_x, pos_y)
            legend_overlay.AddActor(mask_text)
            label_actors.append(mask_text)

        render_window.Render()
        return True, (editable_masks if enable_editing else None)
    except Exception as e:
        print(f"Error adding masks to pipeline: {e}")
        return False, None


def update_interactor_style_for_editing(interactor_style, label_actors, editable_masks,
                                       mode_button, brush_label, save_callback=None):
    """Enable editing on an existing interactor style (labels only, no squares)."""
    if not hasattr(interactor_style, 'enable_editing'):
        return
    interactor_style.enable_editing = True
    interactor_style.label_actors = label_actors
    interactor_style.editable_masks = editable_masks
    interactor_style.mode_button = mode_button
    interactor_style.brush_label = brush_label
    interactor_style.save_callback = save_callback  # Set save callback
    interactor_style.selected_idx = 0
    interactor_style.edit_mode = False
    interactor_style.brush_size = 1
    interactor_style.editing = False
    interactor_style.last_edit_pos = None
    if not hasattr(interactor_style, '_editing_observers_added'):
        interactor_style.AddObserver('KeyPressEvent', interactor_style.on_key_press)
        interactor_style._editing_observers_added = True
    interactor_style.update_selection_visuals()