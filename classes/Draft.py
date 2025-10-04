#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoAlign v0.3
思路：一层一层地生成 7x7 板子，手动整体调整 → 保存 → 再生成下一层
避免一次性操作两层的混乱
"""
## python3 Draft.py --dcm Data/DICOM/P0000001/ST000002/SE000003/IN000001

import argparse, os, math
import numpy as np
import cv2, pydicom
import scipy.io as sio
import matplotlib.pyplot as plt

# ---- 常量 ----
S = 512
XC, YC = 256.0, 256.0
D1, D2 = 2019.0, 1119.0  # 固定常数

# ---------- 相似变换 ----------
def apply_similarity_uv(uv, scale=1.0, theta_deg=0.0, tx=0.0, ty=0.0, center=(256,256)):
    uv = np.asarray(uv, float)
    c  = np.asarray(center, float)
    th = math.radians(theta_deg)
    R  = np.array([[math.cos(th), -math.sin(th)],
                   [math.sin(th),  math.cos(th)]], float)
    return ((uv - c) @ R.T) * scale + c + np.array([tx, ty], float)

# ---------- 手动交互 ----------
def interactive_manual_snap(
    img,
    uv0,
    obs,
    center=(256, 256),
    attach_px=8.0,
    detach_px=14.0,
    step_move=1.0,
    step_rot_deg=1.0,
    step_scale=1.01,
    prev_layers=None,              # 形如 [(uv_prev, "yellow"), ...]，仅显示、不可吸附
    exclude_prev_from_obs=True,    # 将与 prev_layers 重合的观测点排除，不参与吸附
):
    """
    手动整体调整 + 吸附/脱离（保存=所见即所得）
    - 红点：观测点（可吸附）
    - 黄点：上一层（只显示，不参与吸附）
    - 蓝点：当前未吸附的模型点
    - 绿点：当前已吸附到观测点的模型点
    键位：←→↑↓ 平移（Shift×5），A/D 旋转，-/= 缩放，Enter 确认，Esc/Q 取消
    """
    import math
    import numpy as np
    import matplotlib.pyplot as plt

    uv0 = np.asarray(uv0, float)
    obs = np.asarray(obs, float)
    sim = dict(scale=1.0, theta_deg=0.0, tx=0.0, ty=0.0)
    locks = {}  # {model_idx: obs_idx}
    last_uv_disp = uv0.copy()  # 记录“屏幕上看到”的最终点

    # 准备一个用于吸附的观测点副本（可滤除与上一层重合的点）
    obs_snap = obs.copy()
    if prev_layers and exclude_prev_from_obs:
        prev_all = np.vstack([np.asarray(u, float) for (u, _) in prev_layers if len(u)])
        if prev_all.size > 0:
            keep_mask = np.ones(len(obs_snap), dtype=bool)
            # 把与上一层重合(很近)的观测点排掉，避免吸附到黄点当前位置
            for p in prev_all:
                d = np.linalg.norm(obs_snap - p, axis=1)
                j = np.argmin(d)
                if d[j] < 1.5:  # 距离阈值可调
                    keep_mask[j] = False
            obs_snap = obs_snap[keep_mask]

    fig, ax = plt.subplots()
    ax.imshow(img, cmap="gray")

    # 先画红点（观测）
    scat_obs = ax.scatter(obs[:, 0], obs[:, 1], c="r", s=16, label="obs (red)", zorder=3)

    # 再画上一层黄点（在最上层，确保不会被遮盖；也不参与吸附）
    if prev_layers:
        for uv_prev, color in prev_layers:
            uv_prev = np.asarray(uv_prev, float)
            ax.scatter(uv_prev[:, 0], uv_prev[:, 1], c=color, s=22, alpha=0.95,
                       label="prev layer", zorder=6)

    # 当前层：拆成“未吸附(蓝)”与“已吸附(绿)”两组显示，保证绿点在最上层且更显眼
    scat_free = ax.scatter([], [], c="b", s=18, label="model free (blue)", zorder=4)
    scat_snap = ax.scatter([], [], c="g", s=30, label="model snapped (green)", zorder=7)

    txt = ax.text(6, 12, "", color="yellow", va="top", ha="left")
    ax.legend(loc="upper right")

    def current_uv():
        th = math.radians(sim["theta_deg"])
        R = np.array([[math.cos(th), -math.sin(th)],
                      [math.sin(th),  math.cos(th)]], float)
        return ((uv0 - center) @ R.T) * sim["scale"] + center + np.array([sim["tx"], sim["ty"]], float)

    def update_locks(uv):
        """进入 attach_px 吸附；离开 detach_px 脱离；可就近切换。"""
        new_locks = {}
        for i, p in enumerate(uv):
            d = np.linalg.norm(obs_snap - p, axis=1)
            if len(d) == 0:
                continue
            if i in locks:
                j = locks[i]
                # 注意：locks[i] 是基于 obs_snap 的索引
                if 0 <= j < len(obs_snap) and d[j] <= detach_px:
                    new_locks[i] = j
                else:
                    j2 = np.argmin(d)
                    if d[j2] < attach_px:
                        new_locks[i] = j2
            else:
                j = np.argmin(d)
                if d[j] < attach_px:
                    new_locks[i] = j
        locks.clear()
        locks.update(new_locks)

    def build_uv_disp(uv):
        """构造用于显示/保存的点集（所见即所得）"""
        snapped_idx = sorted(locks.keys())
        if snapped_idx:
            uv_snap = obs_snap[[locks[i] for i in snapped_idx]]  # 绿点直接用观测点坐标
        else:
            uv_snap = np.empty((0, 2), float)

        # 未吸附的保持几何变换后的蓝点
        if len(uv) > 0:
            mask = np.ones(len(uv), dtype=bool)
            if snapped_idx:
                mask[snapped_idx] = False
            uv_free = uv[mask]
        else:
            uv_free = np.empty((0, 2), float)
        return uv_free, uv_snap

    def redraw():
        nonlocal last_uv_disp
        uv = current_uv()
        update_locks(uv)

        uv_free, uv_snap = build_uv_disp(uv)

        scat_free.set_offsets(uv_free)
        scat_snap.set_offsets(uv_snap)

        # 文本状态
        txt.set_text(f"tx={sim['tx']:.1f}, ty={sim['ty']:.1f}, "
                     f"θ={sim['theta_deg']:.1f}°, s={sim['scale']:.3f}, "
                     f"locks={len(locks)}")
        fig.canvas.draw_idle()

        # 组合“屏幕可见”的最终点，供返回保存
        if len(uv) == 0:
            last_uv_disp = uv.copy()
        else:
            uv_disp = uv.copy()
            for i, j in locks.items():
                uv_disp[i] = obs_snap[j]
            last_uv_disp = uv_disp
        return last_uv_disp

    def on_key(e):
        if not e.key:
            return
        k = e.key.lower()
        accel = 5.0 if ("shift" in k) else 1.0
        moved = False
        if "left" in k:   sim["tx"] -= step_move * accel; moved = True
        elif "right" in k: sim["tx"] += step_move * accel; moved = True
        elif "up" in k:    sim["ty"] -= step_move * accel; moved = True
        elif "down" in k:  sim["ty"] += step_move * accel; moved = True
        elif k == "a":     sim["theta_deg"] -= step_rot_deg * accel; moved = True
        elif k == "d":     sim["theta_deg"] += step_rot_deg * accel; moved = True
        elif k in ("-", "minus"): sim["scale"] /= (step_scale ** accel); moved = True
        elif k in ("=", "+"):     sim["scale"] *= (step_scale ** accel); moved = True
        elif k in ("enter", "return", "escape", "esc", "q"):
            redraw()  # 关闭前再绘一次，确保 last_uv_disp 为最新
            plt.close(fig); return
        if moved:
            redraw()

    fig.canvas.mpl_connect("key_press_event", on_key)
    redraw()
    plt.show()

    # 返回索引：注意这里索引是基于“模型点”的；obs 索引无法直接还原到原 obs，
    # 因为我们可能对 obs_snap 做了过滤。若需要原始 obs 索引，可在外层做最近邻回找。
    idx_model = list(locks.keys())
    idx_obs_snap = [locks[i] for i in idx_model]  # 基于 obs_snap 的索引

    # 所见即所得（未吸附=蓝点最终位置；已吸附=红点位置）
    return last_uv_disp.copy(), dict(locks), sim.copy(), idx_model, idx_obs_snap


# ---------- 构建网格 ----------
def build_grid_single(f_pix_mm, bead_mm=20.0, Z=0.0, offset_frac=(0,0)):
    bead_px = bead_mm / (2.0 * f_pix_mm)
    coords = []
    dx = offset_frac[0] * bead_px
    dy = offset_frac[1] * bead_px
    for j in range(-3,4):
        for i in range(-3,4):
            X = XC + i * bead_px + dx
            Y = YC + j * bead_px + dy
            coords.append([X, Y, Z])
    return np.array(coords, dtype=np.float64)

def apply_perspective(XYZ, d1=D1, d2=D2, xc=XC, yc=YC):
    X, Y, Z = XYZ[:,0], XYZ[:,1], XYZ[:,2]
    s = d1 / (d2 + Z)
    u = s*(X - xc) + xc
    v = s*(Y - yc) + yc
    return np.stack([u,v], axis=1)

# ---------- 候选点检测 + 手动补点 ----------
def detect_candidates(img512, border=40):
    H, W = img512.shape
    cropped = img512[border:H-border, border:W-border]
    im = cv2.normalize(cropped, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    im = cv2.GaussianBlur(im, (3,3), 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9))
    tophat = cv2.morphologyEx(im, cv2.MORPH_TOPHAT, kernel)
    _, mask = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    num, _, stats, cents = cv2.connectedComponentsWithStats(mask)
    cands=[]
    for i in range(1,num):
        area=stats[i,cv2.CC_STAT_AREA]
        if 5<=area<=100:
            w,h=stats[i,2],stats[i,3]
            if max(w,h)/(min(w,h)+1e-6)<2.0:
                cx,cy=cents[i]; cands.append((cx+border,cy+border))
    return np.array(cands,np.float32)

def manual_add_points(img, existing_points, candidates=None, snap_dist=10):
    fig,ax=plt.subplots(); ax.imshow(img,cmap="gray")
    if len(existing_points)>0:
        ax.scatter(existing_points[:,0],existing_points[:,1],c="r",s=20,label="auto")
    ax.set_title("Left key = add, Enter/right key = end"); ax.legend()
    added=[]
    def onclick(e):
        if e.inaxes is None or e.button!=1: return
        pt=np.array([e.xdata,e.ydata])
        if candidates is not None and len(candidates)>0:
            d=np.linalg.norm(candidates-pt,axis=1); j=np.argmin(d)
            if d[j]<snap_dist: pt=candidates[j]
        added.append(pt); ax.scatter([pt[0]],[pt[1]],c="b",s=20); fig.canvas.draw_idle()
    cid=fig.canvas.mpl_connect("button_press_event",onclick)
    plt.show(); fig.canvas.mpl_disconnect(cid)
    if len(added)>0: return np.vstack([existing_points,np.array(added,np.float32)])
    return existing_points

# ---------- 主流程 ----------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dcm", required=True, help="DICOM 文件路径")
    ap.add_argument("--outdir", default="out", help="输出目录")
    ap.add_argument("--bead-mm", type=float, default=20.0, help="单层格距(mm)")
    ap.add_argument("--face-mm", type=float, default=200.0, help="层间距(mm)")
    ap.add_argument("--plane-offset", default="0.5,0.5", help="第二层偏移(以格距为单位)，如 0.5,0.5")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # --- Step0: DICOM 读图 ---
    ds = pydicom.dcmread(args.dcm)
    img = ds.pixel_array.astype(np.float32)
    img512 = cv2.resize(img, (S, S), interpolation=cv2.INTER_AREA)
    f_pix_mm = float(ds.ImagerPixelSpacing[0])

    ox, oy = map(float, args.plane_offset.split(","))

    # --- Step1: 自动候选 + 手动添加 ---
    cands = detect_candidates(img512, border=40)
    obs_all = manual_add_points(img512, cands, candidates=cands, snap_dist=10)
    if obs_all.shape[0] < 6:
        print("⚠️ 观测点太少(<6)，退出")
        return

    # --- Step2: 第一层 ---
    XYZ0 = build_grid_single(f_pix_mm, bead_mm=args.bead_mm, Z=0.0)
    uv_model0 = apply_perspective(XYZ0)
    uv_adj0, locks0, sim0, idx_m0, idx_o0 = interactive_manual_snap(
        img512, uv_model0, obs_all, center=(S / 2, S / 2)
    )

    print("✅ 第一层完成，保存中...")
    sio.savemat(os.path.join(args.outdir, "layer0.mat"),
                {"uv": uv_adj0, "sim": sim0,
                 "idx_model": idx_m0, "idx_obs": idx_o0,
                 "locks": locks0})  # 👈 保存锁定信息

    # --- Step3: 第二层 (显示第一层结果，黄色) ---
    face_px = args.face_mm / (2.0 * f_pix_mm)
    XYZ1 = build_grid_single(f_pix_mm, bead_mm=args.bead_mm, Z=face_px,
                             offset_frac=(ox, oy))
    uv_model1 = apply_perspective(XYZ1)
    uv_adj1, locks1, sim1, idx_m1, idx_o1 = interactive_manual_snap(
        img512, uv_model1, obs_all, center=(S / 2, S / 2),
        prev_layers=[(uv_adj0, "yellow")],  # 仅显示
        exclude_prev_from_obs=True  # 不参与吸附
    )
    print("✅ 第二层完成，保存中...")
    sio.savemat(os.path.join(args.outdir, "layer1.mat"),
                {"uv": uv_adj1, "sim": sim1, "idx_model": idx_m1, "idx_obs": idx_o1})

    # --- Step4: 合并 ---
    uv_all = np.vstack([uv_adj0, uv_adj1])
    idx_model_all = np.hstack([idx_m0, idx_m1])
    idx_obs_all   = np.hstack([idx_o0, idx_o1])
    sio.savemat(os.path.join(args.outdir, "dist_data.mat"),
                {"uv": uv_all, "idx_model": idx_model_all, "idx_obs": idx_obs_all})
    print("🎯 全部完成，dist_data.mat 已保存")

if __name__=="__main__":
    main()

