#!/usr/bin/env python3
"""
N01 CE201 - Autonomous Hover Mission (Non-GPS, Optical Flow + Rangefinder)
Executes a 30-second local position hold at 1.0m altitude in local-NED coordinates.
Logs 20 Hz timeseries and computes hold and estimator errors against ground truth.
"""

import asyncio
import csv
import json
import math
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from mavsdk import System
from mavsdk.offboard import PositionNedYaw, OffboardError
from pyulog import ULog

# Mission parameters
TARGET_ALTITUDE_M = 1.0       # Hover altitude: 1.0m (z = -1.0m in NED)
HOVER_DURATION_S = 30.0       # Hold window: 30 s THỜI GIAN SIM (PX4 odometry), không phải đồng hồ tường
HOVER_WALL_CAP_S = 300.0      # Chặn trên theo đồng hồ tường, phòng sim đứng (RTF quá thấp)
SETPOINT_RATE_HZ = 20.0       # 20 Hz setpoint stream
DT = 1.0 / SETPOINT_RATE_HZ
RAMP_SPEED_M_S = 0.4          # Smooth vertical climb/descent speed

# Safety boundaries
MAX_HORIZONTAL_DRIFT_M = 1.8  # Safety abort if XY drift > 1.8m
MAX_ALTITUDE_ERROR_M = 0.8    # Safety abort if height diverges by > 0.8m

OUTPUT_DIR = Path("/workspace/sim/evidence/flight_logs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def run_mission():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"==================================================", flush=True)
    print(f"N01 Autonomous Hover Mission (Run ID: {run_id})", flush=True)
    print(f"Target: Hold 1.0m altitude for {HOVER_DURATION_S}s in Local-NED", flush=True)
    print(f"==================================================", flush=True)

    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")

    print("[1/6] Waiting for drone MAVLink connection...", flush=True)
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("      Connected to PX4 Autopilot!", flush=True)
            break

    print("[2/6] Verifying sensor fusion and armable state...", flush=True)
    start_wait = time.time()
    ready_to_arm = False
    while time.time() - start_wait < 60.0:
        async for h in drone.telemetry.health():
            if h.is_local_position_ok:
                ready_to_arm = True
            break
        if ready_to_arm:
            print("      EKF2 Local Position is VALID and Vehicle is ARMABLE!", flush=True)
            break
        await asyncio.sleep(1.0)

    if not ready_to_arm:
        print("ERROR: Timeout waiting for armable vehicle. Aborting.", flush=True)
        sys.exit(1)

    # Initial setpoint on ground (x=0, y=0, z=0, yaw=0)
    current_x = 0.0
    current_y = 0.0
    current_z = 0.0
    current_yaw = 0.0

    async for pos in drone.telemetry.position_velocity_ned():
        current_x = pos.position.north_m
        current_y = pos.position.east_m
        current_z = pos.position.down_m
        break

    print(f"      Initial ground position: N={current_x:.3f}m, E={current_y:.3f}m, D={current_z:.3f}m", flush=True)

    takeoff_x = current_x
    takeoff_y = current_y
    takeoff_z = current_z
    target_z = takeoff_z - TARGET_ALTITUDE_M

    # Stream setpoints before activating Offboard
    print("[3/6] Streaming initial offboard setpoints...", flush=True)
    target_sp = PositionNedYaw(takeoff_x, takeoff_y, takeoff_z, 0.0)
    for _ in range(25):
        await drone.offboard.set_position_ned(target_sp)
        await asyncio.sleep(DT)

    print("[4/6] Starting Offboard mode and Arming...", flush=True)
    try:
        await drone.offboard.start()
        print("      Offboard mode active!", flush=True)
    except OffboardError as e:
        print(f"ERROR: Failed to start Offboard mode: {e}", flush=True)
        sys.exit(1)

    armed = False
    for attempt in range(5):
        try:
            await drone.action.arm()
            armed = True
            print("      Vehicle ARMED successfully!", flush=True)
            break
        except Exception as e:
            print(f"      Arm attempt {attempt+1} note: {e}, waiting 1s...", flush=True)
            await asyncio.sleep(1.0)

    if not armed:
        print("ERROR: Failed to arm vehicle after 5 attempts.", flush=True)
        sys.exit(1)

    # Smooth climb to target_z
    current_target_z = takeoff_z
    print(f"[5/6] Climbing smoothly to target altitude {TARGET_ALTITUDE_M:.1f}m (z={target_z:.1f}m)...", flush=True)

    telemetry_records = []
    abort_reason = None

    # Helper task to update latest position
    latest_ned = {"x": current_x, "y": current_y, "z": current_z, "vx": 0.0, "vy": 0.0, "vz": 0.0}

    async def telemetry_listener():
        async for p in drone.telemetry.position_velocity_ned():
            latest_ned["x"] = p.position.north_m
            latest_ned["y"] = p.position.east_m
            latest_ned["z"] = p.position.down_m
            latest_ned["vx"] = p.velocity.north_m_s
            latest_ned["vy"] = p.velocity.east_m_s
            latest_ned["vz"] = p.velocity.down_m_s

    telem_task = asyncio.create_task(telemetry_listener())

    # Climb loop
    while current_target_z > target_z:
        current_target_z = max(target_z, current_target_z - RAMP_SPEED_M_S * DT)
        sp = PositionNedYaw(takeoff_x, takeoff_y, current_target_z, 0.0)
        await drone.offboard.set_position_ned(sp)
        await asyncio.sleep(DT)

    # Wait until vehicle reaches within 0.20m of hover altitude
    reach_timeout = time.time() + 35.0
    while time.time() < reach_timeout:
        sp = PositionNedYaw(takeoff_x, takeoff_y, target_z, 0.0)
        await drone.offboard.set_position_ned(sp)
        if abs(latest_ned["z"] - target_z) < 0.20:
            print(f"      Reached hover altitude: z={latest_ned['z']:.3f}m! Starting 30s evaluation window...", flush=True)
            break
        await asyncio.sleep(DT)

    # Thời gian PX4 (sim time): cửa sổ 30 s phải đếm theo đây, không theo đồng hồ tường, vì RTF < 1.
    sim_clock = {"t": None}

    async def sim_time_listener():
        async for o in drone.telemetry.odometry():
            sim_clock["t"] = o.time_usec / 1e6

    sim_task = asyncio.create_task(sim_time_listener())

    # 30-Second Hover Measurement Window (đo bằng sim time)
    while sim_clock["t"] is None:
        await asyncio.sleep(0.05)
    sim_start = sim_clock["t"]
    wall_start = time.time()
    hover_start_time = wall_start
    hover_end_time = wall_start + HOVER_WALL_CAP_S
    step = 0

    while time.time() < hover_end_time and (sim_clock["t"] - sim_start) < HOVER_DURATION_S:
        t_rel = sim_clock["t"] - sim_start
        sp = PositionNedYaw(takeoff_x, takeoff_y, target_z, 0.0)
        await drone.offboard.set_position_ned(sp)

        x_est = latest_ned["x"]
        y_est = latest_ned["y"]
        z_est = latest_ned["z"]
        vx_est = latest_ned["vx"]
        vy_est = latest_ned["vy"]
        vz_est = latest_ned["vz"]

        e_xy = math.sqrt((x_est - takeoff_x)**2 + (y_est - takeoff_y)**2)
        e_z = abs(z_est - target_z)

        telemetry_records.append({
            "t_rel_s": round(t_rel, 3),
            "sp_x": 0.0, "sp_y": 0.0, "sp_z": target_z,
            "est_x": round(x_est, 4), "est_y": round(y_est, 4), "est_z": round(z_est, 4),
            "est_vx": round(vx_est, 4), "est_vy": round(vy_est, 4), "est_vz": round(vz_est, 4),
            "err_xy": round(e_xy, 4), "err_z": round(e_z, 4)
        })

        if step % 20 == 0:  # Print every 1 second
            print(f"      [t={t_rel:4.1f}s] Pos: ({x_est:+6.3f}, {y_est:+6.3f}, {z_est:+6.3f})m | "
                  f"e_xy: {e_xy:5.3f}m | e_z: {e_z:5.3f}m", flush=True)

        # Safety supervisor
        if e_xy > MAX_HORIZONTAL_DRIFT_M:
            abort_reason = f"Safety Abort: Horizontal drift ({e_xy:.3f}m) exceeded limit ({MAX_HORIZONTAL_DRIFT_M}m)"
            print(f"WARNING: {abort_reason}", flush=True)
            break
        if e_z > MAX_ALTITUDE_ERROR_M:
            abort_reason = f"Safety Abort: Altitude error ({e_z:.3f}m) exceeded limit ({MAX_ALTITUDE_ERROR_M}m)"
            print(f"WARNING: {abort_reason}", flush=True)
            break

        step += 1
        await asyncio.sleep(DT)

    # [6/6] Descent and Landing
    print("[6/6] Hover window complete. Initiating controlled descent...", flush=True)
    descend_z = target_z
    while descend_z < takeoff_z - 0.15:
        descend_z = min(takeoff_z - 0.15, descend_z + RAMP_SPEED_M_S * DT)
        sp = PositionNedYaw(takeoff_x, takeoff_y, descend_z, 0.0)
        await drone.offboard.set_position_ned(sp)
        await asyncio.sleep(DT)

    try:
        print("      Triggering auto-land...", flush=True)
        await drone.action.land()
    except Exception as e:
        print(f"      Auto-land notification: {e}", flush=True)

    # Wait for disarm
    disarm_timeout = time.time() + 15.0
    while time.time() < disarm_timeout:
        async for armed in drone.telemetry.armed():
            if not armed:
                print("      Vehicle successfully DISARMED on ground!", flush=True)
                break
        else:
            await asyncio.sleep(0.5)
            continue
        break

    telem_task.cancel()
    sim_task.cancel()

    # Save CSV Timeseries
    csv_file = OUTPUT_DIR / f"hover_{run_id}.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "t_rel_s", "sp_x", "sp_y", "sp_z",
            "est_x", "est_y", "est_z",
            "est_vx", "est_vy", "est_vz",
            "err_xy", "err_z"
        ])
        writer.writeheader()
        writer.writerows(telemetry_records)
    print(f"Saved flight timeseries CSV: {csv_file} ({len(telemetry_records)} samples)", flush=True)

    # Copy latest ULog
    px4_log_dir = Path("/px4/build/px4_sitl_default/rootfs/log")
    latest_ulg = None
    if px4_log_dir.exists():
        ulgs = sorted(px4_log_dir.rglob("*.ulg"), key=lambda p: p.stat().st_mtime)
        if ulgs:
            latest_ulg = ulgs[-1]
            dest_ulg = OUTPUT_DIR / f"hover_{run_id}.ulg"
            shutil.copy2(latest_ulg, dest_ulg)
            print(f"Copied source ULog file: {dest_ulg} ({dest_ulg.stat().st_size} bytes)", flush=True)

    # Compute Statistics from telemetry
    err_xy_list = [r["err_xy"] for r in telemetry_records]
    err_z_list = [r["err_z"] for r in telemetry_records]

    if err_xy_list:
        max_e_xy = max(err_xy_list)
        rmse_e_xy = math.sqrt(sum(e**2 for e in err_xy_list) / len(err_xy_list))
        sorted_xy = sorted(err_xy_list)
        p95_e_xy = sorted_xy[int(0.95 * len(sorted_xy))]
        mean_e_xy = sum(err_xy_list) / len(err_xy_list)

        max_e_z = max(err_z_list)
        rmse_e_z = math.sqrt(sum(e**2 for e in err_z_list) / len(err_z_list))

        kpi_pass = (max_e_xy <= 0.50) and (abort_reason is None) and (len(telemetry_records) >= int(0.9 * HOVER_DURATION_S * SETPOINT_RATE_HZ))

        # Ground Truth comparison via ULog if available
        gt_analysis = analyze_ulog_gt(OUTPUT_DIR / f"hover_{run_id}.ulg") if latest_ulg else None

        summary = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "target_altitude_m": TARGET_ALTITUDE_M,
            "hover_duration_requested_s": HOVER_DURATION_S,
            "hover_duration_actual_s": round(telemetry_records[-1]["t_rel_s"], 2) if telemetry_records else 0,
            "samples_count": len(telemetry_records),
            "abort_reason": abort_reason,
            "kpi_target_max_horizontal_error_m": 0.50,
            "telemetry_metrics": {
                "max_horizontal_error_m": round(max_e_xy, 4),
                "rmse_horizontal_error_m": round(rmse_e_xy, 4),
                "p95_horizontal_error_m": round(p95_e_xy, 4),
                "mean_horizontal_error_m": round(mean_e_xy, 4),
                "max_vertical_error_m": round(max_e_z, 4),
                "rmse_vertical_error_m": round(rmse_e_z, 4),
            },
            "kpi_result": "PASS" if kpi_pass else "FAIL",
            "ground_truth_metrics": gt_analysis
        }

        json_file = OUTPUT_DIR / f"hover_{run_id}.json"
        json_file.write_text(json.dumps(summary, indent=2) + "\n")
        print(f"Saved evaluation JSON: {json_file}", flush=True)

        print("\n=================== KPI EVALUATION REPORT ===================", flush=True)
        print(f"Run ID:                  {run_id}", flush=True)
        print(f"Hover Duration:          {summary['hover_duration_actual_s']}s / {HOVER_DURATION_S}s", flush=True)
        print(f"Max Horizontal Error:    {max_e_xy:.4f} m (Threshold: <= 0.50 m)", flush=True)
        print(f"RMSE Horizontal Error:   {rmse_e_xy:.4f} m", flush=True)
        print(f"P95 Horizontal Error:    {p95_e_xy:.4f} m", flush=True)
        print(f"Mean Horizontal Error:   {mean_e_xy:.4f} m", flush=True)
        print(f"Max Altitude Error:      {max_e_z:.4f} m", flush=True)
        print(f"RMSE Altitude Error:     {rmse_e_z:.4f} m", flush=True)
        if gt_analysis:
            print(f"Ground Truth Max Error:  {gt_analysis.get('max_hold_error_gt_m')} m", flush=True)
            print(f"Estimator vs GT RMSE:    {gt_analysis.get('rmse_estimator_vs_gt_m')} m", flush=True)
        print(f"KPI Status:              {'PASS' if kpi_pass else 'FAIL'}", flush=True)
        if abort_reason:
            print(f"Abort Notice:            {abort_reason}", flush=True)
        print("=============================================================", flush=True)


def analyze_ulog_gt(ulg_path: Path):
    if not ulg_path.exists():
        return None
    try:
        ulog = ULog(str(ulg_path))
        lpos = None
        lpos_gt = None
        for d in ulog.data_list:
            if d.name == "vehicle_local_position":
                lpos = d
            elif d.name == "vehicle_local_position_groundtruth":
                lpos_gt = d

        if not lpos or not lpos_gt:
            return {"error": "Missing position or groundtruth topics in ULog"}

        # Extract samples
        t_gt = lpos_gt.data["timestamp"]
        x_gt = lpos_gt.data["x"]
        y_gt = lpos_gt.data["y"]
        z_gt = lpos_gt.data["z"]

        t_est = lpos.data["timestamp"]
        x_est = lpos.data["x"]
        y_est = lpos.data["y"]
        z_est = lpos.data["z"]

        # Cửa sổ hover = các mẫu estimator có độ cao >= 85% độ cao đỉnh (loại cất cánh/hạ cánh).
        # ponytail: xấp xỉ theo độ cao; thay bằng mốc thời gian mission nếu cần khớp 30 s chính xác.
        import numpy as np
        t_e = np.asarray(t_est) / 1e6
        alt = -np.asarray(z_est)
        idx = np.where(alt >= 0.85 * alt.max())[0]
        if len(idx) < 2:
            return {"error": "Không tìm thấy cửa sổ hover trong ULog"}
        t0, t1 = t_e[idx[0]], t_e[idx[-1]]
        t_g = np.asarray(t_gt) / 1e6
        m = (t_g >= t0) & (t_g <= t1)
        if not m.any():
            return {"error": "Không có mẫu GT trong cửa sổ hover"}
        xg, yg = np.asarray(x_gt)[m], np.asarray(y_gt)[m]
        # Sai số giữ vị trí GT: so với điểm GT lúc bắt đầu hover (không phải gốc tọa độ).
        err_hold_gt = np.hypot(xg - xg[0], yg - yg[0])
        # Lệch estimator so với GT (cùng gốc là điểm bắt đầu hover), GT nội suy theo thời gian estimator.
        xe = np.interp(t_g[m], t_e, np.asarray(x_est)); ye = np.interp(t_g[m], t_e, np.asarray(y_est))
        drift = np.hypot((xg - xg[0]) - (xe - xe[0]), (yg - yg[0]) - (ye - ye[0]))
        return {
            "gt_samples": int(m.sum()),
            "est_samples": len(t_est),
            "hover_window_sim_s": round(float(t1 - t0), 2),
            "max_hold_error_gt_m": round(float(err_hold_gt.max()), 4),
            "mean_hold_error_gt_m": round(float(err_hold_gt.mean()), 4),
            "p95_hold_error_gt_m": round(float(np.percentile(err_hold_gt, 95)), 4),
            "rmse_estimator_vs_gt_m": round(float(math.sqrt((drift ** 2).mean())), 4),
            "max_estimator_vs_gt_m": round(float(drift.max()), 4),
        }
    except Exception as e:
        return {"error": f"Failed to parse ULog GT: {e}"}


if __name__ == "__main__":
    asyncio.run(run_mission())
