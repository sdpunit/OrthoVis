#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strict-compatible Fluoro Calibration (v4, clean)
- python3 Draft.py --dcm Data/DICOM/P0000001/ST000002/SE000003/IN000001 --out dist_data.mat
- 标定平面 S=512, 中心(256,256)
- 7x7x2 珠点板: px = mm / (2 * ImagerPixelSpacing)  (与旧版一致)
- 旧版投影: u = d1/(d2+Z)*(X - yc) + yc; v = d1/(d2+Z)*(Y - xc) + xc
- 交互式整体相似变换(蓝色网格): 平移/旋转/缩放
- 半吸附: 阈值→最大连通域→质心 (window=60)
- 观测↔模型匹配: Hungarian + 门限剔除
- 微调 d1/d2, 三次多项式畸变拟合(9基)
- 输出:
  - dist_data.mat  (bpx/bpy/gpx/gpy, 匹配到的成对点, 坐标均为 512 平面)
  - dist_coeff.mat (ax/ay + d1/d2/xc/yc + 相似变换参数)
"""

import argparse, os, math
import numpy as np
import pydicom
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy.optimize import least_squares, linear_sum_assignment
import cv2
from numpy.linalg import svd

# ------------------- 常量（与旧版一致） -------------------
S  = 512
XC = 256.0
YC = 256.0
D1 = 2019.0
D2 = 1119.0

# ------------------- 相似变换 + 交互调网格 -------------------
def apply_similarity_uv(uv, scale=1.0, theta=0.0, tx=0.0, ty=0.0, center=(256.0, 256.0), **_):
    """对 2D 网格 uv 应用相似变换（等比缩放 + 旋转 + 平移）。"""
    uv = np.asarray(uv, dtype=float)
    c  = np.asarray(center, dtype=float)
    th = math.radians(theta)
    R  = np.array([[math.cos(th), -math.sin(th)],
                   [math.sin(th),  math.cos(th)]], dtype=float)
    return ((uv - c) @ R.T) * scale + c + np.array([tx, ty])

def interactive_adjust_grid(img512, uv_init, center=(256.0,256.0),
                            step_move=1.0, step_rot_deg=1.0, step_scale=1.01):
    """
    键盘调网格：
      ← → ↑ ↓ : 平移（Shift ×5）
      A / D   : 旋转 -/+ (1°；Shift ×5)
      - / =   : 缩放 ×1.01 / ÷1.01（Shift 幂次）
      R       : 重置   H: 帮助
      Enter   : 确认   Esc/Q: 取消
    """
    params = dict(scale=1.0, theta=0.0, tx=0.0, ty=0.0)
    uv0 = np.array(uv_init, dtype=float)

    fig, ax = plt.subplots()
    ax.imshow(img512, cmap="gray")
    scat = ax.scatter(uv0[:,0], uv0[:,1], c="b", s=12, label="grid (adjust)")
    ax.set_title("Adjust grid: ←↑→↓ move, A/D rotate, -/= scale, R reset, H help, Enter done")
    ax.legend(loc="upper right")
    txt = ax.text(5, 10, "", color="w", va="top", ha="left")
    help_visible = False

    def render():
        uv_show = apply_similarity_uv(uv0, **params, center=center)
        scat.set_offsets(uv_show)
        txt.set_text(
            f"tx={params['tx']:.1f}, ty={params['ty']:.1f}, θ={params['theta']:.1f}°, s={params['scale']:.4f}"
            + ("\n←↑→↓ move, A/D rotate, -/= scale, R reset, Enter OK, ESC cancel" if help_visible else "")
        )
        fig.canvas.draw_idle()

    done, canceled = [False], [False]
    def on_key(e):
        nonlocal help_visible
        k = (e.key or "").lower()
        accel = 1.0 if ("shift" in (e.key or "")) else 0.1
        moved = False
        if   k == "left":  params["tx"] -= step_move*accel; moved=True
        elif k == "right": params["tx"] += step_move*accel; moved=True
        elif k == "up":    params["ty"] -= step_move*accel; moved=True
        elif k == "down":  params["ty"] += step_move*accel; moved=True
        elif k == "a":     params["theta"] -= step_rot_deg*accel; moved=True
        elif k == "d":     params["theta"] += step_rot_deg*accel; moved=True
        elif k in ("-", "minus"): params["scale"] /= (step_scale**accel); moved=True
        elif k in ("=", "+"):     params["scale"] *= (step_scale**accel); moved=True
        elif k == "r":     params.update(scale=1.0, theta=0.0, tx=0.0, ty=0.0); moved=True
        elif k in ("enter","return"): done[0]=True; plt.close(fig)
        elif k in ("escape","esc","q"): canceled[0]=True; plt.close(fig)
        elif k == "h": help_visible = not help_visible; moved=True
        if moved: render()

    fig.canvas.mpl_connect("key_press_event", on_key)
    render(); plt.show()

    if canceled[0]:
        return uv_init, dict(scale=1.0, theta=0.0, tx=0.0, ty=0.0)
    return apply_similarity_uv(uv0, **params, center=center), params

def collect_points_with_snap(ax, img512, snap_fn, stop_keys=("enter","return","escape")):
    """左键添加并吸附；右键/中键或 Enter/Return/Escape 结束；实时显示"""
    clicked, snapped = [], []
    scat_click, = ax.plot([], [], 'r+', ms=10, label='clicks')
    scat_snap,  = ax.plot([], [], 'yx', ms=7,  label='snapped')
    def on_click(event):
        if event.inaxes != ax: return
        if event.button == 1:
            x, y = float(event.xdata), float(event.ydata)
            sx, sy = snap_fn(img512, x, y, window=60)
            clicked.append((x, y)); snapped.append((sx, sy))
            scat_click.set_data([c[0] for c in clicked], [c[1] for c in clicked])
            scat_snap.set_data([s[0] for s in snapped], [s[1] for s in snapped])
            ax.figure.canvas.draw_idle()
        elif event.button in (2,3):
            plt.close(ax.figure)
    def on_key(event):
        if event.key and event.key.lower() in stop_keys:
            plt.close(ax.figure)
    fig = ax.figure
    cid1 = fig.canvas.mpl_connect('button_press_event', on_click)
    cid2 = fig.canvas.mpl_connect('key_press_event', on_key)
    ax.legend(loc="upper right"); plt.show()
    fig.canvas.mpl_disconnect(cid1); fig.canvas.mpl_disconnect(cid2)
    if len(snapped)==0: return np.empty((0,2)), np.empty((0,2))
    return np.array(clicked, dtype=float), np.array(snapped, dtype=float)

# ------------------- 粗检亮点 + 相似对齐（可选） -------------------
def detect_beads_centroids(img512, thr=None):
    im = cv2.normalize(img512, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    im = cv2.GaussianBlur(im, (5,5), 0)
    if thr is None:
        _, mask = cv2.threshold(im, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    else:
        _, mask = cv2.threshold(im, thr, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
    num, _, stats, cents = cv2.connectedComponentsWithStats(mask)
    keep = []
    for i in range(1, num):
        area = stats[i, cv2.CC_STAT_AREA]
        if 3 <= area <= 200:
            keep.append(cents[i])
    if not keep: return np.empty((0,2), np.float32)
    return np.array(keep, dtype=np.float32)

def procrustes_similarity(X, Y):
    Xc = X - X.mean(axis=0, keepdims=True)
    Yc = Y - Y.mean(axis=0, keepdims=True)
    U, Svals, Vt = svd(Xc.T @ Yc)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1; R = U @ Vt
    scale = (Svals.sum() / (Xc**2).sum())
    t = Y.mean(axis=0) - X.mean(axis=0) @ (scale * R)
    return scale, R, t

# ------------------- 网格 & 投影（旧版） -------------------
def build_grid_px(f_pix_mm, bead_mm=20.0, face_mm=200.0):
    bead_px = bead_mm / (2.0 * f_pix_mm)
    face_px = face_mm / (2.0 * f_pix_mm)
    coords3d = []
    for z in [0.0, face_px]:
        for j in range(-3, 4):
            for i in range(-3, 4):
                X = XC + i * bead_px
                Y = YC + j * bead_px
                coords3d.append([X, Y, z])
    return np.array(coords3d, dtype=np.float64)  # (98,3)

def apply_perspective_calibrate(XYZ, d1=D1, d2=D2, xc=XC, yc=YC):
    X = XYZ[:, 0]; Y = XYZ[:, 1]; Z = XYZ[:, 2]
    s = d1 / (d2 + Z)
    u = s * (X - yc) + yc
    v = s * (Y - xc) + xc
    return np.stack([u, v], axis=1)

# ------------------- 半吸附 -------------------
def snap_to_bead(img512, x, y, window=60):
    H, W = img512.shape
    x0, x1 = int(max(0, x-window)), int(min(W, x+window))
    y0, y1 = int(max(0, y-window)), int(min(H, y+window))
    roi = img512[y0:y1, x0:x1]
    if roi.size == 0: return x, y
    roi = cv2.normalize(roi, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    roi = cv2.GaussianBlur(roi, (5,5), 0)
    _, mask = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    num, _, stats, cents = cv2.connectedComponentsWithStats(mask)
    if num <= 1: return x, y
    idx = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    cx, cy = cents[idx]
    return x0 + cx, y0 + cy

# ------------------- 畸变拟合（9基） -------------------
def poly_features(u, v):
    x = u - S/2.0
    y = v - S/2.0
    Xv = np.stack([x, y, x**2, x*y, y**2, x**3, (x**2)*y, x*(y**2), y**3], axis=1)
    Yv = np.stack([y, x, y**2, y*x, x**2, y**3, (y**2)*x, y*(x**2), x**3], axis=1)
    return Xv, Yv

def fit_distortion(u_obs, v_obs, u_ref, v_ref):
    Xv, Yv = poly_features(u_obs, v_obs)
    du = (u_ref - u_obs)
    dv = (v_ref - v_obs)
    ax, _, _, _ = np.linalg.lstsq(Xv, du, rcond=None)
    ay, _, _, _ = np.linalg.lstsq(Yv, dv, rcond=None)
    return ax.astype(np.float64), ay.astype(np.float64)

# ------------------- 匹配（Hungarian + 门限） -------------------
def match_points(uv_model, uv_obs, gate=25.0):
    from scipy.spatial.distance import cdist
    D = cdist(uv_obs, uv_model)  # M x N
    rows, cols = linear_sum_assignment(D)
    keep = [k for k,(r,c) in enumerate(zip(rows, cols)) if D[r, c] <= gate]
    if len(keep) == 0:
        return np.empty((0,2)), np.empty((0,2)), [], []
    rows = rows[keep]; cols = cols[keep]
    return uv_obs[rows], uv_model[cols], rows.tolist(), cols.tolist()

# ------------------- 主流程 -------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dcm", required=True, help="DICOM 文件路径")
    ap.add_argument("--outdir", default="out", help="输出目录")
    ap.add_argument("--gate", type=float, default=25.0, help="匹配门限(像素, 512坐标系)")
    ap.add_argument("--no-auto-init", action="store_true", help="关闭自动预对齐")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # 读 DICOM -> 缩放到 512
    ds  = pydicom.dcmread(args.dcm)
    img = ds.pixel_array.astype(np.float32)
    img512 = cv2.resize(img, (S, S), interpolation=cv2.INTER_AREA)

    if "ImagerPixelSpacing" not in ds:
        raise RuntimeError("DICOM 缺少 ImagerPixelSpacing")
    f_pix_mm = float(ds.ImagerPixelSpacing[0])

    # 3D grid & 初始投影（旧版）
    XYZ = build_grid_px(f_pix_mm=f_pix_mm)
    uv0 = apply_perspective_calibrate(XYZ)  # (98,2) on 512

    # ——(可选) 自动预对齐：用粗检亮点的质心做相似变换——
    if not args.no_auto_init:
        cand = detect_beads_centroids(img512)  # (M,2)
        if cand.shape[0] >= 30:
            center = np.array([[S/2, S/2]])
            k = min(len(uv0), len(cand))
            idx_c = np.argsort(np.linalg.norm(cand - center, axis=1))[:k]
            idx_m = np.argsort(np.linalg.norm(uv0  - center, axis=1))[:k]
            s, R2, t = procrustes_similarity(uv0[idx_m], cand[idx_c])
            uv0 = (uv0 @ (s * R2)) + t

    # ——交互整体调网格：平移/旋转/缩放——
    uv0_adj, sim_params = interactive_adjust_grid(
        img512, uv0, center=(S/2, S/2),
        step_move=5.0, step_rot_deg=1.0, step_scale=1.01
    )
    print(f"[init adjust] {sim_params}")

    # ——点击 + 半吸附（实时显示）——
    fig, ax = plt.subplots()
    ax.imshow(img512, cmap="gray")
    ax.scatter(uv0_adj[:,0], uv0_adj[:,1], c="b", s=12, label="init grid (adjusted)")
    ax.set_title("Click near beads (Left click = Add and attach, right click /Enter= End)")
    _, snapped = collect_points_with_snap(ax, img512, snap_to_bead)
    plt.close(fig)
    if snapped.shape[0] < 6:
        print("有效点少于6，退出。")
        sio.savemat(os.path.join(args.outdir, "dist_data.mat"),
                    {"bpx": snapped[:,0], "bpy": snapped[:,1], "gpx": [], "gpy": []})
        return

    # ——匹配：观测 ↔ 模型（基于调整后的 uv0_adj）——
    obs_sel, model_sel, idx_obs, idx_model = match_points(uv0_adj, snapped, gate=args.gate)
    if obs_sel.shape[0] < 6:
        print("匹配后有效对数 < 6，请多点些、或调整 --gate。")
        sio.savemat(os.path.join(args.outdir, "dist_data.mat"),
                    {"bpx": snapped[:,0], "bpy": snapped[:,1], "gpx": [], "gpy": []})
        return

    # ——微调 d1/d2（仅在匹配到的索引上）——
    def resid_dd(p):
        d1, d2 = p
        uv = apply_perspective_calibrate(XYZ[idx_model], d1=d1, d2=d2, xc=XC, yc=YC)
        return (uv - obs_sel).ravel()
    try:
        res = least_squares(resid_dd, x0=np.array([D1, D2]),
                            bounds=([D1-200, D2-200], [D1+200, D2+200]),
                            verbose=0)
        d1_opt, d2_opt = float(res.x[0]), float(res.x[1])
    except Exception:
        d1_opt, d2_opt = D1, D2

    uv_opt = apply_perspective_calibrate(XYZ[idx_model], d1=d1_opt, d2=d2_opt, xc=XC, yc=YC)

    # ——畸变拟合(9基)——
    ax_coef, ay_coef = fit_distortion(obs_sel[:,0], obs_sel[:,1], uv_opt[:,0], uv_opt[:,1])

    # ——保存（512坐标系）——
    sio.savemat(os.path.join(args.outdir, "dist_data.mat"),
                {"bpx": obs_sel[:,0], "bpy": obs_sel[:,1],
                 "gpx": uv_opt[:,0], "gpy": uv_opt[:,1],
                 "matched_obs_idx": np.array(idx_obs, dtype=np.int32),
                 "matched_model_idx": np.array(idx_model, dtype=np.int32)})
    sio.savemat(os.path.join(args.outdir, "dist_coeff.mat"),
                {"ax": ax_coef, "ay": ay_coef,
                 "d1": d1_opt, "d2": d2_opt, "xc": XC, "yc": YC,
                 "sim_scale": sim_params.get("scale",1.0),
                 "sim_theta_deg": sim_params.get("theta",0.0),
                 "sim_tx": sim_params.get("tx",0.0),
                 "sim_ty": sim_params.get("ty",0.0)})
    print(f"✅ 保存 dist_data.mat / dist_coeff.mat  (pairs={len(idx_obs)}, d1={d1_opt:.1f}, d2={d2_opt:.1f})")

    # ——可视化结果——
    plt.imshow(img512, cmap="gray")
    plt.scatter(obs_sel[:,0], obs_sel[:,1], c="r", s=14, label="beads (snapped, used)")
    plt.scatter(uv_opt[:,0],  uv_opt[:,1],  c="g", s=14, label="grid (matched, tuned)")
    plt.legend(); plt.title("Calibration (matched)")
    plt.show()

if __name__ == "__main__":
    main()

