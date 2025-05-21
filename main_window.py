# main_window.py
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QPushButton, QWidget, QVBoxLayout

# Import the application pages from frontend_pages.
from frontend_pages.startup.startup_window import HomePage
from frontend_pages.new_project.new_project_window import NewProject
from frontend_pages.segmentation.segmentation_window import Segmentation

# Imports for Widgets that are yet to be created...
# from frontend_pages.calibration_window import Calibration
# from frontend_pages.axis_window import DefineAxis
# from frontend_pages.visualisation_window import Visualisation

# This file manages the actual display window and handles the logic to decide which page to show.

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OrthoVis 2.0")

        # Start up page, chose to create project or open project
        self.homepage = HomePage()

        # Sets up new project, imports CT and Fluro etc
        self.newproject = NewProject()

        # Visualise the Imported ct, start segmentation
        self.segmentation = Segmentation()
        
        # Calibrate the fluroscopy 
        # self.calibration = Calibration()

        # Define the Axis
        # self.defineaxis = DefineAxis()

        # ** Perfom registration... can be just a button on the axis widget? **
        
        # Visualise the end result of the applicaton
        #self.visualisation = Visualisation()

        self.stack = QStackedWidget()

        # Add the pages to the widget stack
        self.stack.addWidget(self.homepage)       # index 0
        self.stack.addWidget(self.newproject)     # index 1
        self.stack.addWidget(self.segmentation)   # index 2
        # self.stack.addWidget(self.calibration)       # index 3
        # self.stack.addWidget(self.defineaxis)     # index 4
        # self.stack.addWidget(self.visualisation)   # index 5

        self.setCentralWidget(self.stack)

        self.stack.setCurrentIndex(2)             # Start at the opening page


        ## IMPLEMENT A BUNCH OF LOGIC HERE TO CYCLE BETWEEN STATES