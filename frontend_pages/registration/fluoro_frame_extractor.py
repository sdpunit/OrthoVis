'''
This program takes a single fluoroscopy and extracts each frame, saving each frame to the local directory given. Accepts either a DICOM file or a folder containing one.
'''

import pydicom
import numpy as np
from PIL import Image
import os
import glob
import argparse

def normalize_frame(frame_data, ds):
    """Normalize DICOM frame pixel data to 0–255 for display/saving."""
    slope = float(getattr(ds, "RescaleSlope", 1.0))
    intercept = float(getattr(ds, "RescaleIntercept", 0.0))
    frame = frame_data.astype(np.float32) * slope + intercept

    wc = getattr(ds, "WindowCenter", None)
    ww = getattr(ds, "WindowWidth", None)
    if wc is not None and ww is not None:
        try:
            wc = float(wc[0]) if hasattr(wc, "__getitem__") else float(wc)
            ww = float(ww[0]) if hasattr(ww, "__getitem__") else float(ww)
            low, high = wc - ww / 2, wc + ww / 2
            frame = np.clip(frame, low, high)
        except Exception:
            pass

    min_val, max_val = np.min(frame), np.max(frame)
    if max_val > min_val:
        frame = (frame - min_val) / (max_val - min_val) * 255.0
    else:
        frame[:] = 0
    return frame.astype(np.uint8)


def _resolve_dicom_path(file_path: str) -> str:
    """Return a usable DICOM file path whether input is a file or a folder (no extension required)."""
    def is_dicom(p: str) -> bool:
        try:
            # lightweight header check; avoids reading pixel data
            return pydicom.misc.is_dicom(p)
        except Exception:
            return False

    if os.path.isdir(file_path):
        # look only in this folder first
        for name in sorted(os.listdir(file_path)):
            p = os.path.join(file_path, name)
            if os.path.isfile(p) and is_dicom(p):
                print(f"Using DICOM file: {p}")
                return p
        # optional: one-level recursive fallback (comment out if you don't want it)
        for root, _, files in os.walk(file_path):
            for name in sorted(files):
                p = os.path.join(root, name)
                if os.path.isfile(p) and is_dicom(p):
                    print(f"Using DICOM file: {p}")
                    return p
        raise FileNotFoundError(f"No DICOM files found in folder: {file_path}")

    # path is a file
    if not is_dicom(file_path):
        raise FileNotFoundError(f"Not a valid DICOM file: {file_path}")
    return file_path


def extract_dicom_frames(file_path, output_dir="extracted_frames", image_format="png"):
    """
    Extract frames from a DICOM fluoroscopy file or folder.
    Args:
        file_path (str): Path to the DICOM file OR a folder containing one
        output_dir (str): Directory to save extracted frames
        image_format (str): Output image format ('png', 'jpg', 'tiff')
    Returns:
        tuple: (number_of_frames, list_of_frame_arrays)
    """
    # Resolve file if folder
    dicom_file = _resolve_dicom_path(file_path)

    # Read the DICOM file
    try:
        ds = pydicom.dcmread(dicom_file)
        print(f"Successfully loaded DICOM file: {dicom_file}")
        print(f"Modality: {ds.get('Modality', 'Unknown')}")
        print(f"Study Description: {ds.get('StudyDescription', 'Unknown')}")
    except Exception as e:
        print(f"Error reading DICOM file: {e}")
        return 0, []

    os.makedirs(output_dir, exist_ok=True)

    pixel_array = ds.pixel_array
    print(f"Pixel array shape: {pixel_array.shape}")

    if len(pixel_array.shape) == 3:
        num_frames = pixel_array.shape[0]
        height, width = pixel_array.shape[1], pixel_array.shape[2]
    elif len(pixel_array.shape) == 4:
        num_frames = pixel_array.shape[0]
        height, width = pixel_array.shape[1], pixel_array.shape[2]
    else:
        num_frames = 1
        height, width = pixel_array.shape[0], pixel_array.shape[1]

    print(f"Number of frames detected: {num_frames}")
    print(f"Frame dimensions: {height} x {width}")
    frame_arrays = []

    for frame_idx in range(num_frames):
        frame_data = pixel_array[frame_idx] if num_frames > 1 else pixel_array
        frame_normalized = normalize_frame(frame_data, ds)
        frame_arrays.append(frame_normalized)

        if len(frame_normalized.shape) == 2:
            img = Image.fromarray(frame_normalized, mode='L')
        else:
            img = Image.fromarray(frame_normalized)

        frame_filename = f"frame_{frame_idx:04d}.{image_format}"
        frame_path = os.path.join(output_dir, frame_filename)
        img.save(frame_path)

        if frame_idx < 5 or frame_idx % 10 == 0:
            print(f"Saved frame {frame_idx + 1}/{num_frames}: {frame_filename}")

    print(f"\nExtraction complete! {num_frames} frames saved to '{output_dir}'")
    return num_frames, frame_arrays