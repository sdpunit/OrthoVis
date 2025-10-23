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

![Project Structure](assets/project_structure.png)

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
- `embedding.py`: integration of VTK visualisation widget with frontend
- `renderer.py`: (archived) standalone testing of VTK visualisation widget

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


## User Guide 

Below we will present a visual walkthrough of OrthoVis, from setup of project to the registration module.

### Module 1: Project Setup

#### Purpose

The Project Setup module allows users to create or adjust project details (name and description) and import medical imaging data (CT scans and fluoroscopy sequences).

---

#### How It Works

- Users can create a new project or open an existing one.
- Project details can be edited as needed.
- CT and fluoroscopy data can be imported from DICOM files and can be removed if necessary.
- The project details is saved in a structured format for later use in subsequent modules.
- Imported files are saved in a dedicated project folder.

---

#### Workflow

![Project Setup Workflow](assets/project_setup.gif)

**For new projects:**

1. Click "New Project" from the Homepage
2. Enter project name and description
3. Click "Import CT Data" to select and load a folder of DICOM files for the CT scan
4. Click "Import Fluoroscopy Data" to select and load a folder of DICOM files for the fluoroscopy sequence
5. Click "Save" to proceed to the Segmentation module

**For existing projects:**

1. Click "Open Project" from the Homepage
2. Edit any project details as needed
3. Click "Save" to proceed to the Segmentation module

### Module 2a: Segmentation (Browse mode, pre-segmentation)

### Module 2b: Segmentation (Edit/Browse mode, post-segmentation)

### Module 3: Calibration

#### Purpose

The Calibration module is designed to provide accurate geometric correction for fluoroscopy and X-ray images using an AutoAlign grid-based method. It aims to eliminate image distortion caused by projection

---

#### How It Works

There’s a section in this paper that might be really helpful to understand the technicality - https://onlinelibrary.wiley.com/doi/full/10.1002/jor.21003. But to explain this in simpler words – Flouro images are warped, the way the beams land on an object creates distortion (which means a cube isn’t a proper cube anymore). So we need to fix this distortion, and the way we do that is by taking a fluoroscopy shot of a calibration cube (or square grid) with beads placed on it in the front (red beads) and back (blue beads). You detect where those beads land in the distorted image and fit a mapping (an overlay grid) that pulls them back to their true evenly spaced positions. This mapping/corrected distance is then used to apply to every frame of your flouro to undistort it and use is correctly for the purposes of projection.

---

#### Overview

We have completed the development of the network-based calibration model, which accurately performs bead detection, manual verification, and layer-by-layer alignment.
***However, the 3D reconstruction has not been integrated into the Calibration GUI page in OrthoVis yet.***
All current progress and working functions are contained within the Draft.py interface under the class file, which serves as the current prototype of the calibration module.
The following content only describes the work we have completed.

---

#### How to Run

To run the Calibration module independently, use the following command in your terminal:

```bash
python3 Draft.py --dcm <path_to_dicom> [--outdir out]
```

| Argument         | Description                              | Default        |
| ---------------- | ---------------------------------------- | -------------- |
| `--dcm`          | Path to input DICOM file                 | **(Required)** |
| `--outdir`       | Output directory                         | `out`          |
| `--bead-mm`      | Distance between beads in one layer (mm) | `20.0`         |
| `--face-mm`      | Distance between layers (mm)             | `200.0`        |
| `--plane-offset` | Offset between layers (in grid units)    | `"0.5,0.5"`    |

for example:

```bash
python3 Draft.py --dcm Data/DICOM/P0000001/ST000002/SE000003/IN000001
```

During execution, a Matplotlib window appears for interactive adjustment.

🖱 Mouse Controls (Point Addition Stage)

Left click: Add a new point.

If near a candidate (< snap_dist), it will snap automatically.

Enter / Right click: End point addition and continue to merge window and you can operate by keyboard.

⌨️ Keyboard Controls (Alignment Stage)

| Key       | Action                                        |
| --------- | --------------------------------------------- |
| `← ↑ ↓ →` | Translate model (use **Shift** for ×5 speed). |
| `A / D`   | Rotate counterclockwise / clockwise.          |
| `- / =`   | Scale down / up.                              |
| `Enter`   | Confirm current layer and continue.           |
| `Esc / Q` | Exit current layer.                           |

🔵 Color Legend

| Color     | Meaning                                     |
| --------- | ------------------------------------------- |
| 🔴 Red    | Observed points (detected + manually added) |
| 🟡 Yellow | Previous layer (display only)               |
| 🔵 Blue   | Current unsnapped model points              |
| 🟢 Green  | Snapped model points                        |

▼ Parameters

| Parameter      | Function                    | Default |
| -------------- | --------------------------- | ------- |
| `attach_px`    | Snapping threshold (pixels) | `5.0`   |
| `detach_px`    | Detach threshold            | `8.0`   |
| `step_move`    | Translation step (pixels)   | `1.0`   |
| `step_rot_deg` | Rotation step (degrees)     | `1.0`   |
| `step_scale`   | Scaling step                | `1.01`  |

---

#### Workflow

1. Run the Draft.py script with the required DICOM path.
2. The Matplotlib interactive window will open.
3. The first stage is point addition:
4. Left-click to add points on detected bead candidates.
5. Right-click or press Enter to finish point addition.
6. The second stage is alignment:
7. Use keyboard controls to adjust the model to fit the observed points.
8. Press Enter to confirm the current layer and proceed to the next.
9. Repeat steps 4-8 for each layer.
10. After completing all layers, the results will be saved in the specified output directory.

---

#### Future Improvements

1. Integrate the interactive window into the PySide6 calibration GUI.
2. Accurate 3D reconstruction of the bead-grid phantom from 2D DICOM images through precise geometric calibration.
3. Testing and Debugging of the complete calibration module within the OrthoVis application.

### Module 4: Define Axes

The Define Axes module has not been completed as of NOV 2025. Users can navigate into and out of the module page using the navigation side-bar.

### Module 5: Registration

#### Purpose

The Registration module aligns 3D CT-derived bone masks with 2D fluoroscopy images. It lets you load medical imaging data and manually adjust alignment in real time using an interactive VTK display.

---

#### How It Works

- The background shows the fluoroscopy frame (DICOM).
- The foreground shows a flattened bone mask (edge map) generated from the CT.
- Adjustments can be made to match the bone outline with the fluoroscopy anatomy.

---

#### Controls

| Action | Function |
|--------|-----------|
| **Left-click + Drag** | Move overlay (X/Y translation) |
| **Mouse Scroll** | Move overlay forward/back (Z translation) |
| **Ctrl + Drag** | Rotate overlay (X/Y out-of-plane and Z spin) |
| **Pose Fields** | Manually enter translation/rotation values |

---

#### Workflow

1. Open the Registration page — the fluoroscopy loads automatically.  
2. Click Load Bone Mask to generate and display the bone edge overlay.  
3. Use mouse or numeric fields to fine-tune alignment.  
4. For out-of-plane rotations (X/Y), the system reprojects the CT volume and recomputes the flattened image.

---

#### Notes

- Out-of-plane rotations may take several seconds while the 3D projection recomputes.  
- The overlay is always drawn on top of the fluoroscopy.  
- The module is incompleted, you may incounter bugs.
- The module is not linked to a registration AI model yet, in it's current state, the user is unable to progress further.


