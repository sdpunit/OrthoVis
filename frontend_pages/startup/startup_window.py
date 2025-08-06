# Startup window on opening of the application
from PySide6.QtWidgets import QWidget
from frontend_pages.startup.ui_startup_window import Ui_HomePage
from frontend_pages.project_setup.project_setup_window import ProjectSetup
from PySide6.QtWidgets import QFileDialog
import json

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_HomePage()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.handle_new_project)
        self.ui.pushButton_2.clicked.connect(self.handle_open_project)
        self.ui.pushButton.setToolTip("Create a new OrthoVis project with CT and Fluoroscopy data.")
        self.ui.pushButton_2.setToolTip("Open an existing OrthoVis project from your computer.")
        self.ui.pushButton.setStyleSheet("""
            QPushButton {
                background-color: rgb(255, 215, 0);
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgb(255, 230, 50);
                font-size: 18px;
            }
        """)
        self.ui.pushButton_2.setStyleSheet("""
                    QPushButton {
                        background-color: rgb(255, 215, 0);
                        border-radius: 10px;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: rgb(255, 230, 50);
                        font-size: 18px;
                    }
                """)
    def handle_new_project(self):
        # Jump to the new project page
        self.parent().setCurrentIndex(1)

    def handle_open_project(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select the CT sequence folder (e.g. SE000000)"
        )

        if folder_path:
            # Define the path to your JSON file
            file_path = folder_path + "/data.json"

            try:
                # Open the JSON file in read mode ('r')
                with open(file_path, 'r') as f:
                    # Load the JSON data from the file
                    data = json.load(f)

                # Now 'data' contains the parsed JSON as a Python object
                projectsetup = self.parent().widget(1)
                projectsetup.updateData(data)
                self.parent().setCurrentIndex(1)


            except FileNotFoundError:
                print(f"Error: The file '{file_path}' was not found.")
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from '{file_path}'. Check if the file contains valid JSON.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                    
