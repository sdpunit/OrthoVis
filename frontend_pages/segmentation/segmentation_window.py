# segmentation_window.py

from PySide6.QtWidgets import QWidget, QMessageBox, QCheckBox
from PySide6.QtCore import QTimer, QThread, Signal

# Import the UI form
from frontend_pages.segmentation.ui_segmentation_window import Ui_Form
from seg.embedding import create_vtk_pipeline, add_masks_to_pipeline, update_interactor_style_for_editing
from seg.totalseg import load_ct, get_all_available_bones
from classes.objects import SingletonPatient, Context
from classes.utils import ProgressDialogMixin
import os


class SegmentationWorker(QThread):
    """Worker thread for running segmentation"""
    finished = Signal(bool)
    
    def __init__(self, context, custom_roi):
        super().__init__()
        self.context = context
        self.custom_roi = custom_roi
    
    def run(self):
        # Pass custom ROI to the context for processing
        success = self.context.request_process(self.custom_roi)
        self.finished.emit(success)


class Segmentation(QWidget, ProgressDialogMixin):
    proceed_to_calibration_signal = Signal()
    
    def __init__(self, ct_dir: str = None, mask_dir: str = None):
        super().__init__()
        instance = SingletonPatient.get_instance()
        self.ct_dir = instance.patient.CT
        self.mask_dir = instance.patient.seg_masks_dir
        self._vtk_initialized = False
        
        # Initialize paths as None - will be set from backend
        self.ct_dir = None
        self.mask_dir = None
        
        self.interactor_style = None
        self.viewers = None
        self.ct_img = None
        self.context = None
        self.completion_callback = None  # Initialize callback
        self.progress_dialog = None  # Single dialog for all progress messages

        # Editing-related attributes
        self.editing_enabled = False
        self.editable_masks = None
        self.label_actors = None
        self.mode_button = None
        self.brush_label = None

        # ROI selection attributes
        self.roi_checkboxes = {}
        self.selected_roi = []

        # Set up UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Set the title
        self.ui.titlebar.ui.title.setText("CT Segmentation")

        # Highlight the segmentation button in sidebar
        self.ui.sidebar.ui.segmentation.setStyleSheet(
            """
            QPushButton { 
                color: white; 
                background-color: #6f8ab7; 
                border: none; 
                padding: 10px 25px;  
                text-align: center;}
            """
        )

        # Connect the segmentation button
        if hasattr(self.ui, 'segment_btn'):
            self.ui.segment_btn.clicked.connect(self.run_segmentation)
            print("Connected segmentation button: segment_btn")

        # Connect editing mode buttons
        if hasattr(self.ui, 'proceed_calibration_btn'):
            self.ui.proceed_calibration_btn.clicked.connect(self.proceed_to_calibration)
            print("Connected proceed to calibration button")
        
        # Initialize ROI selection
        self.setup_roi_selection()
        
        # Set initial shortcuts display (browse mode only)
        self.update_shortcuts_display(False)
        
        print("Segmentation window created - waiting for backend paths")

    def setup_roi_selection(self):
        """Set up the ROI selection checkboxes"""
        try:
            # Get all available bones and sort alphabetically
            all_bones = sorted(get_all_available_bones())  # Sort alphabetically
            
            # Clear existing checkboxes
            for checkbox in self.roi_checkboxes.values():
                checkbox.setParent(None)
            self.roi_checkboxes.clear()
            
            # Create checkboxes for each bone
            for bone in all_bones:
                checkbox = QCheckBox(bone.replace('_', ' ').title())
                checkbox.setObjectName(f"roi_checkbox_{bone}")
                checkbox.setStyleSheet("""
                    QCheckBox {
                        font: 10pt "Segoe UI";
                        padding: 2px;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                    }
                """)
                checkbox.stateChanged.connect(lambda state, b=bone: self.on_roi_checkbox_changed(b, state))
                
                self.roi_checkboxes[bone] = checkbox
                self.ui.roi_content_layout.addWidget(checkbox)
            
            print(f"Created {len(all_bones)} ROI checkboxes (alphabetically sorted)")
            
        except Exception as e:
            print(f"Error setting up ROI selection: {e}")

    def on_roi_checkbox_changed(self, bone_name, state):
        """Handle ROI checkbox state changes"""
        if state == 2:  # Checked
            if bone_name not in self.selected_roi:
                self.selected_roi.append(bone_name)
        else:  # Unchecked
            if bone_name in self.selected_roi:
                self.selected_roi.remove(bone_name)
        
        print(f"Selected ROI updated: {self.selected_roi}")

    def set_editing_mode(self, editing_enabled: bool):
        """Toggle between browse and editing modes"""
        self.editing_enabled = editing_enabled
        
        if editing_enabled:
            # Hide ROI selection and segment button, show editing buttons
            self.ui.roi_selection_widget.hide()
            self.ui.segment_btn.hide()  # Hide segment button in editing mode
            self.ui.editing_buttons_widget.show()
            # Update shortcuts to show editing mode
            self.update_shortcuts_display(True)
        else:
            # Show ROI selection and segment button, hide editing buttons
            self.ui.roi_selection_widget.show()
            self.ui.segment_btn.show()  # Show segment button in browse mode
            self.ui.editing_buttons_widget.hide()
            # Update shortcuts to show browse mode only
            self.update_shortcuts_display(False)
        
        print(f"Editing mode set to: {editing_enabled}")

    def update_shortcuts_display(self, show_editing: bool):
        """Update the shortcuts display based on current mode"""
        if show_editing:
            # Show both browse and editing shortcuts
            shortcuts_html = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
            <html><head><meta name="qrichtext" content="1" /><meta charset="utf-8" /><style type="text/css">
            p, li { white-space: pre-wrap; }
            hr { height: 1px; border-width: 0; }
            li.unchecked::marker { content: "\\2610"; }
            li.checked::marker { content: "\\2612"; }
            .shortcut-title { 
                font-weight: bold; 
                font-size: 12pt; 
                color: #000000; 
                margin-bottom: 15px; 
                text-align: center;
            }
            .shortcut-section { 
                font-weight: bold; 
                font-size: 11pt; 
                color: #000000; 
                margin-top: 15px; 
                margin-bottom: 8px; 
                text-decoration: underline;
            }
            .shortcut-table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
            }
            .shortcut-table td {
                padding: 2px 0px;
                vertical-align: top;
            }
            .shortcut-action { 
                font-weight: bold; 
                color: #000000; 
                width: 60%;
                text-align: left;
            }
            .shortcut-control { 
                color: #666666; 
                width: 40%;
                text-align: left;
                padding-left: 5px;
            }
            </style></head><body style="font-family:'Segoe UI'; font-size:10pt; font-weight:400; font-style:normal;">

            <p class="shortcut-title">SHORTCUTS</p>

            <p class="shortcut-section">Browse Mode</p>
            <table class="shortcut-table">
                <tr>
                    <td class="shortcut-action">View Slices</td>
                    <td class="shortcut-control">Scroll</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Zoom</td>
                    <td class="shortcut-control">Ctrl + Scroll</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Pan</td>
                    <td class="shortcut-control">Ctrl + Shift + Drag</td>
                </tr>
            </table>

            <p class="shortcut-section">Edit Mode</p>
            <table class="shortcut-table">
                <tr>
                    <td class="shortcut-action">View Slices</td>
                    <td class="shortcut-control">Scroll</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Zoom</td>
                    <td class="shortcut-control">Ctrl + Scroll</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Pan</td>
                    <td class="shortcut-control">Ctrl + Shift + Drag</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Paint</td>
                    <td class="shortcut-control">Drag</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Erase</td>
                    <td class="shortcut-control">Ctrl + Drag</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Brush Size</td>
                    <td class="shortcut-control">+/-</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Save Edits</td>
                    <td class="shortcut-control">S</td>
                </tr>
            </table>

            </body></html>"""
        else:
            # Show only browse mode shortcuts
            shortcuts_html = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
            <html><head><meta name="qrichtext" content="1" /><meta charset="utf-8" /><style type="text/css">
            p, li { white-space: pre-wrap; }
            hr { height: 1px; border-width: 0; }
            li.unchecked::marker { content: "\\2610"; }
            li.checked::marker { content: "\\2612"; }
            .shortcut-title { 
                font-weight: bold; 
                font-size: 12pt; 
                color: #000000; 
                margin-bottom: 15px; 
                text-align: center;
            }
            .shortcut-section { 
                font-weight: bold; 
                font-size: 11pt; 
                color: #000000; 
                margin-top: 15px; 
                margin-bottom: 8px; 
                text-decoration: underline;
            }
            .shortcut-table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
            }
            .shortcut-table td {
                padding: 2px 0px;
                vertical-align: top;
            }
            .shortcut-action { 
                font-weight: bold; 
                color: #000000; 
                width: 60%;
                text-align: left;
            }
            .shortcut-control { 
                color: #666666; 
                width: 40%;
                text-align: left;
                padding-left: 5px;
            }
            </style></head><body style="font-family:'Segoe UI'; font-size:10pt; font-weight:400; font-style:normal;">

            <p class="shortcut-title">SHORTCUTS</p>

            <p class="shortcut-section">Browse Mode</p>
            <table class="shortcut-table">
                <tr>
                    <td class="shortcut-action">View Slices</td>
                    <td class="shortcut-control">Scroll</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Zoom</td>
                    <td class="shortcut-control">Ctrl + Scroll</td>
                </tr>
                <tr>
                    <td class="shortcut-action">Pan</td>
                    <td class="shortcut-control">Ctrl + Shift + Drag</td>
                </tr>
            </table>

            </body></html>"""
        
        self.ui.textBrowser.setHtml(shortcuts_html)

    def set_context(self, context: Context):
        """Set the context and handle automatic visualization for loaded projects"""
        print("=== set_context called ===")
        self.context = context
        
        # Get paths from singleton
        singleton = SingletonPatient.get_instance()
        patient = singleton.patient
        
        self.ct_dir = patient.CT
        self.mask_dir = patient.seg_masks_dir
        
        # Update the project name in the UI
        if patient.name:
            self.ui.label_2.setText(f"   {patient.name}")  # Add spaces for horizontal spacing
        
        print(f"Backend CT path: {self.ct_dir}")
        print(f"Backend mask path: {self.mask_dir}")
        print(f"CT path exists: {os.path.exists(self.ct_dir) if self.ct_dir else False}")
        print(f"Mask path exists: {os.path.exists(self.mask_dir) if self.mask_dir else False}")
        
        # Check what's available and initialize accordingly
        if self.ct_dir and os.path.exists(self.ct_dir):
            # Check if this is a loaded project with existing masks
            has_masks = self.check_for_existing_masks()
            
            if has_masks:
                print("Found existing masks - loading CT with masks in EDIT mode...")
                self.set_editing_mode(True)  # Enable editing when masks exist
                self.show_progress_dialog("Loading Project", "Loading CT data and segmentation masks in EDIT mode...")
            else:
                print("No existing masks - loading CT only in BROWSE mode...")
                self.set_editing_mode(False)  # Browse-only when no masks
                self.show_progress_dialog("Loading Project", "Loading CT data in BROWSE mode...")
            
            # Initialize VTK with delay to allow UI to update
            QTimer.singleShot(100, self.initialize_vtk_with_backend_paths)
        else:
            print("No valid CT path available yet")

    def set_context_with_delayed_transition(self, context: Context, callback):
        """Set context with delayed transition callback"""
        print("=== set_context_with_delayed_transition called ===")
        self.completion_callback = callback
        print(f"Stored completion callback: {callback}")
        
        # Get patient name and update UI
        singleton = SingletonPatient.get_instance()
        patient = singleton.patient
        if patient.name:
            self.ui.label_2.setText(f"    {patient.name}")  # Add spaces for horizontal spacing
    
        self.set_context(context)

    def check_for_existing_masks(self) -> bool:
        """Check if segmentation masks already exist for this project"""
        if not self.mask_dir or not os.path.exists(self.mask_dir):
            return False
        
        try:
            mask_files = [f for f in os.listdir(self.mask_dir) 
                         if f.endswith(('.nii.gz', '.nii'))]
            
            if mask_files:
                print(f"Found {len(mask_files)} existing mask files:")
                for mask_file in mask_files:
                    print(f"  - {mask_file}")
                return True
            else:
                print("Mask directory exists but is empty")
                return False
                
        except Exception as e:
            print(f"Error checking for existing masks: {e}")
            return False

    def initialize_vtk_with_backend_paths(self):
        """Initialize VTK pipeline with backend paths and auto-load masks if available"""
        print("=== Initializing VTK with backend paths ===")
        print(f"Editing enabled: {self.editing_enabled}")
        
        if not self.ct_dir or not os.path.exists(self.ct_dir):
            print(f"ERROR: Invalid CT directory: {self.ct_dir}")
            self.complete_loading_process()
            return
        
        try:
            # Find DICOM directory
            ct_path_to_use = self.find_dicom_directory(self.ct_dir)
            if not ct_path_to_use:
                print(f"ERROR: No DICOM files found in: {self.ct_dir}")
                self.complete_loading_process()
                return
            
            print(f"Using DICOM directory: {ct_path_to_use}")
            
            # Set up VTK with OFF-SCREEN rendering during initialization
            import vtk
            vtk.vtkObject.GlobalWarningDisplayOff()
            
            render_window = self.ui.VTK_display.GetRenderWindow()
            
            # CRITICAL: Turn OFF on-screen rendering during loading
            render_window.SetOffScreenRendering(True)
            render_window.SetMultiSamples(0)
            
            # Clear existing renderers
            render_window.GetRenderers().RemoveAllItems()
            
            # Check for masks - include existing masks from loaded projects
            mask_dir_for_display = None
            if self.mask_dir and os.path.exists(self.mask_dir):
                mask_files = [f for f in os.listdir(self.mask_dir) 
                             if f.endswith(('.nii.gz', '.nii'))]
                if mask_files:
                    mask_dir_for_display = self.mask_dir
                    print(f"Will display {len(mask_files)} existing mask files")
            
            # Create VTK pipeline with off-screen rendering and editing capability
            print(f"Creating VTK pipeline (off-screen) with editing={self.editing_enabled}...")
            self.interactor_style = create_vtk_pipeline(
                ct_path_to_use, 
                mask_dir_for_display,
                render_window=render_window,
                enable_editing=self.editing_enabled,  # Enable editing when appropriate
                save_callback=self.on_save_shortcut  # Pass save callback for 'S' key
            )
            
            if self.interactor_style:
                # Store references
                self.viewers = self.interactor_style.viewers
                self.ct_img = load_ct(ct_path_to_use)
                
                # Store editing-related references if editing is enabled
                if self.editing_enabled and hasattr(self.interactor_style, 'editable_masks'):
                    self.editable_masks = self.interactor_style.editable_masks
                    self.label_actors = getattr(self.interactor_style, 'label_actors', None)
                    self.mode_button = getattr(self.interactor_style, 'mode_button', None)
                    self.brush_label = getattr(self.interactor_style, 'brush_label', None)
                    print(f"Editing features initialized: {len(self.editable_masks) if self.editable_masks else 0} editable masks")
                
                # Set interactor style
                interactor = render_window.GetInteractor()
                interactor.SetInteractorStyle(self.interactor_style)
                
                # Now turn ON on-screen rendering and initialize
                render_window.SetOffScreenRendering(False)
                
                # Initialize VTK and complete after delay
                QTimer.singleShot(50, self._initialize_vtk_final)
                
                print("VTK pipeline created successfully!")
                if mask_dir_for_display:
                    print(f"Existing masks loaded from: {mask_dir_for_display}")
                    if self.editing_enabled:
                        print("EDITING MODE: You can now edit masks using mouse and keyboard shortcuts")
            else:
                print("ERROR: Failed to create VTK pipeline")
                self.complete_loading_process()
                
        except Exception as e:
            print(f"Error initializing VTK: {e}")
            import traceback
            traceback.print_exc()
            self.complete_loading_process()

    def _initialize_vtk_final(self):
        """Final VTK initialization and rendering"""
        try:
            print("Final VTK initialization...")
            self.ui.VTK_display.Initialize()
            self._vtk_initialized = True
            
            # Render and then complete loading after successful render
            QTimer.singleShot(100, self._render_and_complete)
            
        except Exception as e:
            print(f"Error in final VTK initialization: {e}")
            # Even if VTK init fails, complete the loading process
            QTimer.singleShot(100, self.complete_loading_process)

    def _render_and_complete(self):
        """Render VTK and complete loading process"""
        try:
            print("Rendering VTK...")
            rw = self.ui.VTK_display.GetRenderWindow()
            rw.Render()
            print("VTK rendering completed")
            
            # Complete loading process after successful render
            QTimer.singleShot(200, self.complete_loading_process)
            
        except Exception as e:
            print(f"Error during VTK render: {e}")
            # Complete loading even if render fails
            QTimer.singleShot(100, self.complete_loading_process)

    def complete_loading_process(self):
        """Complete the loading process - close dialog and trigger page transition"""
        print("=== Completing loading process ===")
        
        # Close the loading dialog
        self.close_progress_dialog()
        
        # Call completion callback if available
        if hasattr(self, 'completion_callback') and self.completion_callback:
            print("Found completion callback - calling it")
            callback = self.completion_callback
            self.completion_callback = None  # Clear it to prevent multiple calls
            # Call with a delay to ensure dialog is fully closed
            QTimer.singleShot(100, callback)
        else:
            print("No completion callback found")
        
        print("Loading process completed")

    def find_dicom_directory(self, base_dir):
        """Find directory containing DICOM files"""
        if self.contains_dicom_files(base_dir):
            return base_dir
        
        try:
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if os.path.isdir(item_path) and self.contains_dicom_files(item_path):
                    return item_path
        except Exception as e:
            print(f"Error searching for DICOM files: {e}")
        
        return None

    def contains_dicom_files(self, directory):
        """Check if directory contains DICOM files"""
        try:
            files = os.listdir(directory)
            dicom_files = [f for f in files if '.' not in f or f.endswith('.dcm')]
            return len(dicom_files) > 0
        except:
            return False

    def run_segmentation(self):
        """Run segmentation process with custom ROI"""
        if not self.context:
            self.show_error("No context available")
            return
        
        if not self.ct_dir or not os.path.exists(self.ct_dir):
            self.show_error(f"Invalid CT directory: {self.ct_dir}")
            return
        
        # Check if ROI is selected
        if not self.selected_roi or len(self.selected_roi) == 0:
            self.show_error("Please select at least one bone from the ROI list before running segmentation.")
            return
        
        print(f"Running segmentation with custom ROI: {self.selected_roi}")
        
        # Show progress dialog
        self.show_progress_dialog("Segmentation Progress", f"Running segmentation for {len(self.selected_roi)} selected bones...")
        
        # Disable segmentation button and VTK widget interaction
        if hasattr(self.ui, 'segment_btn'):
            self.ui.segment_btn.setEnabled(False)
        
        if hasattr(self, 'vtk_widget'):
            self.ui.VTK_display.setEnabled(False)
        
        # Start segmentation worker with custom ROI
        self.segmentation_worker = SegmentationWorker(self.context, self.selected_roi)
        self.segmentation_worker.finished.connect(self.on_segmentation_finished)
        self.segmentation_worker.start()

    def on_segmentation_finished(self, success):
        """Handle segmentation completion"""
        print(f"=== Segmentation finished: {success} ===")
        
        # Close progress dialog
        self.close_progress_dialog()
        
        # Re-enable segmentation button and VTK widget
        if hasattr(self.ui, 'segment_btn'):
            self.ui.segment_btn.setEnabled(True)
        
        if hasattr(self, 'vtk_widget'):
            self.ui.VTK_display.setEnabled(True)
        
        if success:
            self.show_info("Segmentation completed successfully!")
            
            # Switch to editing mode and add masks to visualization WITH EDITING ENABLED
            self.set_editing_mode(True)
            
            if self.mask_dir and os.path.exists(self.mask_dir):                
                # Show brief loading message for mask overlay
                self.show_progress_dialog("Adding Masks", "Overlaying segmentation masks in EDIT mode...")
                
                # Add masks with delay to allow UI update
                QTimer.singleShot(100, self._add_masks_and_close_dialog)
            else:
                print("No mask directory available")
        else:
            self.show_error("Segmentation failed. Check console for details.")

    def _add_masks_and_close_dialog(self):
        """Add masks with editing enabled and close the dialog"""
        try:
            # Enable editing mode since we now have masks
            success = self.add_masks(self.mask_dir, enable_editing=True)
            
            # Close the progress dialog
            self.close_progress_dialog()
            
            if success:
                print("Masks added successfully in EDIT mode!")
                print("=== EDITING MODE NOW ACTIVE ===")
            else:
                print("Failed to add masks")
                
        except Exception as e:
            print(f"Error adding masks: {e}")
            # Close dialog even if there was an error
            self.close_progress_dialog()

    def add_masks(self, mask_dir: str, enable_editing: bool = False):
        """Add masks to the existing CT visualization"""
        if not self.viewers or not self.ct_img:
            print("Cannot add masks - VTK pipeline not initialized")
            return False
        
        try:
            render_window = self.ui.VTK_display.GetRenderWindow()
            
            # Use enhanced add_masks_to_pipeline with editing support
            success, editable_masks = add_masks_to_pipeline(
                self.viewers, 
                self.ct_img, 
                mask_dir, 
                render_window,
                enable_editing=enable_editing,  # Enable editing features
                save_callback=self.on_save_shortcut  # Pass save callback for 'S' key
            )
            
            if success:
                print(f"Masks added successfully from: {mask_dir}")
                
                # If editing was enabled, update interactor style and store references
                if enable_editing and editable_masks:
                    print("Updating interactor style for editing...")
                    
                    # Store editing references
                    self.editable_masks = editable_masks
                    self.editing_enabled = True
                    
                    # Find the UI elements that were created
                    render_window = self.ui.VTK_display.GetRenderWindow()
                    renderers = render_window.GetRenderers()
                    
                    # Look for the legend overlay renderer (layer 1)
                    legend_renderer = None
                    renderers.InitTraversal()
                    for i in range(renderers.GetNumberOfItems()):
                        renderer = renderers.GetNextItem()
                        if hasattr(renderer, 'GetLayer') and renderer.GetLayer() == 1:
                            legend_renderer = renderer
                            break
                    
                    if legend_renderer:
                        # Extract UI elements from the renderer
                        self.label_actors = []
                        self.mode_button = None
                        self.brush_label = None
                        
                        actors = legend_renderer.GetActors2D()
                        actors.InitTraversal()
                        for i in range(actors.GetNumberOfItems()):
                            actor = actors.GetNextItem()
                            if hasattr(actor, 'GetInput'):
                                input_text = actor.GetInput()
                                if "Mode:" in input_text:
                                    self.mode_button = actor
                                elif "Brush Size:" in input_text:
                                    self.brush_label = actor
                                elif input_text not in ["Edit Mode:\nDrag: Paint\nCtrl+Drag: Erase\nCtrl+Shift+Left: Pan\n+/-: Brush size\nS: Save"]:
                                    # This is likely a mask label
                                    self.label_actors.append(actor)
                        
                        # Update the interactor style with editing features using the helper function
                        update_interactor_style_for_editing(
                            self.interactor_style,
                            self.label_actors,
                            self.editable_masks,
                            self.mode_button,
                            self.brush_label,
                            self.on_save_shortcut
                        )
                        
                        print(f"Editing enabled with {len(self.editable_masks)} editable masks")
                    else:
                        print("Warning: Could not find legend renderer for UI elements")
            
            return success
            
        except Exception as e:
            print(f"Error adding masks: {e}")
            import traceback
            traceback.print_exc()
            return False

    def on_save_shortcut(self):
        """Callback for 'S' key shortcut - shows GUI message"""
        message = "Saved edits to masks"
        print(message)
        self.show_info(message)

    def save_edited_masks(self):
        self.context.request_save(self)
        # if not self.editing_enabled or not self.editable_masks:
        #     print("No editable masks available")
        #     self.show_info("No editable masks available")
        #     return False
        
        # try:
        #     saved_count = 0
        #     for mask in self.editable_masks:
        #         if hasattr(mask, 'modified') and mask.modified:
        #             mask.save_mask()
        #             saved_count += 1
            
        #     # Always show the message, even if no masks were modified
        #     message = "Saved edits to masks"
        #     print(message)
        #     self.show_info(message)
            
        #     return True
                
        # except Exception as e:
        #     print(f"Error saving masks: {e}")
        #     self.show_error(f"Error saving masks: {e}")
        #     return False

    def proceed_to_calibration(self):
        """Proceed to calibration step"""
        # First save any edited masks
        self.save_edited_masks()
        
        # Transition to calibration page
        self.proceed_to_calibration_signal.emit()

    def refresh_visualization(self):
        """Refresh the VTK visualization - called when switching to this page"""
        print("=== refresh_visualization called ===")
        
        # Get current paths from backend
        singleton = SingletonPatient.get_instance()
        patient = singleton.patient
        
        print(f"Current backend CT path: {patient.CT}")
        print(f"Current widget CT path: {self.ct_dir}")
        
        # If we don't have VTK initialized yet and we have valid paths, initialize now
        if not self._vtk_initialized and patient.CT and os.path.exists(patient.CT):
            print("VTK not initialized - setting context to initialize...")
            # This will be called by set_context, so no need to duplicate
        elif self._vtk_initialized:
            print("VTK already initialized - just rendering...")
            QTimer.singleShot(50, self._render_vtk)
        else:
            print("No valid CT data available for visualization")

    def show_error(self, message):
        """Show error message dialog"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.exec()

    def show_info(self, message):
        """Show info message dialog"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Information")
        msg.setText(message)
        msg.exec()

    def _render_vtk(self):
        """Perform VTK render"""
        print("=== _render_vtk called ===")
        try:
            if hasattr(self, 'vtk_widget'):
                rw = self.ui.VTK_display.GetRenderWindow()
                rw.Render()
                print("VTK rendering completed")
                    
        except Exception as e:
            print(f"Error during VTK render: {e}")

    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        # Initialization handled by set_context

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if hasattr(self, 'vtk_widget') and self._vtk_initialized:
            QTimer.singleShot(10, lambda: self.ui.VTK_display.GetRenderWindow().Render())