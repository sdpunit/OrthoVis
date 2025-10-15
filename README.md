# 🦴 OrthoVis 2.0 - Installation & Setup Guide

Welcome to **OrthoVis 2.0**, a joint motion assessment toolkit for accurate 3D analysis using CT and fluoroscopy data.

---

## 📦 Required Dependencies

Ensure the following Python packages are installed:

- `ImageIO`: a Python library to read and write image data
- `Matplotlib`: a plotting library for creating static, animated, and interactive visualizations
- `NumPy`: a fundamental package for scientific computing with Python
- `OpenCV-Python`: Open Source Computer Vision Library
- `Pydicom`: a pure Python package for working with DICOM files
- `PySide6`: Python bindings for the Qt application framework
- `SciPy`: open-source library for scientific and technical computing
- `SimpleITK`: open-source library designed for multi-dimensional image analysis
- `Scikit-Image`: library designed for image processing and computer vision tasks
- `TotalSegmentator`: a tool for automated medical image segmentation (you will need to get your own license key for this dependency [here](https://backend.totalsegmentator.com/license-academic/))
- `VTK`: Visualization Toolkit for 3D computer graphics, image processing, and visualization

These dependencies can be found in the `requirements.txt` file and versions are not specififed to let pip install the latest compatible versions.

---

## 🗂 Project Structure Overview

The **OrthoVis 2.0** project follows a modular and organized directory structure. Each directory is responsible for a specific functionality within the application.

### 📁 `assets/`

Contains SVG diagrams illustrating key workflows in documentation such as projection, segmentation, and registration, and images used in the UI.

### 📁 `classes/`

Core logic and reusable components:
- `objects.py`: Implements `Singleton`, `State` design pattern and other useful data structures.
- `lib.py`: Common utility functions.
- `utils.py`: Helper functions for dialog boxes, file handling, etc.

### 📁 `frontend_pages/`

Main application frontend pages built with PySide6:

- `startup/`: Home screen (e.g. `startup_window.py`)
- `project_setup/`: UI and logic for project description and importing CT & Fluoroscopy data
- `segmentation/`: Image segmentation interface  
- `calibration/`: Fluoroscopy calibration interface
- `registration/`: 2D-3D registration interface
- `define_axis/`: Define axes interface
- `visualisation/`: 3D visualization - final output interface
  
Each folder contains `.ui` (Qt Designer), `ui_*.py` (generated), and functional `.py` files.

### 📁 `widgets/`

Reusable subcomponents for consistent UI across pages:
- `sidebar/`: Sidebar navigation widget     
- `titlebar/`: Title bar widget
 
Each folder contains `.ui` (Qt Designer), `ui_*.py` (generated), and functional `.py` files.

### 📁 `seg/`

CT segmentation and 3D data processing scripts:
- `totalseg.py`: fully automated CT segmentation using TotalSegmentator 
- `renderer.py`: CT rendering

### 📁 `Projects/`

Stores data of existing projects in subfolders.

### 📁 `Test/`

Contains unit tests for the application.

### 📄 `main_window.py` / `main.py`

Entry points of the application.
- `main_window.py`: Controls page logic and stack view with `QStackedWidget`.
- `main.py`: Initializes and runs the application.

### 📄 `README.Docker`

Instructions for building and deploying the application using Docker.

### 📄 `README.md`

Top-level file describing the project and how to install and use it.

### 📄 `requirements.txt`

Lists all required Python packages for easy installation via pip.

---

## 🛠 Installation Steps

1. Ensure you are using compatible version of Python.

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv ortho_env
   source ortho_env/bin/activate
   # On Windows use `ortho_env\Scripts\activate`
   ```
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt # Add --user if not using a virtual environment to avoid permission issues
   ```
4. Run the main application using the `Run` configuration in your IDE or execute:
   ```bash
   python main_window.py
   ```
---

- For documentation, minutes, and software engineering practices, please refer to our [Wiki](https://github.com/sdpunit/OrthoVis/wiki).


- Please look at our [Project landing page](https://orthovis2.wixsite.com/orthovis-2) to learn more about the project and our team members. 