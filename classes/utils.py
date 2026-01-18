from PySide6.QtWidgets import (
    QMessageBox,
    QLabel,
    QVBoxLayout,
    QWidget,
    QProgressBar
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt


class ProgressDialogMixin:
    """Mixin class for universal progress dialog functionality"""

    def __init__(self):
        self.progress_dialog = None
        self._progress_bar = None
        self._status_label = None

    def show_progress_dialog(self, title: str, message: str):
        """Show progress dialog with status text and progress bar"""
        self.close_progress_dialog()

        self.progress_dialog = QMessageBox(self)
        self.progress_dialog.setWindowTitle(title)
        self.progress_dialog.setStandardButtons(QMessageBox.NoButton)
        self.progress_dialog.setModal(True)
        self.progress_dialog.setWindowIcon(QIcon("assets/logo_small.png"))

        # ---- Custom content widget ----
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Status label
        self._status_label = QLabel(message)
        self._status_label.setAlignment(Qt.AlignLeft)
        self._status_label.setStyleSheet(
            "font: 12pt 'Segoe UI'; color: #333333;"
        )
        main_layout.addWidget(self._status_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(0)  # indeterminate by default
        main_layout.addWidget(self._progress_bar)

        # Inject into QMessageBox layout
        self.progress_dialog.layout().addWidget(
            content_widget, 0, 0, 1, 1
        )

        self.progress_dialog.show()

    # ---------- Slots / helpers ----------

    def update_progress(self, value):
        """
        Update progress bar.
        value = None  → indeterminate (busy)
        value = int   → determinate percentage
        """
        if not self._progress_bar:
            return

        if value is None:
            self._progress_bar.setRange(0, 0)  # busy mode
        else:
            if self._progress_bar.maximum() == 0:
                self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(value)

    def update_status(self, text: str):
        """Update status text in dialog"""
        if self._status_label:
            self._status_label.setText(text)

    def close_progress_dialog(self):
        """Close and reset progress dialog"""
        if self.progress_dialog:
            self.progress_dialog.accept()
            self.progress_dialog = None
            self._progress_bar = None
            self._status_label = None
    