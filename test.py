import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QTextEdit, QTextBrowser
from PySide6.QtGui import QPalette, Qt

from ui_testui import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # self.ui = Ui_MainWindow()
        # self.ui.setupUi(self)

        self.setWindowTitle("My App")
        self.setStyleSheet("background-color: #FFFFFF;")

        # Main Widget and Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        app_name = QLabel("OrthoVis")
        app_name.setMinimumWidth(200)
        app_name.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background-color: #100178;")
        app_name.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(app_name)

        # Right panel
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(10, 10, 10, 10)

        # Welcome panel
        welcome_box = QVBoxLayout()
        welcome_label = QLabel("Welcome to OrthoVis 2.0!")
        welcome_label.setStyleSheet("font-size: 40px; font-weight: bold;")
        introduction_label = QLabel("OrthoVis 2.0 provides fast and accurate 3D joint movement analysis by registering CT and fluoroscopy images, streamlining orthopedic research and clinical assessment.")
        introduction_label.setStyleSheet("font-size: 18px;")
        introduction_label.setWordWrap(True)
        welcome_box.addWidget(welcome_label)
        welcome_box.addWidget(introduction_label)
        # welcome_box.setAlignment(Qt.AlignVCenter)
        right_panel.addStretch()
        right_panel.addLayout(welcome_box)
        right_panel.addStretch()

        # Create or Open project
        create_project_box = QVBoxLayout()
        create_project_label = QLabel("New project")
        create_project_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        create_project_text = QLabel("Create a new OrthoVis project. \nYou will need valid CT scan and Fluroscopy files for OrthoVis to produce an accurate 3D reconstruction.")
        create_project_text.setWordWrap(True)
        create_project_text.setMinimumWidth(400)
        create_project_button = QPushButton("New Project")
        create_project_button.setStyleSheet("background-color: #100178; color: white; font-size: 14px; font-weight: bold;")
        create_project_button.setFixedSize(150, 40)
        # create_project_box.addWidget(create_project_label)
        # create_project_box.addWidget(create_project_text)
        # create_project_box.addWidget(create_project_button)
        # create_project_box.setAlignment(Qt.AlignTop)

        open_project_box = QVBoxLayout()
        open_project_label = QLabel("Open project")
        open_project_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        open_project_text = QLabel("Already got a project? Open an OrthoVis project from file system.")
        open_project_button = QPushButton("Open Project")
        open_project_button.setStyleSheet("background-color: #100178; color: white; font-size: 14px; font-weight: bold;")
        open_project_button.setFixedSize(150, 40)
        # open_project_box.addWidget(open_project_label)
        # open_project_box.addWidget(open_project_text)
        # open_project_box.addWidget(open_project_button)
        # open_project_box.setAlignment(Qt.AlignTop)

        # projects_box.addLayout(create_project_box)
        # projects_box.addLayout(open_project_box)
        # projects_box.setAlignment(Qt.AlignTop)
        # projects_box.setStretch(0, 1)
        # projects_box.setStretch(1, 1)

        # right_panel.addLayout(projects_box)

        labels = QHBoxLayout()
        labels.addWidget(create_project_label,1, Qt.AlignLeft)
        labels.addWidget(open_project_label, 1, Qt.AlignLeft)

        texts = QHBoxLayout()
        texts.addWidget(create_project_text, 1, Qt.AlignLeft)
        texts.addWidget(open_project_text, 1, Qt.AlignLeft)

        buttons = QHBoxLayout()
        buttons.addWidget(create_project_button, 1, Qt.AlignLeft)
        buttons.addWidget(open_project_button, 1, Qt.AlignLeft)

        projects_box = QVBoxLayout()
        projects_box.addStretch()
        projects_box.addLayout(labels)
        projects_box.addStretch()
        projects_box.addLayout(texts)
        projects_box.addStretch()
        projects_box.addLayout(buttons)
        projects_box.addStretch()

        right_panel.addLayout(projects_box)
        right_panel.addStretch()
        right_panel.setAlignment(Qt.AlignTop)

        main_layout.addLayout(right_panel)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()