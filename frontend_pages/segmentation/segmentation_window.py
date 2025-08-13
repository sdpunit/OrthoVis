# segmentation_window.py

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QTimer
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# Import the UI form (like project_setup does)
from frontend_pages.segmentation.ui_segmentation_window import Ui_Form
from seg.embedding import create_vtk_pipeline, add_masks_to_pipeline
from seg.totalseg import load_ct

class Segmentation(QWidget):
    def __init__(self, ct_dir: str, mask_dir: str = None):
        super().__init__()
        self._vtk_initialized = False
        self.ct_dir = ct_dir
        self.mask_dir = mask_dir
        self.interactor_style = None
        self.viewers = None
        self.ct_img = None  # Store CT image for later mask addition

        # Set up UI using the form (like project_setup does)
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

        # Replace the VTK_display (QGraphicsView) with our VTK widget
        self.setupVTKWidget()
        
        # Initialize VTK after UI is set up
        if create_vtk_pipeline is not None:
            self.setupVTK()

    def setupVTKWidget(self):
        """Replace the placeholder QGraphicsView with our VTK widget"""
        # Get the parent layout of VTK_display (which should be horizontalLayout_2)
        parent_layout = self.ui.VTK_display.parent().layout()
        
        # Get the current position of VTK_display in the layout
        vtk_display_index = parent_layout.indexOf(self.ui.VTK_display)
        
        # Remove the existing VTK_display widget
        parent_layout.removeWidget(self.ui.VTK_display)
        self.ui.VTK_display.deleteLater()
        
        # Create our VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor()
        
        # Insert the VTK widget at the same position as the old VTK_display
        parent_layout.insertWidget(vtk_display_index, self.vtk_widget)
        
        # Store reference for easy access
        self.ui.VTK_display = self.vtk_widget

    def setupVTK(self):
        """Set up the VTK pipeline"""
        try:
            # Set VTK to be more defensive about window creation
            import vtk
            vtk.vtkObject.GlobalWarningDisplayOff()
            
            # Get the render window from the Qt widget
            render_window = self.vtk_widget.GetRenderWindow()
            
            # Configure render window before creating pipeline
            render_window.SetMultiSamples(0)  # Disable anti-aliasing
            render_window.SetOffScreenRendering(False)  # Ensure on-screen rendering
            
            # Create the VTK pipeline using our extracted function
            # Pass mask_dir (which can be None) to the pipeline
            self.interactor_style = create_vtk_pipeline(
                self.ct_dir, 
                self.mask_dir,  # This can be None
                render_window=render_window
            )
            
            # Store reference to viewers for potential mask addition later
            self.viewers = self.interactor_style.viewers
            
            # Load and store CT image for potential mask addition later
            if load_ct is not None:
                self.ct_img = load_ct(self.ct_dir)
            
            # Get the interactor and set our custom style
            interactor = render_window.GetInteractor()
            interactor.SetInteractorStyle(self.interactor_style)
            
            print(f"VTK pipeline created successfully for CT: {self.ct_dir}")
            if self.mask_dir:
                print(f"Masks directory: {self.mask_dir}")
            else:
                print("No masks directory provided - CT only visualization")
            
        except Exception as e:
            print(f"Error setting up VTK pipeline: {e}")
            import traceback
            traceback.print_exc()

    def add_masks(self, mask_dir: str):
        """
        Add masks to the existing CT visualization.
        This can be called after segmentation is complete.
        
        Args:
            mask_dir: Directory containing mask files
        
        Returns:
            Boolean indicating success
        """
        if not self.viewers or not self.ct_img or add_masks_to_pipeline is None:
            print("Cannot add masks - VTK pipeline not properly initialized")
            return False
        
        try:
            render_window = self.vtk_widget.GetRenderWindow()
            success = add_masks_to_pipeline(
                self.viewers, 
                self.ct_img, 
                mask_dir, 
                render_window
            )
            
            if success:
                self.mask_dir = mask_dir
                print(f"Successfully added masks from: {mask_dir}")
            else:
                print(f"Failed to add masks from: {mask_dir}")
            
            return success
            
        except Exception as e:
            print(f"Error adding masks: {e}")
            import traceback
            traceback.print_exc()
            return False

    def showEvent(self, event):
        """Called when the widget is shown"""
        super().showEvent(event)
        if not self._vtk_initialized and hasattr(self, 'vtk_widget'):
            # Initialize the VTK widget after it's shown
            QTimer.singleShot(100, self._initialize_vtk)
            self._vtk_initialized = True

    def _initialize_vtk(self):
        """Initialize VTK rendering"""
        try:
            print("Initializing VTK widget...")
            self.vtk_widget.Initialize()
            
            # Wait a moment then render
            QTimer.singleShot(50, self._render_vtk)
            
        except Exception as e:
            print(f"Error initializing VTK widget: {e}")
            # Try alternative initialization
            try:
                print("Trying alternative VTK initialization...")
                rw = self.vtk_widget.GetRenderWindow()
                rw.Render()
            except Exception as e2:
                print(f"Alternative initialization also failed: {e2}")

    def _render_vtk(self):
        """Perform the initial render"""
        try:
            rw = self.vtk_widget.GetRenderWindow()
            rw.Render()
            print("VTK rendering completed successfully")
        except Exception as e:
            print(f"Error during VTK render: {e}")

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if hasattr(self, 'vtk_widget') and self._vtk_initialized:
            # Update VTK render window size
            QTimer.singleShot(10, lambda: self.vtk_widget.GetRenderWindow().Render())