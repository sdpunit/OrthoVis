# This file can open pop up for importing both CT and Fluroscopy
from PySide6.QtWidgets import QWidget, QMessageBox, QApplication
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton, QWidget, QListWidgetItem)
from frontend_pages.project_setup.ui_project_setup_window import Ui_Form
from PySide6.QtWidgets import QFileDialog
from test import *
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QListWidgetItem, QMessageBox

name = ""
model = QStandardItemModel()
path_list = []
class ProjectSetup(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)



        self.ui.titlebar.ui.title.setText("Project Setup")
        self.ui.projectNameInput.setText(name)
        self.ui.importFluoro.clicked.connect(self.handleImportFluoro)
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
        path = path_list[0]
        try:
            se1_path = os.path.join(path, "SE000001")
            se3_path = os.path.join(path, "SE000003")
            if not os.path.exists(se1_path) or not os.path.exists(se3_path):
                raise FileNotFoundError("Required SE000001 or SE000003 folders are missing.")
            msg = QMessageBox(self)
            msg.setWindowTitle("Import Data")
            msg.setText("Data is being loaded!   ")
            msg.setStandardButtons(QMessageBox.NoButton)
            msg.setModal(False)
            msg.show()
            QApplication.processEvents()
            context = initialize_project(projectName, projectDesc, path)
            patient = context._singleton_data.get_instance()
            #Test for simple save function
            context.request_save(patient)
            self.ui.save.setEnabled(False)

            self.parent().setCurrentIndex(2)
            msg.done(0)
            msg.close()


        except FileNotFoundError as e:
            self.show_error(f"File not found, make sure you select file with CT file(SE000003) and Fluoroscopy file(SE000001) in the same folder.")
    
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
            self.add_import_item(folder_path)
            path_list.append(folder_path)
            print(f"Selected folder: {folder_path}")
            self.ui.save.setEnabled(True)

    def add_import_item(self, path):

        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(5, 2, 5, 2)


        label = QLabel(path)
        layout.addWidget(label)



        btn_delete = QPushButton("Delete")
        btn_delete.clicked.connect(lambda: self.delete_item(list_item))
        layout.addWidget(btn_delete)


        list_item = QListWidgetItem(self.ui.importListView)
        list_item.setSizeHint(row_widget.sizeHint())
        self.ui.importListView.addItem(list_item)
        self.ui.importListView.setItemWidget(list_item, row_widget)

    def select_file(self, label):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a file", "", "All Files (*.*)")
        if file_path:
            label.setText(file_path)

    def delete_item(self, list_item):
        row = self.ui.importListView.row(list_item)
        self.ui.importListView.takeItem(row)
        path_list.pop(row)

    def changeName(self, new_name):
        name = new_name
        self.ui.projectNameInput.setText(name)

    def show_error(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)  # 错误图标
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.exec()

    def handle_text_change(self):
        self.ui.save.setEnabled(True)
