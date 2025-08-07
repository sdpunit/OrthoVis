# segmentation_window.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtCore import QTimer
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# Import our VTK pipeline creator
try:
    # Try relative import from project root
    import sys
    import os
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from seg.embedding import create_vtk_pipeline
except ImportError as e:
    print(f"Warning: Could not import create_vtk_pipeline: {e}")
    print("Make sure embedding.py is in the seg/ folder at project root.")
    create_vtk_pipeline = None

class Segmentation(QWidget):
    def __init__(self, ct_dir: str, mask_dir: str):
        super().__init__()
        self._vtk_initialized = False
        self.ct_dir = ct_dir
        self.mask_dir = mask_dir

        self.setupUI()
        
        # Initialize VTK after UI is set up
        if create_vtk_pipeline is not None:
            self.setupVTK()

    def setupUI(self):
        """Set up the user interface"""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # VTK display frame (takes up most of the space)
        self.vtk_frame = QFrame()
        self.vtk_frame.setStyleSheet("QFrame { border: 1px solid gray; }")
        vtk_layout = QVBoxLayout(self.vtk_frame)
        vtk_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the VTK widget
        self.vtk_widget = QVTKRenderWindowInteractor(self.vtk_frame)
        vtk_layout.addWidget(self.vtk_widget)
        
        # Add VTK frame to main layout
        main_layout.addWidget(self.vtk_frame, stretch=3)  # 3/4 of the space
        
        # Right panel for controls (if needed later)
        self.control_panel = QFrame()
        self.control_panel.setStyleSheet("QFrame { border: 1px solid gray; background-color: #f0f0f0; }")
        self.control_panel.setMaximumWidth(250)
        self.control_panel.setMinimumWidth(200)
        
        control_layout = QVBoxLayout(self.control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add control panel to main layout
        main_layout.addWidget(self.control_panel, stretch=1)  # 1/4 of the space

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
            self.interactor_style = create_vtk_pipeline(
                self.ct_dir, 
                self.mask_dir, 
                render_window=render_window
            )
            
            # Get the interactor and set our custom style
            interactor = render_window.GetInteractor()
            interactor.SetInteractorStyle(self.interactor_style)
            
            print(f"VTK pipeline created successfully for CT: {self.ct_dir}")
            print(f"Masks directory: {self.mask_dir}")
            
        except Exception as e:
            print(f"Error setting up VTK pipeline: {e}")
            import traceback
            traceback.print_exc()

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