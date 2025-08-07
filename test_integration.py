#!/usr/bin/env python3
"""
Test script to verify VTK integration with Qt
Run this to test the segmentation window independently
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow

from frontend_pages.segmentation.segmentation_window import Segmentation

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VTK Integration Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Test paths - update these to match your data
        ct_dir = r"C:/users/avery/Desktop/PI201/DICOM/P0000001/ST000001/SE000003"
        mask_dir = r"C:/users/avery/Desktop/segmentation_masks"

        # Create the segmentation widget
        self.segmentation_widget = Segmentation(ct_dir, mask_dir)
        self.setCentralWidget(self.segmentation_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create and show the test window
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())