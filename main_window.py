# main_window.py
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QPushButton, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer
import os

# Import the application pages from frontend_pages.
from frontend_pages.startup.startup_window import HomePage
from frontend_pages.project_setup.project_setup_window import ProjectSetup
from frontend_pages.segmentation.segmentation_window import Segmentation
from frontend_pages.calibration.calibration_window import Calibration
from frontend_pages.define_axis.define_axis_window import DefineAxis
from frontend_pages.registration.registration_window import Registration
from frontend_pages.visualisation.visualisation_window import Visualisation

# Import backend objects
from classes.objects import SingletonPatient, Context, RawState, SegmentState


# This file manages the actual display window and handles the logic to decide which page to show.

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OrthoVis 2.0")

        # Initialize backend context and singleton
        self.singleton = SingletonPatient.get_instance()
        self.context = Context(RawState(), self.singleton)

        # Start up page, chose to create project or open project
        self.homepage = HomePage()

        # Sets up new project, imports CT and Fluro etc
        self.projectsetup = ProjectSetup()
        
        # Connect project setup to context updates - IMPORTANT!
        self.projectsetup.project_saved.connect(self.on_project_saved)
        print("Connected project_saved signal to main window")

        # Visualise the Imported ct, start segmentation
        # Create without hardcoded paths - will be set dynamically from backend
        self.segmentation = Segmentation()
        
        # Set initial context for segmentation page
        self.segmentation.set_context(self.context)

        # Calibrate the fluroscopy
        self.calibration = Calibration()

        # Define the Axis
        self.defineaxis = DefineAxis()

        # Perform Registration
        self.registration = Registration()
        
        # Visualise the end result of the application
        self.visualisation = Visualisation()

        self.stack = QStackedWidget()

        # Add the pages to the widget stack
        self.stack.addWidget(self.homepage)       # index 0
        self.stack.addWidget(self.projectsetup)     # index 1
        self.stack.addWidget(self.segmentation)   # index 2
        self.stack.addWidget(self.calibration)       # index 3
        self.stack.addWidget(self.defineaxis)     # index 4
        self.stack.addWidget(self.registration)   # index 5
        self.stack.addWidget(self.visualisation)   # index 6

        self.setCentralWidget(self.stack)

        self.stack.setCurrentIndex(0)             # Start at the opening page

    def get_segmentation_page(self):
        """Get the segmentation page widget"""
        return self.segmentation

    def on_project_saved(self):
        """Handle project saved event from project setup - FOR NEW PROJECTS"""
        print("MainWindow: Project saved signal received from NEW project setup...")
        
        # Get the updated context from singleton
        singleton = SingletonPatient.get_instance()
        patient = singleton.patient
        
        print(f"Verification - Patient CT path: {patient.CT}")
        print(f"Verification - Patient mask path: {patient.seg_masks_dir}")
        
        # Note: For NEW projects, the VTK initialization and page transition
        # is handled by the project setup page's delayed transition mechanism.
        # The segmentation context is already set up in handleSave().
        
        print("MainWindow: New project setup completed - waiting for VTK loading to finish...")

    def setCurrentIndex(self, index):
        """Override to handle page transitions"""
        current_index = self.stack.currentIndex()
        print(f"Page transition: {current_index} -> {index}")
        
        self.stack.setCurrentIndex(index)
        
        # Handle segmentation page specifically
        if index == 2:  # Segmentation page
            print("Switching to segmentation page...")
            
            # Get current widget and check if VTK needs initialization
            current_widget = self.stack.currentWidget()
            if hasattr(current_widget, 'refresh_visualization'):
                # Only refresh if we're coming from another page after initial setup
                if current_index != 1:  # Not coming from project setup
                    print("Refreshing segmentation visualization...")
                    # Delay to ensure page is fully shown first
                    QTimer.singleShot(200, current_widget.refresh_visualization)
                else:
                    print("Coming from project setup - VTK already initializing via delayed transition")
            else:
                print("Warning: Segmentation widget doesn't have refresh_visualization method")