#! /usr/bin/env python

import numpy as np
import os 
import subprocess
import shutil

# pip install TotalSegmentator 

# Get academic license for TotalSegmentator (needed for task "appendicular_bones") 
# https://backend.totalsegmentator.com/license-academic/

# Set license
# totalseg_set_license -l <your-license-number>

# Download weights of the pre-trained model 
# totalseg_download_weights -t total [femur_left, femur_right]
# totalseg_download_weights -t appendicular_bones [patella, tibia, fibula]

# ROIs to segment - these are the only masks we'll keep
roi = ["femur_right", "fibula", "patella", "tibia"] 

def run_totalseg(ct_dir: str, seg_dir: str): 
    """
    Run TotalSegmentator on CT directory, outputting masks to separate seg_dir.
    Original CT files are never modified.
    
    Args:
        ct_dir: Path to CT directory (DICOM files) - READ ONLY
        seg_dir: Output directory for segmentation masks - WRITE ONLY
    """
    # Ensure output directory exists
    os.makedirs(seg_dir, exist_ok=True)
    
    # Verify input directory exists and is readable
    if not os.path.exists(ct_dir):
        raise FileNotFoundError(f"CT directory not found: {ct_dir}")
    
    print(f"Reading CT from: {ct_dir} (READ ONLY)")
    print(f"Writing masks to: {seg_dir} (WRITE ONLY)")
    
    # TotalSegmentator commands - these only READ from ct_dir, never modify it
    # Note: Cannot combine multiple --ta tasks in single command, must run sequentially
    base_command = f"TotalSegmentator -i \"{ct_dir}\" -o \"{seg_dir}\""
    
    command_total = f"{base_command} --ta total"
    command_appendicular = f"{base_command} --ta appendicular_bones"

    # Run segmentation commands
    print("Running TotalSegmentator (total)...")
    print(f"Command: {command_total}")
    subprocess.run(command_total, shell=True)
    
    print("Running TotalSegmentator (appendicular_bones)...")
    print(f"Command: {command_appendicular}")
    subprocess.run(command_appendicular, shell=True)
    
    # Clean up ONLY in seg_dir - never touch ct_dir
    print("Cleaning up unwanted masks...")
    rois = {f'{bone}.nii.gz' for bone in roi}
    
    for f in os.listdir(seg_dir):
        if f not in rois:
            file_path = os.path.join(seg_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    
    # Verify original CT directory is untouched
    if not os.path.exists(ct_dir):
        raise Exception(f"CRITICAL ERROR: Original CT directory was deleted! {ct_dir}")
    
    print(f"TotalSegmentator completed. Original CT preserved at: {ct_dir}")
    print(f"Masks saved to: {seg_dir}")


import SimpleITK as sitk 
from scipy.ndimage import uniform_filter
from skimage.filters import threshold_otsu

def load_ct(ct_source: str) -> sitk.Image:
    """
    Load a CT volume from either a DICOM series directory or a NIfTI file (.nii / .nii.gz).

    Parameters
        ct_source (str):
            Path to a folder containing a DICOM series, or to a NIfTI file
            (with extension `.nii` or `.nii.gz`).

    Returns:
        sitk.Image: The loaded CT volume as a SimpleITK Image.

    Raises: 
        RuntimeError: If `ct_source` is a directory but no DICOM series can be found in it.
    """
    if os.path.isdir(ct_source):
        reader = sitk.ImageSeriesReader()
        series_ids = reader.GetGDCMSeriesIDs(ct_source)
        if not series_ids:
            raise RuntimeError(f"No DICOM series found in {ct_source}")
        # Pick the first series
        file_names = reader.GetGDCMSeriesFileNames(ct_source, series_ids[0])
        reader.SetFileNames(file_names)
        return reader.Execute()
    else:
        return sitk.ReadImage(ct_source)

# Modify after enhancing contrast with window/level? 
def refine_mask_adaptive_otsu(mask_path: str, ct_path: str, output_path: str,
                               window_size=2, dilation_radius=3, erosion_radius=1, min_component_size=500, gaussian_sigma=2.0):
    """
    Refine segmentation using adaptive thresholding with Otsu-derived HU threshold.
    
    Parameters:
        mask_path (str): Path to segmentation mask
        ct_path (str): Path to CT scan in HU
        output_path (str): Where to save the refined mask
        window_size (int): Size of cube for adaptive mean filter
        erosion_radius (int): Core erosion to preserve center
        min_component_size (int): Minimum voxels to keep in connected components
        gaussian_sigma (float): Sigma for smoothing CT before Otsu
    """

    # --- Load mask and CT ---
    mask = sitk.ReadImage(mask_path)
    print(f"Loading mask from: {mask_path}")

    # Resample CT to mask geometry
    resample = sitk.ResampleImageFilter()
    resample.SetReferenceImage(mask)
    resample.SetInterpolator(sitk.sitkNearestNeighbor)
    ct_aligned = resample.Execute(load_ct(ct_path))

    # Smooth CT to suppress noise before Otsu
    ct_smoothed = sitk.SmoothingRecursiveGaussian(ct_aligned, gaussian_sigma)
    mask_float = sitk.Cast(mask, sitk.sitkFloat32)
    mask_smoothed = sitk.BinaryThreshold(sitk.SmoothingRecursiveGaussian(mask_float, gaussian_sigma),
                                     lowerThreshold=0.5, upperThreshold=1e9,
                                     insideValue=1, outsideValue=0)
    

    # Convert arrays
    ct_np = sitk.GetArrayFromImage(ct_smoothed)
    mask_np = sitk.GetArrayFromImage(mask)

    # --- Step 1: Define shell for Otsu and adaptive filtering ---
    dilated = sitk.BinaryDilate(mask, [dilation_radius]*3)
    dilated_np = sitk.GetArrayFromImage(dilated)

    # Apply Otsu threshold only inside the dilated mask
    ct_in_dilated = ct_np[dilated_np > 0]
    if ct_in_dilated.size < 20:
        print("Insufficient points in bone region for Otsu thresholding: skipping")
        return

    otsu_hu_thresh = threshold_otsu(ct_in_dilated)
    print(f"[Otsu] HU threshold inside boundary: {otsu_hu_thresh:.1f}")

    # --- Step 2: Adaptive local HU filtering ---
    local_mean = uniform_filter(ct_np, size=window_size)
    refined_np = (dilated_np > 0) & (local_mean > otsu_hu_thresh)

    # --- Step 3: Remove speckles ---
    refined_img = sitk.GetImageFromArray(refined_np.astype(np.uint8))
    refined_img.CopyInformation(mask)
    cc = sitk.ConnectedComponent(refined_img)

    label_stats = sitk.LabelShapeStatisticsImageFilter()
    label_stats.Execute(cc)

    cc_np = sitk.GetArrayFromImage(cc)
    cleaned_np = np.zeros_like(refined_np)
    for l in label_stats.GetLabels():
        if label_stats.GetNumberOfPixels(l) > min_component_size:
            cleaned_np[cc_np == l] = 1

    # --- Step 4: Preserve interior core ---
    eroded = sitk.BinaryErode(mask_smoothed, [erosion_radius]*3)
    eroded_np = sitk.GetArrayFromImage(eroded)

    final_combined = np.logical_or(eroded_np, cleaned_np)

    # --- Step 5: Save output ---
    final_img = sitk.GetImageFromArray(final_combined.astype(np.uint8))
    final_img.CopyInformation(mask)
    sitk.WriteImage(final_img, output_path) 

    print(f"Hybrid Otsu-adaptive refined mask saved to: {output_path}")


def run_complete_segmentation(ct_dir: str, seg_dir: str):
    """
    Complete segmentation pipeline: TotalSegmentator + Otsu refinement
    Original CT directory is never modified - only read from.
    
    Args:
        ct_dir: Path to CT directory (READ ONLY)
        seg_dir: Output directory for refined masks (WRITE ONLY)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Segmentation pipeline: {ct_dir} (READ) -> {seg_dir} (WRITE)")
        
        # Verify original CT exists before starting
        if not os.path.exists(ct_dir):
            print(f"ERROR: CT directory not found: {ct_dir}")
            return False
        
        # Step 1: Run TotalSegmentator (only reads from ct_dir)
        run_totalseg(ct_dir, seg_dir)
        
        # Step 2: Apply Otsu refinement (only works in seg_dir)
        print("Applying Otsu refinement...")
        for mask_name in roi:
            original_mask = os.path.join(seg_dir, f"{mask_name}.nii.gz")
            refined_mask = os.path.join(seg_dir, f"{mask_name}_otsu.nii.gz")
            
            if os.path.exists(original_mask):
                # Otsu refinement reads from ct_dir but only writes to seg_dir
                refine_mask_adaptive_otsu(original_mask, ct_dir, refined_mask)
                # Remove only the original mask in seg_dir
                os.remove(original_mask)
        
        # Final verification that original CT is untouched
        if not os.path.exists(ct_dir):
            raise Exception(f"CRITICAL: Original CT directory was deleted: {ct_dir}")
        
        print("Segmentation completed! Original CT files preserved.")
        return True
        
    except Exception as e:
        print(f"Segmentation error: {e}")
        return False


if __name__ == "__main__":
    # Example usage with hardcoded paths
    ct_dir = r"C:/users/avery/Desktop/PI201/DICOM/P0000001/ST000001/SE000003"
    seg_dir = r"C:/users/avery/Desktop/segmentation_masks"
    
    run_complete_segmentation(ct_dir, seg_dir)