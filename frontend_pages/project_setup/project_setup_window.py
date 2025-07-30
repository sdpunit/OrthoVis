# This file can open pop up for importing both CT and Fluroscopy
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QStandardItemModel, QStandardItem
from frontend_pages.project_setup.ui_project_setup_window import Ui_Form
from PySide6.QtWidgets import QFileDialog
from classes.test import *

name = ""
model = QStandardItemModel()

class ProjectSetup(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.importListView.setModel(model)

        self.ui.titlebar.ui.title.setText("New Project")
        self.ui.projectNameInput.setText(name)
        self.ui.importFluoro.clicked.connect(self.handleImportFluoro)
        self.ui.save.clicked.connect(self.handleSave)
        
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


    def handleSave(self):
        projectName = self.ui.projectNameInput.text()
        # Initialize a new patient and context
        #print(f"Item: {model.itemFromIndex(0)}")
        idx = model.index(0, 0)
        path = model.itemFromIndex(idx).text()
        print(f"{path}")
        context = initialize_project(projectName, 24, path)
        #Test for simple save function
        save_patient_data_to_file(context, projectName)
        self.parent().setCurrentIndex(2)
    
    # def handleImportCT(self):
    #     folder_path = QFileDialog.getExistingDirectory(
    #         self,
    #         "Select the CT sequence folder (e.g. SE000000)"
    #     )
        
    #     if folder_path:
    #         item = QStandardItem(folder_path)
    #         model.appendRow(item)

    #         print(f"Selected folder: {folder_path}")


    def handleImportFluoro(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select the CT sequence folder (e.g. SE000000)"
        )
        
        if folder_path:
            item = QStandardItem(folder_path)
            model.appendRow(item)
            print(f"Selected folder: {folder_path}")
    

    def changeName(self, new_name):
        name = new_name
        self.ui.projectNameInput.setText(name)
