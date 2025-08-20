# segmentation_window.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QApplication, QPushButton
from PySide6.QtCore import QTimer, QThread, Signal
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk

# Import the UI form
from frontend_pages.segmentation.ui_segmentation_window import Ui_Form
from seg.embedding import create_vtk_pipeline, add_masks_to_pipeline
from seg.totalseg import load_ct
from classes.objects import SingletonPatient, Context
import os


class SegmentationWorker(QThread):
    """Worker thread for running segmentation"""
    finished = Signal(bool)
    
    def __init__(self, context):
        super().__init__()
        self.context = context
    
    def run(self):
        success = self.context.request_process()
        self.finished.emit(success)


class Segmentation(QWidget):
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
        self.segmentation_progress_msg = None  # Initialize segmentation dialog
        self.mask_addition_msg = None  # Initialize mask dialog

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
        
        # Set up VTK widget
        self.setupVTKWidget()
        
        print("Segmentation window created - waiting for backend paths")

    def setupVTKWidget(self):
        """Replace the placeholder QGraphicsView with VTK widget"""
        parent_layout = self.ui.VTK_display.parent().layout()
        vtk_display_index = parent_layout.indexOf(self.ui.VTK_display)
        
        parent_layout.removeWidget(self.ui.VTK_display)
        self.ui.VTK_display.deleteLater()
        
        self.vtk_widget = QVTKRenderWindowInteractor()
        parent_layout.insertWidget(vtk_display_index, self.vtk_widget, stretch=3)
        self.ui.VTK_display = self.vtk_widget

    def set_context(self, context: Context):
        """Set the context and handle automatic visualization for loaded projects"""
        print("=== set_context called ===")
        self.context = context
        
        # Get paths from singleton
        singleton = SingletonPatient.get_instance()
        patient = singleton.patient
        
        self.ct_dir = patient.CT
        self.mask_dir = patient.seg_masks_dir
        
        print(f"Backend CT path: {self.ct_dir}")
        print(f"Backend mask path: {self.mask_dir}")
        print(f"CT path exists: {os.path.exists(self.ct_dir) if self.ct_dir else False}")
        print(f"Mask path exists: {os.path.exists(self.mask_dir) if self.mask_dir else False}")
        
        # Check what's available and initialize accordingly
        if self.ct_dir and os.path.exists(self.ct_dir):
            # Check if this is a loaded project with existing masks
            has_masks = self.check_for_existing_masks()
            
            if has_masks:
                print("Found existing masks - loading CT with masks...")
                self.show_loading_dialog_with_message("Loading CT data and segmentation masks...")
            else:
                print("No existing masks - loading CT only...")
                self.show_loading_dialog_with_message("Loading CT data...")
            
            # Initialize VTK with delay to allow UI to update
            QTimer.singleShot(100, self.initialize_vtk_with_backend_paths)
        else:
            print("No valid CT path available yet")

    def set_context_with_delayed_transition(self, context: Context, callback):
        """Set context with delayed transition callback"""
        print("=== set_context_with_delayed_transition called ===")
        self.completion_callback = callback
        print(f"Stored completion callback: {callback}")
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

    def show_loading_dialog_with_message(self, message: str):
        """Show loading dialog with custom message"""
        # Close any existing dialog first
        if hasattr(self, 'loading_msg'):
            self.loading_msg.close()
            delattr(self, 'loading_msg')
        
        self.loading_msg = QMessageBox(self)
        self.loading_msg.setWindowTitle("Loading Project")
        self.loading_msg.setText(message)
        self.loading_msg.setStandardButtons(QMessageBox.NoButton)
        self.loading_msg.setModal(False)  # Make non-modal to prevent blocking
        self.loading_msg.show()
        QApplication.processEvents()
        print(f"Loading dialog shown: {message}")

    def show_loading_dialog(self):
        """Show default loading CT dialog"""
        self.show_loading_dialog_with_message("Loading CT data, please wait...")

    def hide_loading_dialog(self):
        """Hide loading CT dialog"""
        if hasattr(self, 'loading_msg'):
            self.loading_msg.close()
            delattr(self, 'loading_msg')
            print("Loading dialog hidden")

    def initialize_vtk_with_backend_paths(self):
        """Initialize VTK pipeline with backend paths and auto-load masks if available"""
        print("=== Initializing VTK with backend paths ===")
        
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
            
            render_window = self.vtk_widget.GetRenderWindow()
            
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
            
            # Create VTK pipeline with off-screen rendering
            print("Creating VTK pipeline (off-screen)...")
            self.interactor_style = create_vtk_pipeline(
                ct_path_to_use, 
                mask_dir_for_display,
                render_window=render_window
            )
            
            if self.interactor_style:
                # Store references
                self.viewers = self.interactor_style.viewers
                self.ct_img = load_ct(ct_path_to_use)
                
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
            self.vtk_widget.Initialize()
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
            rw = self.vtk_widget.GetRenderWindow()
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
        
        # Force close the loading dialog
        self.force_close_loading_dialog()
        
        # Call completion callback if available
        if hasattr(self, 'completion_callback') and self.completion_callback:
            print("Found completion callback - calling it")
            callback = self.completion_callback
            self.completion_callback = None  # Clear it to prevent multiple calls
            # Call with a delay to ensure dialog is fully closed
            QTimer.singleShot(300, callback)
        else:
            print("No completion callback found")
        
        print("Loading process completed")

    def force_close_loading_dialog(self):
        """Force close loading dialog with multiple methods"""
        print("=== Force closing loading dialog ===")
        
        try:
            if hasattr(self, 'loading_msg') and self.loading_msg:
                print("Attempting to close loading dialog...")
                
                # Try multiple methods to close the dialog
                self.loading_msg.setVisible(False)
                self.loading_msg.close()
                self.loading_msg.hide()
                self.loading_msg.reject()
                
                # Process events multiple times
                for i in range(5):
                    QApplication.processEvents()
                
                # Delete the dialog
                self.loading_msg.deleteLater()
                self.loading_msg = None
                
                print("Loading dialog forcefully closed")
                
            else:
                print("No loading dialog to close")
                
        except Exception as e:
            print(f"Error force closing loading dialog: {e}")
        
        # Clean up attribute
        if hasattr(self, 'loading_msg'):
            try:
                delattr(self, 'loading_msg')
            except:
                pass
        
        # Force additional UI updates
        for i in range(3):
            QTimer.singleShot(50 * (i + 1), lambda: QApplication.processEvents())

    def force_close_segmentation_dialog(self):
        """Force close segmentation progress dialog"""
        print("=== Force closing segmentation dialog ===")
        
        try:
            if hasattr(self, 'segmentation_progress_msg') and self.segmentation_progress_msg:
                print("Attempting to close segmentation progress dialog...")
                
                # Try multiple methods to close the dialog
                self.segmentation_progress_msg.setVisible(False)
                self.segmentation_progress_msg.close()
                self.segmentation_progress_msg.hide()
                self.segmentation_progress_msg.reject()
                
                # Process events multiple times
                for i in range(5):
                    QApplication.processEvents()
                
                # Delete the dialog
                self.segmentation_progress_msg.deleteLater()
                self.segmentation_progress_msg = None
                
                print("Segmentation progress dialog forcefully closed")
                
            else:
                print("No segmentation progress dialog to close")
                
        except Exception as e:
            print(f"Error force closing segmentation dialog: {e}")
        
        # Clean up attribute
        if hasattr(self, 'segmentation_progress_msg'):
            try:
                delattr(self, 'segmentation_progress_msg')
            except:
                pass
        
        # Force additional UI updates
        for i in range(3):
            QTimer.singleShot(50 * (i + 1), lambda: QApplication.processEvents())

    def force_close_mask_dialog(self):
        """Force close mask addition dialog"""
        print("=== Force closing mask addition dialog ===")
        
        try:
            if hasattr(self, 'mask_addition_msg') and self.mask_addition_msg:
                print("Attempting to close mask addition dialog...")
                
                # Try multiple methods to close the dialog
                self.mask_addition_msg.setVisible(False)
                self.mask_addition_msg.close()
                self.mask_addition_msg.hide()
                self.mask_addition_msg.reject()
                
                # Process events multiple times
                for i in range(5):
                    QApplication.processEvents()
                
                # Delete the dialog
                self.mask_addition_msg.deleteLater()
                self.mask_addition_msg = None
                
                print("Mask addition dialog forcefully closed")
                
            else:
                print("No mask addition dialog to close")
                
        except Exception as e:
            print(f"Error force closing mask addition dialog: {e}")
        
        # Clean up attribute
        if hasattr(self, 'mask_addition_msg'):
            try:
                delattr(self, 'mask_addition_msg')
            except:
                pass
        
        # Force additional UI updates
        for i in range(3):
            QTimer.singleShot(50 * (i + 1), lambda: QApplication.processEvents())

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
        """Run segmentation process"""
        if not self.context:
            self.show_error("No context available")
            return
        
        if not self.ct_dir or not os.path.exists(self.ct_dir):
            self.show_error(f"Invalid CT directory: {self.ct_dir}")
            return
        
        # Show progress dialog
        self.segmentation_progress_msg = QMessageBox(self)
        self.segmentation_progress_msg.setWindowTitle("Segmentation Progress")
        self.segmentation_progress_msg.setText("Running segmentation...")
        self.segmentation_progress_msg.setStandardButtons(QMessageBox.NoButton)
        self.segmentation_progress_msg.setModal(True)
        self.segmentation_progress_msg.show()
        QApplication.processEvents()
        
        # Disable segmentation button and VTK widget interaction
        if hasattr(self.ui, 'segment_btn'):
            self.ui.segment_btn.setEnabled(False)
        
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.setEnabled(False)
        
        # Start segmentation worker
        self.segmentation_worker = SegmentationWorker(self.context)
        self.segmentation_worker.finished.connect(self.on_segmentation_finished)
        self.segmentation_worker.start()

    def on_segmentation_finished(self, success):
        """Handle segmentation completion"""
        print(f"=== Segmentation finished: {success} ===")
        
        # Force close progress dialog
        self.force_close_segmentation_dialog()
        
        # Re-enable segmentation button and VTK widget
        if hasattr(self.ui, 'segment_btn'):
            self.ui.segment_btn.setEnabled(True)
        
        if hasattr(self, 'vtk_widget'):
            self.vtk_widget.setEnabled(True)
        
        if success:
            self.show_info("Segmentation completed successfully!")
            
            # Add masks to visualization
            if self.mask_dir and os.path.exists(self.mask_dir):
                print("Adding masks to visualization...")
                
                # Show brief loading message for mask overlay
                self.mask_addition_msg = QMessageBox(self)
                self.mask_addition_msg.setWindowTitle("Adding Masks")
                self.mask_addition_msg.setText("Adding segmentation masks to visualization...")
                self.mask_addition_msg.setStandardButtons(QMessageBox.NoButton)
                self.mask_addition_msg.setModal(False)
                self.mask_addition_msg.show()
                QApplication.processEvents()
                
                # Add masks with delay to allow UI update
                QTimer.singleShot(100, self._add_masks_and_close_dialog)
            else:
                print("No mask directory available")
        else:
            self.show_error("Segmentation failed. Check console for details.")

    def _add_masks_and_close_dialog(self):
        """Add masks and close the dialog"""
        try:
            if hasattr(self, 'mask_addition_msg'):
                success = self.add_masks(self.mask_dir)
                
                # Force close the mask addition dialog
                self.force_close_mask_dialog()
                
                if success:
                    print("Masks added successfully!")
                else:
                    print("Failed to add masks")
            else:
                print("No mask addition dialog to close")
                
        except Exception as e:
            print(f"Error adding masks: {e}")
            # Force close dialog even if there was an error
            self.force_close_mask_dialog()

    def add_masks(self, mask_dir: str):
        """Add masks to the existing CT visualization"""
        if not self.viewers or not self.ct_img:
            print("Cannot add masks - VTK pipeline not initialized")
            return False
        
        try:
            render_window = self.vtk_widget.GetRenderWindow()
            success = add_masks_to_pipeline(self.viewers, self.ct_img, mask_dir, render_window)
            
            if success:
                print(f"Masks added successfully from: {mask_dir}")
            
            return success
            
        except Exception as e:
            print(f"Error adding masks: {e}")
            return False

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
                rw = self.vtk_widget.GetRenderWindow()
                rw.Render()
                print("VTK rendering completed")
                    
        except Exception as e:
            print(f"Error during VTK render: {e}")

    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        # Don't auto-initialize here anymore - handled by set_context

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if hasattr(self, 'vtk_widget') and self._vtk_initialized:
            QTimer.singleShot(10, lambda: self.vtk_widget.GetRenderWindow().Render())