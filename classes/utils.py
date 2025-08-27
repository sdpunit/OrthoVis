from PySide6.QtWidgets import QMessageBox, QLabel, QHBoxLayout, QWidget
from PySide6.QtGui import QMovie, QIcon
from PySide6.QtCore import QSize

class ProgressDialogMixin:
    """Mixin class for universal progress dialog functionality"""
    
    def __init__(self):
        self.progress_dialog = None
    
    def show_progress_dialog(self, title: str, message: str):
        """Universal function to show progress dialog with loading animation"""
        self.close_progress_dialog()
        
        self.progress_dialog = QMessageBox(self)
        self.progress_dialog.setWindowTitle(title)
        self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
        self.progress_dialog.setModal(True)
        
        # Set custom icon
        self.progress_dialog.setWindowIcon(QIcon("assets/logo_small.png"))
        
        # Create custom widget for text + loading gif on same line
        content_widget = QWidget()
        layout = QHBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Text label
        text_label = QLabel(message)
        text_label.setStyleSheet("font: 12pt 'Segoe UI'; color: #333333;")
        layout.addWidget(text_label)
        
        # Set the custom widget as the dialog content
        self.progress_dialog.layout().addWidget(content_widget, 0, 0, 1, 1)
        
        self.progress_dialog.show()

    def close_progress_dialog(self):
        """Universal function to close progress dialog"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.accept()
            self.progress_dialog = None