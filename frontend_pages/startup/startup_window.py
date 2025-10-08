# startup_window.py - Startup window on opening of the application
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import QObject
from frontend_pages.startup.ui_startup_window import Ui_HomePage
from PySide6.QtWidgets import QFileDialog
from classes.objects import *
from datetime import datetime
import json, os

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_HomePage()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.handle_new_project)
        self.ui.pushButton_2.clicked.connect(self.handle_open_project)
        
        # Style the buttons
        button_style = """
            QPushButton {
                background-color: rgb(255, 215, 0);
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgb(255, 230, 50);
                font-size: 18px;
            }
        """
        self.ui.pushButton.setStyleSheet(button_style)
        self.ui.pushButton_2.setStyleSheet(button_style)

        current_dir = Path(__file__).resolve().parent.parent
        parent_dir = current_dir.parent
        path = parent_dir / "Projects" / "opened_projects.txt"
        if os.path.isfile(path):
            self.read_entries()  

    def handle_new_project(self):
        """Handle new project creation"""
        self.parent().setCurrentIndex(1)

    def handle_open_project(self):
        """Handle opening an existing project"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select existing OrthoVis project folder"
        )

        if folder_path:
            json_file_path = os.path.join(folder_path, "data.json")
            
            try:
                # Load project data from JSON
                with open(json_file_path, 'r') as f:
                    project_data = json.load(f)
                
                print(f"=== Loading existing project ===")
                print(f"Project folder: {folder_path}")
                print(f"Project data: {project_data}")

                # Whenever the new project is opened, append the entry to the opened_projects.txt
                self.append_entry(project_data["name"])
                
                # Load project into backend singleton
                success = self.load_project_into_backend(project_data, folder_path)
                
                if success:
                    # Get the main window components
                    stacked_widget = self.parent()  # QStackedWidget
                    main_window = stacked_widget.parent()  # MainWindow
                    
                    print(f"Stacked widget type: {type(stacked_widget)}")
                    print(f"Main window type: {type(main_window)}")
                    
                    # Create context and set to SegmentState
                    singleton = SingletonPatient.get_instance()
                    state = StateFactory.get_state(project_data["state"])
                    context = Context(state, singleton)

                    state = project_data["state"]
                    
                    # Get segmentation page
                    page = self.get_page(main_window, stacked_widget, state)
                    
                    if page:
                        print(f"Segmentation page found: {type(page)}")
                        print(f"Available methods: {[method for method in dir(page) if not method.startswith('_') and 'context' in method.lower()]}")
                        
                        # Store references for transition callback
                        self.pending_stacked_widget = stacked_widget
                        self.pending_main_window = main_window
                        
                        # Check if delayed transition method exists, otherwise use regular method
                        if hasattr(page, 'set_context_with_delayed_transition'):
                            print("Using delayed transition method")
                            page.set_context_with_delayed_transition(
                                context, 
                                self.on_vtk_loading_complete
                            )
                        elif hasattr(page, 'set_context'):
                            print("Using regular set_context method with manual callback setup")
                            # Manually set up the callback
                            print(f"Setting completion_callback to: {self.on_vtk_loading_complete}")
                            page.completion_callback = self.on_vtk_loading_complete
                            
                            # Verify it was set
                            if hasattr(page, 'completion_callback'):
                                print(f"Callback successfully set: {page.completion_callback}")
                            else:
                                print("ERROR: Failed to set completion_callback")
                            
                            page.set_context(context)
                        else:
                            print("ERROR: No set_context method found")
                            print(f"All methods: {[method for method in dir(page) if not method.startswith('_')]}")
                            self.show_error("Internal error: Cannot set context on segmentation page")
                            return
                        
                        # Store context in main window
                        if hasattr(main_window, 'context'):
                            main_window.context = context
                        
                        
                        print("Project loaded - VTK loading started, staying on startup page...")
                    else:
                        print("ERROR: Could not find segmentation page")
                        self.show_error("Internal error: Segmentation page not available")
                else:
                    self.show_error("Failed to load project data")

            except FileNotFoundError:
                self.show_error(
                    "Project file 'data.json' not found in selected folder.\n"
                    "Make sure you selected a valid OrthoVis project folder."
                )
            except json.JSONDecodeError:
                self.show_error(
                    "Invalid project file format.\n"
                    "The data.json file appears to be corrupted."
                )
            except Exception as e:
                self.show_error(f"Error loading project: {str(e)}")


    def append_entry(self, name, max_entries=3):
        """
        Appends an entry in the format: name, D-M-YYYY to display the recently opened projects
        If the file already has max_entries, deletes the last entry first.
        """
        current_dir = Path(__file__).resolve().parent.parent
        parent_dir = current_dir.parent
        path = parent_dir / "Projects" / "opened_projects.txt" 

        # Ensure parent folder exists
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        # Read existing lines (if any)
        lines = []

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # If file already has max_entries, drop the last one
        if len(lines) >= max_entries:
            lines = lines[:-1]

        # Format today's date
        today = datetime.today()
        try:
            formatted_date = today.strftime("%-d-%-m-%Y")  # Linux/macOS
        except ValueError:
            formatted_date = today.strftime("%#d-%#m-%Y")  # Windows

        # Add new entry at the top
        lines.insert(0, f"{name}, {formatted_date}\n")

        # Write everything back
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def read_entries(self):
        """
        Appends an entry in the format: name, D-M-YYYY to display the recently opened projects
        If the file already has max_entries, deletes the last entry first.
        """
        current_dir = Path(__file__).resolve().parent.parent
        parent_dir = current_dir.parent
        path = parent_dir / "Projects" / "opened_projects.txt" 

        lines = []

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  # skip empty lines
                    name, date = line.split(", ", 1)
                    lines.append((name, date))

        labels = [(self.ui.fileName1, self.ui.lastAccess1), (self.ui.fileName2, self.ui.lastAccess2),
                  (self.ui.fileName3, self.ui.lastAccess3)]
        
        for i in range(len(lines)):
            file, lastAccess = labels[i]
            name, date = lines[i]
            file.setText(name)
            lastAccess.setText(date)

    
    def get_page(self, main_window : QObject, stacked_widget: QObject, state: str) -> QObject:
        page = None
        index = 0
        page_name = ''

        if state == "RawState" or "SegmentState":
            page = main_window.segmentation
            page_name = "segmentation"
            index = 2
        

        
        # elif state == "CalibrationState":
        #     page = main_window.segmentation
        #     page_name = "segmentation"
        #     index = 2
        

        if hasattr(main_window, page_name) and isinstance(state, SegmentState):
            print("Got segmentation page via main_window.segmentation")
        elif hasattr(stacked_widget, 'widget'):
            page = stacked_widget.widget(index)
            print("Got segmentation page via stacked_widget.widget(2)")
        return page

    def on_vtk_loading_complete(self):
        """Called when VTK loading is complete - transition to segmentation page"""
        print("VTK loading complete - transitioning to segmentation page")
        
        if hasattr(self, 'pending_stacked_widget'):
            self.pending_stacked_widget.setCurrentIndex(2)
            print("Successfully transitioned to segmentation page")
            
            # Clean up pending references
            delattr(self, 'pending_stacked_widget')
            if hasattr(self, 'pending_main_window'):
                delattr(self, 'pending_main_window')

    def load_project_into_backend(self, project_data: dict, project_folder: str) -> bool:
        """Load project data into the backend singleton and validate paths"""
        try:
            # Get singleton instance
            singleton = SingletonPatient.get_instance()
            patient = singleton.patient
            
            # Extract data from JSON
            name = project_data.get('name', 'Unknown Project')
            description = project_data.get('description', '')
            ct_path = project_data.get('CT', '')
            fluoro_path = project_data.get('fluoro', '')
            caligrid_path = project_data.get('caligrid', '')
            seg_masks_path = project_data.get('seg_masks_dir', '')
            
            # Validate and fix paths
            ct_path = self.validate_and_fix_path(ct_path, project_folder)
            fluoro_path = self.validate_and_fix_path(fluoro_path, project_folder)
            caligrid_path = self.validate_and_fix_path(caligrid_path, project_folder)
            
            # Handle seg_masks_dir
            if not seg_masks_path:
                seg_masks_path = os.path.join(project_folder, "seg_masks")
            else:
                seg_masks_path = self.validate_and_fix_path(seg_masks_path, project_folder)
            
            # Update patient data
            patient.name = name
            patient.description = description
            patient.CT = ct_path
            patient.fluoro = fluoro_path
            patient.caligrid = caligrid_path
            patient.seg_masks_dir = seg_masks_path
            
            print(f"Loaded project into backend:")
            print(f"  Name: {patient.name}")
            print(f"  CT: {patient.CT} (exists: {os.path.exists(patient.CT) if patient.CT else False})")
            print(f"  Fluoro: {patient.fluoro} (exists: {os.path.exists(patient.fluoro) if patient.fluoro else False})")
            print(f"  Caligrid: {patient.caligrid} (exists: {os.path.exists(patient.caligrid) if patient.caligrid else False})")
            print(f"  Seg masks: {patient.seg_masks_dir} (exists: {os.path.exists(patient.seg_masks_dir) if patient.seg_masks_dir else False})")
            
            # Validate CT exists
            if not patient.CT or not os.path.exists(patient.CT):
                print(f"ERROR: CT directory not found: {patient.CT}")
                return False
            
            # Check CT content
            if not self.check_ct_content(patient.CT):
                print(f"ERROR: CT directory is empty or invalid: {patient.CT}")
                return False
            
            # Check segmentation masks
            self.check_segmentation_masks(patient.seg_masks_dir)
            
            return True
            
        except Exception as e:
            print(f"Error loading project into backend: {e}")
            import traceback
            traceback.print_exc()
            return False

    def validate_and_fix_path(self, path: str, project_folder: str) -> str:
        """Validate and fix paths that might be absolute or relative"""
        if not path:
            return ""
        
        # If path exists as-is, use it
        if os.path.isabs(path) and os.path.exists(path):
            return path
        
        # Try relative to project folder
        relative_path = os.path.join(project_folder, os.path.basename(path))
        if os.path.exists(relative_path):
            return relative_path
        
        # Try original path
        if os.path.exists(path):
            return path
        
        return path

    def check_ct_content(self, ct_path: str) -> bool:
        """Check if CT directory contains valid DICOM files"""
        if not os.path.exists(ct_path):
            return False
        
        try:
            items = os.listdir(ct_path)
            if not items:
                return False
            
            # Look for DICOM files
            dicom_files = [f for f in items if '.' not in f or f.endswith('.dcm')]
            if dicom_files:
                print(f"Found {len(dicom_files)} DICOM files in CT directory")
                return True
            
            # Check subdirectories
            for item in items:
                item_path = os.path.join(ct_path, item)
                if os.path.isdir(item_path):
                    sub_items = os.listdir(item_path)
                    sub_dicom = [f for f in sub_items if '.' not in f or f.endswith('.dcm')]
                    if sub_dicom:
                        print(f"Found {len(sub_dicom)} DICOM files in subdirectory: {item}")
                        return True
            
            print("No DICOM files found in CT directory")
            return False
            
        except Exception as e:
            print(f"Error checking CT content: {e}")
            return False

    def check_segmentation_masks(self, seg_masks_path: str):
        """Check segmentation masks directory"""
        if not seg_masks_path or not os.path.exists(seg_masks_path):
            print("No segmentation masks directory - will show CT only")
            return
        
        try:
            mask_files = [f for f in os.listdir(seg_masks_path) 
                         if f.endswith(('.nii.gz', '.nii'))]
            
            if mask_files:
                print(f"Found {len(mask_files)} segmentation mask files:")
                for mask_file in mask_files:
                    print(f"  - {mask_file}")
            else:
                print("Segmentation masks directory exists but is empty")
                
        except Exception as e:
            print(f"Error checking segmentation masks: {e}")

    def show_error(self, message: str):
        """Show error message dialog"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Error Opening Project")
        msg.setText(message)
        msg.exec()
        print(f"Error: {message}")




        
'''
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QSizePolicy, QVBoxLayout
from PySide6.QtCore import QObject, Qt
from frontend_pages.startup.ui_startup_window import Ui_HomePage
from classes.objects import *
from datetime import datetime
from pathlib import Path
import json, os

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_HomePage()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.handle_new_project)
        self.ui.pushButton_2.clicked.connect(self.handle_open_project)
        

        self.setup_responsive_layouts()
        self.apply_styles()
        self.update_button_sizes()

        current_dir = Path(__file__).resolve().parent.parent
        parent_dir = current_dir.parent
        path = parent_dir / "Projects" / "opened_projects.txt"
        if os.path.isfile(path):
            self.read_entries()

    def setup_responsive_layouts(self):
        """Adjust spacing and size policies for a responsive rounded layout."""

        self.setMinimumSize(960, 640)

        self.ui.gridLayout_2.setContentsMargins(32, 32, 32, 32)
        self.ui.gridLayout_2.setHorizontalSpacing(24)
        self.ui.gridLayout_2.setVerticalSpacing(24)

        self.ui.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.ui.mainLayout.setSpacing(32)

        self.ui.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.ui.leftLayout.setHorizontalSpacing(0)
        self.ui.leftLayout.setVerticalSpacing(0)

        self.ui.gridLayout_4.setContentsMargins(32, 32, 32, 32)
        self.ui.gridLayout_4.setHorizontalSpacing(12)
        self.ui.gridLayout_4.setVerticalSpacing(12)

        self.ui.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.ui.rightLayout.setSpacing(0)

        self.ui.gridLayout_3.setContentsMargins(32, 32, 32, 32)
        self.ui.gridLayout_3.setHorizontalSpacing(24)
        self.ui.gridLayout_3.setVerticalSpacing(24)
        self.ui.gridLayout_3.setRowStretch(3, 3)
        self.ui.gridLayout_3.setRowStretch(4, 4)

        self.ui.selectionLayout.setSpacing(18)
        self.ui.texts.setSpacing(24)

        self.ui.buttonsLayout.setContentsMargins(0, 0, 0, 0)
        self.ui.buttonsLayout.setSpacing(24)
        self.ui.buttonsLayout.setStretch(0, 1)
        self.ui.buttonsLayout.setStretch(1, 1)

        self.ui.verticalLayout_3.setContentsMargins(24, 24, 24, 24)
        self.ui.verticalLayout_3.setSpacing(16)

        header_layouts = [
            self.ui.horizontalLayout,
            self.ui.horizontalLayout_3,
            self.ui.horizontalLayout_4,
            self.ui.horizontalLayout_5,
        ]
        for layout in header_layouts:
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(18)

        for frame in (self.ui.project1Frame, self.ui.project2Frame, self.ui.project3Frame):
            frame.setMinimumHeight(72)

        self.ui.headers.setMinimumHeight(64)

        button_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for frame, button in (
            (self.ui.newProjectFrame, self.ui.pushButton),
            (self.ui.openProjectFrame, self.ui.pushButton_2),
        ):
            if frame.layout() is None:
                frame_layout = QVBoxLayout(frame)
            else:
                frame_layout = frame.layout()
                while frame_layout.count():
                    item = frame_layout.takeAt(0)
                    if widget := item.widget():
                        widget.setParent(None)
            frame_layout.setContentsMargins(0, 0, 0, 0)
            frame_layout.addWidget(button)
            frame_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            button.setSizePolicy(button_policy)
            button.setMinimumHeight(64)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

    def apply_styles(self):
        """Apply a rounded, modern visual style to the startup window."""

        base_styles = """
            QWidget#HomePage {
                background-color: #0b1120;
            }
            QFrame#leftFrame {
                background-color: #1d3461;
                border-radius: 32px;
            }
            QLabel#lblOrthoVis {
                color: #f8fafc;
                letter-spacing: 1.5px;
            }
            QFrame#rightFrame {
                background-color: rgba(15, 23, 42, 0.75);
                border-radius: 32px;
                border: 1px solid rgba(148, 163, 184, 0.25);
            }
            QLabel#lblWelcome,
            QLabel#newPfoject,
            QLabel#openProject,
            QLabel#recentsLabel {
                color: #f8fafc;
            }
            QLabel#lblIntro,
            QLabel#newProjectText,
            QLabel#createProjectText {
                color: rgba(226, 232, 240, 0.85);
            }
            QFrame#recentsFrame {
                background-color: rgba(15, 23, 42, 0.55);
                border-radius: 24px;
                border: 1px solid rgba(148, 163, 184, 0.15);
            }
            QFrame#headers {
                background-color: rgba(148, 163, 184, 0.2);
                border-radius: 18px;
            }
            QLabel#fileNameLabel,
            QLabel#lastAccessLabel {
                color: rgba(226, 232, 240, 0.8);
            }
            QFrame#project1Frame,
            QFrame#project2Frame,
            QFrame#project3Frame {
                background-color: rgba(15, 23, 42, 0.6);
                border-radius: 18px;
                border: 1px solid rgba(148, 163, 184, 0.12);
            }
            QLabel#fileName1,
            QLabel#fileName2,
            QLabel#fileName3 {
                color: #f8fafc;
            }
            QLabel#lastAccess1,
            QLabel#lastAccess2,
            QLabel#lastAccess3 {
                color: rgba(226, 232, 240, 0.7);
            }
            QPushButton {
                background-color: #facc15;
                color: #0f172a;
                border-radius: 24px;
                padding: 18px 28px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover {
                background-color: #fde047;
            }
            QPushButton:pressed {
                background-color: #eab308;
            }
        """


        self.setStyleSheet(base_styles)

'''