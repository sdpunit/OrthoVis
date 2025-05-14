#! /usr/bin/env python

import numpy as np
import os 
import subprocess

# pip install TotalSegmentator 

# Get academic license for TotalSegmentator (needed for task "appendicular_bones") 
# https://backend.totalsegmentator.com/license-academic/

# Set license
# totalseg_set_license -l <your-license-number>

# Download weights of the pre-trained model 
# totalseg_download_weights -t total [femur_left, femur_right]
# totalseg_download_weights -t appendicular_bones [patella, tibia, fibula]

# Input and output directories
ct_dir = "/Users/liruohua/Desktop/OrthoVis/PI201/DICOM/P0000001/ST000001/SE000003"  # Input CT directory 
seg_dir = "/Users/liruohua/Desktop/OrthoVis/segmentation_masks"  # Output segmentation masks directory
roi = ["femur_left", "femur_right", "fibula", "patella", "tibia"] # ROIs 

def run_totalseg(ct_dir: str, seg_dir: str): 
    # TotalSegmentator segmentation 
    # Commands to run segmentations for trained classes 
    command_total = f"TotalSegmentator -i {ct_dir} -o {seg_dir} --ta total" # "total"
    command_appendicular = f"TotalSegmentator -i {ct_dir} -o {seg_dir} --ta appendicular_bones" # "appendicular_bones"

    # Run first command (femurs)
    print("Running segmentation with '--ta total'...")
    result_total = subprocess.run(command_total, shell=True, capture_output=True, text=True)
    if result_total.stderr:
        print("Errors:")
        print(result_total.stderr)
    print("Finished '--ta total' segmentation./n")

    # Run second command (patella, tibia, fibula)
    print("Running segmentation with '--ta appendicular_bones'...")
    result_appendicular = subprocess.run(command_appendicular, shell=True, capture_output=True, text=True)
    if result_appendicular.stderr:
        print("Errors:")
        print(result_appendicular.stderr)
    print("Finished '--ta appendicular_bones' segmentation./n")
    
    for f in os.listdir(seg_dir):
        if f not in [bone + ".nii.gz" for bone in roi]:
            os.remove(f"{seg_dir}/{f}")  
    print(f"TotalSegmentator masks successfully saved to: {seg_dir}")


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


if __name__ == "__main__":
    run_totalseg(ct_dir, seg_dir)
    for m in roi:
        print(f"Post-processing {m} mask...")
        refine_mask_adaptive_otsu(f"{seg_dir}/{m}.nii.gz", ct_dir, f"{seg_dir}/{m}_otsu.nii.gz")
        print(f"Successfully saved refined {m} mask to: {seg_dir}/{m}_otsu.nii.gz")