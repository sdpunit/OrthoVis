# 🦴 OrthoVis 2.0 - Installation & Setup Guide

Welcome to **OrthoVis 2.0**, a joint motion assessment toolkit for accurate 3D analysis using CT and fluoroscopy data.

---

## 📦 Required Dependencies

Ensure the following Python packages are installed:

- `PySide6`
- `SimpleITK`
- `os` *(built-in)*
- `pickle` *(built-in)*

---

## 🗂 Project Structure Overview

The **OrthoVis 2.0** project follows a modular and organized directory structure. Each directory is responsible for a specific functionality within the application.

### 📁 `assets/`
Contains SVG diagrams illustrating key workflows such as projection, segmentation, and registration. These are used in documentation and UI tutorials.

### 📁 `classes/`
Core logic and reusable components:
- `singleton.py`: Implements `SingletonPatient`, a singleton object managing user/project state.
- `states.py`: Defines `Context` and `State` classes for UI flow management.
- `lib.py`: Common utility functions.

### 📁 `frontend_pages/`
Main application pages built with PySide6:
- `startup/`: Home screen (e.g. `startup_window.py`)
- `new_project/`: UI and logic for importing CT & Fluoroscopy data
- `segmentation/`: Image segmentation interface  
Each folder contains `.ui` (Qt Designer), `ui_*.py` (generated), and functional `.py` files.

### 📁 `widgets/`
Reusable subcomponents, like:
- `sidebar/`: Sidebar navigation widget with its own `.ui` and `.py`.

### 📁 `seg/`
CT segmentation and 3D data processing scripts:
- `ct-seg-backend.ipynb`: Jupyter notebook for testing segmentation logic
- `renderer.py`, `renderer2.py`, `totalseg.py`: CT rendering and segmentation algorithms

### 📄 `main_window.py` / `main.py`
Entry points of the application.
- `main_window.py`: Controls page logic and stack view with `QStackedWidget`.

### 📄 `README.md`
Top-level file describing the project and how to use it.

---

## 🛠 Installation Steps

1.Ensure you are using Python 3.10 or compatible version.
2.Create and activate a virtual environment (recommended):
   ```bash
   python -m venv ortho_env
   source ortho_env/bin/activate  # On Windows use `ortho_env\Scripts\activate`
   ```
3.Install required dependencies:
   ```bash
   pip install PySide6 SimpleITK
   ```
4.Run the main application script, e.g.:
   ```bash
   python main_window.py
   ```
---

# 🌐 Project landing page

https://orthovis2.wixsite.com/orthovis-2
