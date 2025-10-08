# edge_map.py
# pip install SimpleITK nibabel scikit-image imageio

from __future__ import annotations
import numpy as np
import SimpleITK as sitk
from pathlib import Path
from skimage import filters, feature, morphology, exposure
import imageio.v2 as iio


def generate_edge_map_np(
    dicom_dir: str,
    mask_path: str,
    *,
    view: str = "sagittal",                 # 'sagittal' | 'coronal' | 'axial'
    rx_deg: float = 0.0,                    # out-of-plane rotate about X (deg)
    ry_deg: float = 0.0,                    # out-of-plane rotate about Y (deg)
    rz_deg: float = 0.0,                    # in-plane rotate about Z (deg)
    use_gradient_projection: bool = True,   # richer internal detail
    clamp_hu: tuple[float, float] = (200.0, 2000.0),
    pre_smooth_sigma: float = 0.8,          # Gaussian before Canny
    canny_sigma: float = 1.6,               # Canny blur
    canny_perc_lo: float = 60,              # hysteresis lo-threshold (% of grad mag)
    canny_perc_hi: float = 90,              # hysteresis hi-threshold
    clahe: bool = False,                    # local contrast boost
) -> np.ndarray:
    """
    Build a 2D edge map (binary numpy array HxW) by orthographic projection
    of CT intensities gated by a bone mask. Optional rx/ry/rz are applied in 3D
    (mask space) before flattening, so calling again with different angles
    re-computes the projection correctly.

    Returns:
        edge_bin: np.ndarray[bool] of shape (H, W)
    """
    # ---- 1) DICOM CT ----
    series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(dicom_dir)
    if not series_ids:
        raise RuntimeError(f"No DICOM series found in {dicom_dir}")
    files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(dicom_dir, series_ids[0])
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(files)
    ct_img = reader.Execute()  # HU with slope/intercept applied

    # ---- 2) Mask ----
    mask_img = sitk.ReadImage(mask_path)

    # ---- 3) Resample CT into mask space ----
    resample_to_mask = sitk.ResampleImageFilter()
    resample_to_mask.SetReferenceImage(mask_img)
    resample_to_mask.SetInterpolator(sitk.sitkLinear)
    resample_to_mask.SetTransform(sitk.Transform())
    ct_on_mask = resample_to_mask.Execute(ct_img)

    mask_bin = sitk.Cast(mask_img > 0.5, sitk.sitkUInt8)

    # ---- 4) Optional 3D rotations (about mask centre) ----
    if abs(rx_deg) > 1e-6 or abs(ry_deg) > 1e-6 or abs(rz_deg) > 1e-6:
        euler = sitk.Euler3DTransform()
        size  = mask_img.GetSize()
        sp    = mask_img.GetSpacing()
        org   = mask_img.GetOrigin()
        cx = org[0] + sp[0] * (size[0]-1)/2.0
        cy = org[1] + sp[1] * (size[1]-1)/2.0
        cz = org[2] + sp[2] * (size[2]-1)/2.0
        euler.SetCenter((cx, cy, cz))
        euler.SetRotation(np.deg2rad(rx_deg), np.deg2rad(ry_deg), np.deg2rad(rz_deg))

        # Resample CT
        r_ct = sitk.ResampleImageFilter()
        r_ct.SetReferenceImage(mask_img)
        r_ct.SetInterpolator(sitk.sitkLinear)
        r_ct.SetTransform(euler)
        ct_on_mask = r_ct.Execute(ct_on_mask)

        # Resample mask
        r_mk = sitk.ResampleImageFilter()
        r_mk.SetReferenceImage(mask_img)
        r_mk.SetInterpolator(sitk.sitkNearestNeighbor)
        r_mk.SetTransform(euler)
        mask_bin = sitk.Cast(r_mk.Execute(mask_bin), sitk.sitkUInt8)

    # ---- 5) Gate CT by mask + window to bone ----
    lo, hi = clamp_hu
    ct_masked = sitk.Mask(ct_on_mask, mask_bin)
    ct_win = sitk.Clamp(ct_masked, sitk.sitkFloat32, lowerBound=float(lo), upperBound=float(hi))
    ct_win = (ct_win - float(lo)) / max(1e-6, float(hi-lo))

    ct_np = sitk.GetArrayFromImage(ct_win).astype(np.float32)  # [Z, Y, X]

    # ---- 6) Pick volume for projection ----
    if use_gradient_projection:
        ct_raw_np = sitk.GetArrayFromImage(sitk.Mask(ct_on_mask, mask_bin)).astype(np.float32)
        gx = np.gradient(ct_raw_np, axis=2)
        gy = np.gradient(ct_raw_np, axis=1)
        gz = np.gradient(ct_raw_np, axis=0)
        vol_for_proj = np.sqrt(gx*gx + gy*gy + gz*gz).astype(np.float32)
    else:
        vol_for_proj = ct_np

    # ---- 7) Orthographic projection (sum) ----
    v = view.lower()
    if v == "sagittal":
        proj = vol_for_proj.sum(axis=2).transpose(1, 0)   # (Y, Z)
    elif v == "coronal":
        proj = vol_for_proj.sum(axis=1).transpose(1, 0)   # (X, Z)
    elif v == "axial":
        proj = vol_for_proj.sum(axis=0)                    # (Y, X)
    else:
        raise ValueError("view must be 'sagittal', 'coronal', or 'axial'")

    proj -= proj.min()
    if proj.max() > 0: proj /= proj.max()

    # ---- 8) Canny edges (rich detail defaults) ----
    P = filters.gaussian(proj, sigma=pre_smooth_sigma, preserve_range=True)
    if clahe:
        P = exposure.equalize_adapthist(P, clip_limit=0.01)

    gmag = filters.sobel(P)
    lo_thr = np.percentile(gmag, canny_perc_lo)
    hi_thr = np.percentile(gmag, canny_perc_hi)

    edges = feature.canny(P, sigma=canny_sigma, low_threshold=lo_thr, high_threshold=hi_thr)
    edges = morphology.remove_small_objects(edges, min_size=16, connectivity=2)
    edges = morphology.thin(edges)

    return edges  # bool HxW


def save_edge_map_png(edge_bin: np.ndarray, path: str | Path) -> str:
    """Save a binary edge map (0/255 PNG)."""
    path = str(Path(path))
    if not path.lower().endswith(".png"):
        path += ".png"
    iio.imwrite(path, (edge_bin.astype(np.uint8) * 255))
    return path