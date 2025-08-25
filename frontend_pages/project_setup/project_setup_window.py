# This file can open pop up for importing both CT and Fluroscopy
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget, QListWidgetItem
from PySide6.QtGui import QStandardItemModel
from PySide6.QtCore import Signal

from frontend_pages.project_setup.ui_project_setup_window import Ui_Form

# Import backend objects
from classes.objects import SingletonPatient, Context, initialize_project, SegmentState

name = ""
model = QStandardItemModel()
path_list = []
path_dict = {}

class ProjectSetup(QWidget):
    # Signal to notify when project is saved
    project_saved = Signal()
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        # Initialize attributes for dialog and transition handling
        self.progress_dialog = None  # Single dialog for all progress messages
        self.pending_stacked_widget = None
        self.pending_main_window = None

        self.ui.titlebar.ui.title.setText("Project Setup")
        self.ui.projectNameInput.setText(name)
        self.ui.importCT.clicked.connect(self.handleImportCT)
        self.ui.importFL.clicked.connect(self.handleImportFL)
        self.ui.importCG.clicked.connect(self.handleImportCG)
        self.ui.save.clicked.connect(self.handleSave)

        # Enable Save button only when there are changes to save
        self.ui.save.setEnabled(False)
        self.ui.projectNameInput.textChanged.connect(self.handle_text_change)
        self.ui.projectDesInput.textChanged.connect(self.handle_text_change)

        self.ui.sidebar.ui.project_setup.setStyleSheet(
        """
            QPushButton { 
                color: white; 
                background-color: #6f8ab7; 
                border: none; 
                padding: 10px 25px;  
                text-align: center;}
        """
        )

    def show_progress_dialog(self, title: str, message: str):
        """Universal function to show progress dialog"""
        self.close_progress_dialog()  # Close any existing dialog first
        
        self.progress_dialog = QMessageBox(self)
        self.progress_dialog.setWindowTitle(title)
        self.progress_dialog.setText(message)
        self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()

    def close_progress_dialog(self):
        """Universal function to close progress dialog"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.accept()
            self.progress_dialog = None

    def handleSave(self):
        projectName = self.ui.projectNameInput.text()
        if not projectName:
            self.show_error("Project name cannot be empty.")
            return
        projectDesc = self.ui.projectDesInput.toPlainText()
        # Initialize a new patient and context
        if not path_list:
            self.show_error("Please import at least one CT sequence folder.")
            return
        
        ct_path = path_dict.get("CT", "")
        fluoro_path = path_dict.get("fluoro", "")
        caligrid_path = path_dict.get("caligrid", "")

        if not ct_path:
            self.show_error("CT path is required.")
            return

        try:
            # Get singleton and update patient data
            singleton = SingletonPatient.get_instance()
            patient = singleton.patient
            
            # Update patient with new data
            patient.name = projectName
            patient.description = projectDesc
            patient.CT = ct_path
            patient.fluoro = fluoro_path
            patient.caligrid = caligrid_path
            
            print(f"Updated patient data:")
            print(f"  Name: {patient.name}")
            print(f"  CT: {patient.CT}")
            print(f"  Fluoro: {patient.fluoro}")
            print(f"  Caligrid: {patient.caligrid}")
            
            # Initialize context and save project
            context = initialize_project(projectName, projectDesc, ct_path, fluoro_path, caligrid_path)
            
            # Save the project through context
            context.request_save(singleton)
            
            # Transition to segmentation state
            #context.transition_to(SegmentState())
            
            self.ui.save.setEnabled(False)
            
            # Get the main window components for delayed transition
            stacked_widget = self.parent()  # QStackedWidget
            main_window = stacked_widget.parent()  # MainWindow
            
            print(f"Stacked widget type: {type(stacked_widget)}")
            print(f"Main window type: {type(main_window)}")
            
            # Store references for transition callback
            self.pending_stacked_widget = stacked_widget
            self.pending_main_window = main_window
            
            # Get segmentation page and set up delayed transition
            segmentation_page = None
            if hasattr(main_window, 'segmentation'):
                segmentation_page = main_window.segmentation
                print("Got segmentation page via main_window.segmentation")
            elif hasattr(stacked_widget, 'widget'):
                segmentation_page = stacked_widget.widget(2)
                print("Got segmentation page via stacked_widget.widget(2)")
            
            if segmentation_page:
                print(f"Segmentation page found: {type(segmentation_page)}")
                
                # Check if delayed transition method exists, otherwise use regular method
                if hasattr(segmentation_page, 'set_context_with_delayed_transition'):
                    print("Using delayed transition method")
                    segmentation_page.set_context_with_delayed_transition(
                        context, 
                        self.on_vtk_loading_complete
                    )
                elif hasattr(segmentation_page, 'set_context'):
                    print("Using regular set_context method with manual callback setup")
                    # Manually set up the callback
                    print(f"Setting completion_callback to: {self.on_vtk_loading_complete}")
                    segmentation_page.completion_callback = self.on_vtk_loading_complete
                    
                    # Verify it was set
                    if hasattr(segmentation_page, 'completion_callback'):
                        print(f"Callback successfully set: {segmentation_page.completion_callback}")
                    else:
                        print("ERROR: Failed to set completion_callback")
                    
                    segmentation_page.set_context(context)
                else:
                    print("ERROR: No set_context method found")
                    self.show_error("Internal error: Cannot set context on segmentation page")
                    self.close_progress_dialog()
                    return
                
                # Store context in main window
                if hasattr(main_window, 'context'):
                    main_window.context = context
                
                print("Project saved - VTK loading started, staying on project setup page...")
                
                # Emit signal that project was saved successfully
                self.project_saved.emit()
            else:
                print("ERROR: Could not find segmentation page")
                self.show_error("Internal error: Segmentation page not available")
                self.close_progress_dialog()

        except FileNotFoundError as e:
            self.show_error(f"File not found, make sure you select folder with CT and Fluoroscopy files in the same path.")
            self.close_progress_dialog()
        except Exception as e:
            self.show_error(f"Error saving project: {str(e)}")
            self.close_progress_dialog()

    def on_vtk_loading_complete(self):
        """Called when VTK loading is complete - transition to segmentation page"""
        print("VTK loading complete - transitioning to segmentation page")
        
        # Close the loading dialog
        self.close_progress_dialog()
        
        if hasattr(self, 'pending_stacked_widget'):
            self.pending_stacked_widget.setCurrentIndex(2)
            print("Successfully transitioned to segmentation page")
            
            # Clean up pending references
            delattr(self, 'pending_stacked_widget')
            if hasattr(self, 'pending_main_window'):
                delattr(self, 'pending_main_window')
    
    def handleImportFL(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select the Fluoroscopy sequence folder (e.g. SE000001)"
        )
        
        if folder_path:
            self.add_import_item(folder_path, "fluoro")
            if folder_path not in path_list:
                path_list.append(folder_path)
            print(f"Selected fluoroscopy folder: {folder_path}")
            self.ui.save.setEnabled(True)

    def handleImportCG(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select the Calibration Grid sequence folder"
        )
        
        if folder_path:
            self.add_import_item(folder_path, "caligrid")
            if folder_path not in path_list:
                path_list.append(folder_path)
            print(f"Selected calibration grid folder: {folder_path}")
            self.ui.save.setEnabled(True)

    def handleImportCT(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select the CT sequence folder (e.g. SE000003)"
        )
        
        if folder_path:
            self.add_import_item(folder_path, "CT")
            if folder_path not in path_list:
                path_list.append(folder_path)
            print(f"Selected CT folder: {folder_path}")
            self.ui.save.setEnabled(True)

    def add_import_item(self, path: str, key: str):
        # Remove existing item with same key if it exists
        for i in range(self.ui.importListView.count()):
            item = self.ui.importListView.item(i)
            widget = self.ui.importListView.itemWidget(item)
            if widget:
                label = widget.findChild(QLabel)
                if label and path_dict.get(key) == label.text():
                    self.ui.importListView.takeItem(i)
                    if label.text() in path_list:
                        path_list.remove(label.text())
                    break

        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(5, 2, 5, 2)

        # Add key prefix to show what type of data this is
        display_text = f"[{key.upper()}] {path}"
        label = QLabel(display_text)
        layout.addWidget(label)

        btn_delete = QPushButton("X")
        btn_delete.clicked.connect(lambda: self.delete_item(list_item, path, key))
        btn_delete.setFixedWidth(25)
        layout.addWidget(btn_delete)

        list_item = QListWidgetItem(self.ui.importListView)
        list_item.setSizeHint(row_widget.sizeHint())
        self.ui.importListView.addItem(list_item)
        self.ui.importListView.setItemWidget(list_item, row_widget)

        path_dict[key] = path
        print(f"Updated path_dict: {path_dict}")

    def select_file(self, label):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a file", "", "All Files (*.*)")
        if file_path:
            label.setText(file_path)

    def delete_item(self, list_item: QListWidgetItem, path: str, key: str):
        row = self.ui.importListView.row(list_item)
        self.ui.importListView.takeItem(row)
        
        if path in path_list:
            path_list.remove(path)
        
        if key in path_dict and path_dict[key] == path:
            del path_dict[key]
        
        print(f"Updated path_dict after deletion: {path_dict}")

    def changeName(self, new_name):
        global name
        name = new_name
        self.ui.projectNameInput.setText(name)

    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.exec()

    def handle_text_change(self):
        self.ui.save.setEnabled(True)