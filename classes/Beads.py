#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strict-compatible Fluoro Calibration (旧版兼容模式)
- S=512 的标定平面
- 7x7x2 网格, 按旧版把 mm -> px 用: px = mm / (2 * ImagerPixelSpacing)
- 旧版投影: u = d1/(d2+Z)*(X - yc) + yc; v = d1/(d2+Z)*(Y - xc) + xc
- 半吸附: 阈值 -> 最大连通域 -> 质心
- 畸变: 三次多项式 (9 基)
- 输出: dist_data.mat (bpx/bpy/gpx/gpy in 512px coords), dist_coeff.mat (ax/ay)
"""

import argparse, os
import numpy as np
import pydicom
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy import ndimage
from scipy.optimize import least_squares
import cv2
import math
from numpy.linalg import svd

# -------------------------
# 旧版常量 & 标定平面
# -------------------------
S = 512
XC = 256.0
YC = 256.0
D1 = 2019.0
D2 = 1119.0

def apply_similarity_uv(uv, scale=1.0, theta_deg=0.0, tx=0.0, ty=0.0, center=(256.0, 256.0)):
    """
    对 2D 网格 uv 应用相似变换（等比缩放 + 旋转 + 平移）
    uv: (N,2)
    scale: 尺度 >0
    theta_deg: 旋转角度(度，逆时针)
    tx,ty: 平移（像素，512坐标系）
    center: 围绕此中心旋转/缩放
    """
    uv = np.asarray(uv, dtype=float)
    c = np.asarray(center, dtype=float)
    th = math.radians(theta_deg)
    R = np.array([[math.cos(th), -math.sin(th)],
                  [math.sin(th),  math.cos(th)]], dtype=float)
    return ( (uv - c) @ R.T ) * scale + c + np.array([tx, ty])

def interactive_adjust_grid(img512, uv_init, center=(256.0,256.0),
                            step_move=5.0, step_rot_deg=1.0, step_scale=1.01):
    """
    键盘交互调整 grid：
      ← → ↑ ↓ : 平移
      A / D   : 旋转 -/+ (1°)
      - / =   : 缩小/放大 (×1.01)
      SHIFT   : 加速（步长×5）
      R       : 重置
      ENTER   : 确认并返回
      ESC/Q   : 放弃并返回原始 uv
      H       : 显示/隐藏帮助
    """
    params = dict(scale=1.0, theta=0.0, tx=0.0, ty=0.0)
    uv0 = np.array(uv_init, dtype=float)
    uv  = apply_similarity_uv(uv0, **params, center=center)

    fig, ax = plt.subplots()
    ax.imshow(img512, cmap="gray")
    scat = ax.scatter(uv[:,0], uv[:,1], c="b", s=12, label="grid (adjust)")
    ax.set_title("Adjust grid: ←↑→↓ move, A/D rotate, -/= scale, R reset, H help, Enter done")
    ax.legend(loc="upper right")
    txt = ax.text(5, 10, "", color="w", va="top", ha="left")

    help_visible = False
    def render():
        uv_show = apply_similarity_uv(uv0, **params, center=center)
        scat.set_offsets(uv_show)
        txt.set_text(
            f"tx={params['tx']:.1f}, ty={params['ty']:.1f}, "
            f"θ={params['theta']:.1f}°, s={params['scale']:.4f}"
            + ("\n←↑→↓ move, A/D rotate, -/= scale, R reset, Enter OK, ESC cancel" if help_visible else "")
        )
        fig.canvas.draw_idle()

    done, canceled = [False], [False]

    def on_key(e):
        nonlocal help_visible
        if e.inaxes is not ax and e.key is None:
            return
        k = (e.key or "").lower()
        accel = 5.0 if (("shift" in (e.key or "")) or (e.key in ("shift",))) else 1.0
        moved = False
        if k in ("left",):
            params["tx"] -= step_move*accel; moved=True
        elif k in ("right",):
            params["tx"] += step_move*accel; moved=True
        elif k in ("up",):
            params["ty"] -= step_move*accel; moved=True
        elif k in ("down",):
            params["ty"] += step_move*accel; moved=True
        elif k in ("a",):
            params["theta"] -= step_rot_deg*accel; moved=True
        elif k in ("d",):
            params["theta"] += step_rot_deg*accel; moved=True
        elif k in ("-", "minus"):
            params["scale"] /= (step_scale**accel); moved=True
        elif k in ("=", "+"):
            params["scale"] *= (step_scale**accel); moved=True
        elif k in ("r",):
            params.update(scale=1.0, theta=0.0, tx=0.0, ty=0.0); moved=True
        elif k in ("enter", "return"):
            done[0] = True; plt.close(fig)
        elif k in ("escape", "esc", "q"):
            canceled[0] = True; plt.close(fig)
        elif k in ("h",):
            help_visible = not help_visible; moved=True
        if moved:
            render()

    cid = fig.canvas.mpl_connect("key_press_event", on_key)
    render()
    plt.show()
    fig.canvas.mpl_disconnect(cid)

    if canceled[0]:
        return uv0, dict(scale=1.0, theta=0.0, tx=0.0, ty=0.0)
    return apply_similarity_uv(uv0, **params, center=center), params
def collect_points_with_snap(ax, img512, snap_fn, stop_keys=("enter","return","escape")):
    """
    左键：添加并吸附；右键/中键或按 Enter/Return/Escape：结束
    实时在图上显示 red(原点击) / yellow(吸附后)
    """
    clicked, snapped = [], []
    scat_click, = ax.plot([], [], 'r+', ms=10, label='clicks')
    scat_snap,  = ax.plot([], [], 'yx', ms=7,  label='snapped')

    def on_click(event):
        if event.inaxes != ax:
            return
        if event.button == 1:  # 左键：点一下并吸附
            x, y = float(event.xdata), float(event.ydata)
            sx, sy = snap_fn(img512, x, y, window=60)
            clicked.append((x, y))
            snapped.append((sx, sy))
            scat_click.set_data([c[0] for c in clicked], [c[1] for c in clicked])
            scat_snap.set_data([s[0] for s in snapped], [s[1] for s in snapped])
            ax.figure.canvas.draw_idle()
        elif event.button in (2, 3):  # 中/右键：结束
            plt.close(ax.figure)

    def on_key(event):
        if event.key and event.key.lower() in stop_keys:
            plt.close(ax.figure)

    fig = ax.figure
    cid1 = fig.canvas.mpl_connect('button_press_event', on_click)
    cid2 = fig.canvas.mpl_connect('key_press_event', on_key)
    ax.legend(loc="upper right")
    plt.show()
    fig.canvas.mpl_disconnect(cid1)
    fig.canvas.mpl_disconnect(cid2)

    if len(snapped) == 0:
        return np.empty((0,2)), np.empty((0,2))
    return np.array(clicked, dtype=float), np.array(snapped, dtype=float)
def detect_beads_centroids(img512, thr=None):
    """在整幅512图里粗检亮珠点，返回 Nx2 像素坐标（u,v）"""
    im = cv2.normalize(img512, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    im = cv2.GaussianBlur(im, (5,5), 0)
    # 自动阈值或固定阈值
    if thr is None:
        _, mask = cv2.threshold(im, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    else:
        _, mask = cv2.threshold(im, thr, 255, cv2.THRESH_BINARY)
    # 去小噪点
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
    num, labels, stats, cents = cv2.connectedComponentsWithStats(mask)
    # 过滤面积太小/太大
    keep = []
    for i in range(1, num):
        area = stats[i, cv2.CC_STAT_AREA]
        if 3 <= area <= 200:   # 视图像而定，可调
            keep.append(cents[i])
    if not keep:
        return np.empty((0,2), np.float32)
    return np.array(keep, dtype=np.float32)  # (N,2) -> (x=u, y=v)

def procrustes_similarity(X, Y):
    """
    用 Procrustes/SVD 拟合 2D 相似变换，使 X * sR + t ≈ Y
    X,Y: (N,2)
    返回 s(缩放), R(2x2旋转), t(2,)
    """
    Xc = X - X.mean(axis=0, keepdims=True)
    Yc = Y - Y.mean(axis=0, keepdims=True)
    U, Svals, Vt = svd(Xc.T @ Yc)
    R = U @ Vt
    if np.linalg.det(R) < 0:  # 反射修正
        U[:, -1] *= -1
        R = U @ Vt
    scale = (Svals.sum() / (Xc**2).sum())
    t = Y.mean(axis=0) - X.mean(axis=0) @ (scale * R)
    return scale, R, t
# -------------------------
# 7x7x2 网格 (旧版 mm->px 转换)
# -------------------------
def build_grid_px(f_pix_mm, bead_mm=20.0, face_mm=200.0):
    """
    f_pix_mm: ImagerPixelSpacing (mm/pixel)
    旧版将 mm -> px 时除以 (2 * f_pix)，和 Calibrate_Fluoro.m 一致
    """
    bead_px = bead_mm / (2.0 * f_pix_mm)
    face_px = face_mm / (2.0 * f_pix_mm)

    # 两层: Z=0 和 Z=face_px，中心在 (XC,YC)
    coords3d = []
    for z in [0.0, face_px]:
        for j in range(-3, 4):     # Y 方向
            for i in range(-3, 4): # X 方向
                X = XC + i * bead_px
                Y = YC + j * bead_px
                # 旧版使用圆板，可选内切筛选；这里保留全部 49*2=98 点（兼容性最好）
                coords3d.append([X, Y, z])
    return np.array(coords3d, dtype=np.float64)  # (98,3)

# -------------------------
# 旧版投影 (apply_perspective_calibrate)
# -------------------------
def apply_perspective_calibrate(XYZ, d1=D1, d2=D2, xc=XC, yc=YC):
    """
    注意旧版坐标轴: 用 yc 与 X, 用 xc 与 Y 交叉 (确实如此)
    XYZ: (N,3) in 'px', Z in px-depth
    返回 uv: (N,2) in 'px' on 512x512 plane
    """
    X = XYZ[:, 0]; Y = XYZ[:, 1]; Z = XYZ[:, 2]
    scale = d1 / (d2 + Z)
    u = scale * (X - yc) + yc
    v = scale * (Y - xc) + xc
    return np.stack([u, v], axis=1)

# -------------------------
# 半吸附 (阈值 -> 最大连通域 -> 质心)
# -------------------------
def snap_to_bead(img512, x, y, window=40):
    H, W = img512.shape
    x0, x1 = int(max(0, x-window)), int(min(W, x+window))
    y0, y1 = int(max(0, y-window)), int(min(H, y+window))
    roi = img512[y0:y1, x0:x1]
    if roi.size == 0:
        return x, y

    roi_norm = cv2.normalize(roi, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    roi_blur = cv2.GaussianBlur(roi_norm, (5,5), 0)
    # 珠点为亮, 使用 Otsu
    _, mask = cv2.threshold(roi_blur, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    if num_labels <= 1:
        return x, y
    # 取最大连通域(去背景)
    largest_idx = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    cx, cy = centroids[largest_idx]
    return x0 + cx, y0 + cy

# -------------------------
# 多项式畸变拟合 (与旧版一致的9基)
# -------------------------
def poly_features(u, v):
    x = u - S/2.0
    y = v - S/2.0
    Xv = np.stack([x, y, x**2, x*y, y**2, x**3, (x**2)*y, x*(y**2), y**3], axis=1)
    Yv = np.stack([y, x, y**2, y*x, x**2, y**3, (y**2)*x, y*(x**2), x**3], axis=1)
    return Xv, Yv

def fit_distortion(u_obs, v_obs, u_proj, v_proj):
    Xv, Yv = poly_features(u_obs, v_obs)
    du = (u_proj - u_obs)
    dv = (v_proj - v_obs)
    ax, _, _, _ = np.linalg.lstsq(Xv, du, rcond=None)
    ay, _, _, _ = np.linalg.lstsq(Yv, dv, rcond=None)
    return ax.astype(np.float64), ay.astype(np.float64)

# -------------------------
# 可选: 距离场目标(与旧版思路一致，但默认用最小二乘)
# -------------------------
def distance_field(img512):
    # 将亮珠点变成前景(255), 取其距离变换
    im = cv2.normalize(img512, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, mask = cv2.threshold(im, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    inv = 255 - mask  # 珠点为黑，背景白，计算到黑的距离
    dist = cv2.distanceTransform(inv, distanceType=cv2.DIST_L2, maskSize=3)
    return dist

# -------------------------
# 主流程
# -------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dcm", required=True, help="DICOM 文件路径 (原图大小可为 1024)")
    ap.add_argument("--outdir", default=".", help="输出目录")
    ap.add_argument("--use-dfield", action="store_true", help="使用距离场目标(实验特性)")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # 读 DICOM 原图
    ds = pydicom.dcmread(args.dcm)
    img = ds.pixel_array.astype(np.float32)
    H0, W0 = img.shape

    # 缩放到 512 (旧版标定平面)
    img512 = cv2.resize(img, (S, S), interpolation=cv2.INTER_AREA)
    scale_to_512 = S / float(W0)  # 1024->512 的比例（假设正方形）

    # 读取像素尺寸 (mm/pixel)
    if "ImagerPixelSpacing" in ds:
        f_pix_mm = float(ds.ImagerPixelSpacing[0])
    else:
        raise RuntimeError("DICOM 缺少 ImagerPixelSpacing，无法按旧版换算 mm->px")

    # 生成 3D 网格 (单位: 'px on 512 plane')
    XYZ = build_grid_px(f_pix_mm=f_pix_mm)

    # 初始投影 (旧版投影公式)
    uv0 = apply_perspective_calibrate(XYZ)  # (N,2), on 512 plane
    # —— 自动预对齐（让初始化蓝点几乎贴住白点）——
    cand = detect_beads_centroids(img512)  # (M,2)
    if cand.shape[0] >= 30:  # 足够多的候选珠点
        # 用所有 uv0 与 cand 做粗配准（Procrustes相似变换）
        # 为了鲁棒，你也可以用最近邻下采样或RANSAC；这里直接全局拟合就够稳
        # 先把 cand 的数量与 uv0 对齐（按中心优先采样）
        k = min(len(uv0), len(cand))
        # 取 cand 中最靠近图中心的 k 个点
        center = np.array([[S / 2, S / 2]])
        d = np.linalg.norm(cand - center, axis=1)
        idx = np.argsort(d)[:k]
        cand_k = cand[idx]

        # 同样取 uv0 中最靠近中心的 k 个点
        d0 = np.linalg.norm(uv0 - center, axis=1)
        idx0 = np.argsort(d0)[:k]
        uv0_k = uv0[idx0]

        s, R2, t = procrustes_similarity(uv0_k, cand_k)
        # 应用到整个 uv0（仅做显示初始化的相似变换，不改变投影模型参数）
        uv0 = (uv0 @ (s * R2)) + t
    # 显示初始网格并点击(半吸附)
    plt.figure()
    fig, ax = plt.subplots()
    ax.imshow(img512, cmap="gray")
    ax.scatter(uv0[:, 0], uv0[:, 1], c="b", s=12, label="init grid")
    ax.set_title("Click near beads (左键=添加并吸附，右键/Enter=结束)")
    clicked, snapped = collect_points_with_snap(ax, img512, snap_to_bead)
    # snapped 就是吸附后的点
    bpx, bpy = snapped[:, 0], snapped[:, 1]
    plt.close(fig)

    # 与 uv 的对应关系：按点击数量截断
    N = min(len(bpx), uv0.shape[0])
    if N < 9:
        print("⚠️ 点的数量太少(<9)，只能保存原始点击，不做畸变拟合。")
        sio.savemat(os.path.join(args.outdir, "dist_data.mat"),
                    {"bpx": bpx, "bpy": bpy, "gpx": uv0[:N,0], "gpy": uv0[:N,1]})
        return

    u_obs, v_obs = bpx[:N], bpy[:N]
    u_mod, v_mod = uv0[:N,0], uv0[:N,1]

    # 非线性微调 d1,d2（可选小范围）以最小化 reprojection（严格旧版可固定不调）
    def resid(params):
        d1, d2 = params
        uv = apply_perspective_calibrate(XYZ[:N], d1=d1, d2=d2, xc=XC, yc=YC)
        return np.hypot(uv[:,0]-u_obs, uv[:,1]-v_obs)
    try:
        res = least_squares(lambda p: resid(p), x0=np.array([D1, D2]),
                            bounds=([D1-200, D2-200], [D1+200, D2+200]), verbose=0)
        d1_opt, d2_opt = float(res.x[0]), float(res.x[1])
    except Exception:
        d1_opt, d2_opt = D1, D2

    uv_opt = apply_perspective_calibrate(XYZ[:N], d1=d1_opt, d2=d2_opt, xc=XC, yc=YC)

    # 畸变拟合 (与旧版完全同构的 9 基)
    ax, ay = fit_distortion(u_obs, v_obs, uv_opt[:,0], uv_opt[:,1])

    # 保存 (坐标都在 512 平面)
    sio.savemat(os.path.join(args.outdir, "dist_data.mat"),
                {"bpx": u_obs, "bpy": v_obs, "gpx": uv_opt[:,0], "gpy": uv_opt[:,1]})
    sio.savemat(os.path.join(args.outdir, "dist_coeff.mat"),
                {"ax": ax, "ay": ay, "d1": d1_opt, "d2": d2_opt, "xc": XC, "yc": YC})
    print(f"✅ 保存 dist_data.mat / dist_coeff.mat  (d1={d1_opt:.1f}, d2={d2_opt:.1f})")

    # 可视化
    plt.figure()
    plt.imshow(img512, cmap="gray")
    plt.scatter(u_obs, v_obs, c="r", s=12, label="beads (snapped)")
    plt.scatter(uv_opt[:,0], uv_opt[:,1], c="g", s=12, label="grid (old model, tuned)")
    plt.legend(); plt.title("Calibration (old-model compatible)")
    plt.show()

if __name__ == "__main__":
    main()

