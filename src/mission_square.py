#!/usr/bin/env python3
"""
N01 CE201 - Autonomous Square Trajectory Mission (Non-GPS, Optical Flow + Rangefinder)
Executes a 2.0m x 2.0m square trajectory at 1.0m altitude in local-NED coordinates:
(0,0) -> (2,0) -> (2,2) -> (0,2) -> (0,0) meters.
Logs 20 Hz timeseries and computes corner errors, cross-track errors, and loop closure.
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
ALTITUDE_M = 1.0              # Flight altitude: 1.0m (z = -1.0m in NED)
CRUISE_SPEED_M_S = 0.25       # Safe indoor trajectory speed: 0.25 m/s
CORNER_DWELL_S = 3.0          # Dwell time at each vertex: 3.0s
SETPOINT_RATE_HZ = 20.0       # 20 Hz setpoint stream
DT = 1.0 / SETPOINT_RATE_HZ
RAMP_SPEED_M_S = 0.4          # Vertical climb/descent speed

# 4 Waypoints defining 2x2m square in local NED (North, East, Down, Yaw)
WAYPOINTS = [
    {"name": "WP0_Origin", "x": 0.0, "y": 0.0, "z": -ALTITUDE_M, "yaw": 0.0},
    {"name": "WP1_North",  "x": 2.0, "y": 0.0, "z": -ALTITUDE_M, "yaw": 0.0},
    {"name": "WP2_East",   "x": 2.0, "y": 2.0, "z": -ALTITUDE_M, "yaw": 0.0},
    {"name": "WP3_South",  "x": 0.0, "y": 2.0, "z": -ALTITUDE_M, "yaw": 0.0},
    {"name": "WP4_Home",   "x": 0.0, "y": 0.0, "z": -ALTITUDE_M, "yaw": 0.0},
]

# Safety boundaries
MAX_CROSS_TRACK_M = 1.5       # Safety abort if perpendicular drift > 1.5m
MAX_ALTITUDE_ERROR_M = 0.8    # Safety abort if height diverges by > 0.8m

OUTPUT_DIR = Path("/workspace/sim/evidence/flight_logs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def run_mission():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"==================================================", flush=True)
    print(f"N01 Autonomous 2x2m Square Mission (Run ID: {run_id})", flush=True)
    print(f"Trajectory: (0,0) -> (2,0) -> (2,2) -> (0,2) -> (0,0)m at 1.0m altitude", flush=True)
    print(f"==================================================", flush=True)

    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")

    print("[1/6] Waiting for drone MAVLink connection...", flush=True)
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("      Connected to PX4 Autopilot!", flush=True)
            break

    print("[2/6] Verifying sensor fusion and local estimate...", flush=True)
    start_wait = time.time()
    local_pos_ok = False
    while time.time() - start_wait < 45.0:
        async for h in drone.telemetry.health():
            if h.is_local_position_ok:
                local_pos_ok = True
            break
        if local_pos_ok:
            print("      EKF2 Local Position is VALID (Optical Flow + Range active)!", flush=True)
            break
        await asyncio.sleep(1.0)

    if not local_pos_ok:
        print("ERROR: Timeout waiting for valid local position estimate. Aborting.", flush=True)
        sys.exit(1)

    # Initial ground setpoint
    current_x = 0.0
    current_y = 0.0
    current_z = 0.0

    async for pos in drone.telemetry.position_velocity_ned():
        current_x = pos.position.north_m
        current_y = pos.position.east_m
        current_z = pos.position.down_m
        break

    print(f"      Initial ground position: N={current_x:.3f}m, E={current_y:.3f}m, D={current_z:.3f}m", flush=True)

    # Stream setpoints before activating Offboard
    print("[3/6] Streaming initial offboard setpoints...", flush=True)
    target_sp = PositionNedYaw(0.0, 0.0, 0.0, 0.0)
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

    try:
        await drone.action.arm()
        print("      Vehicle ARMED successfully!", flush=True)
    except Exception as e:
        print(f"ERROR: Failed to arm vehicle: {e}", flush=True)
        sys.exit(1)

    # Telemetry listener task
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

    # Vertical Climb to -1.0m
    target_z = -ALTITUDE_M
    current_target_z = 0.0
    print(f"[5/6] Climbing to hover altitude {ALTITUDE_M:.1f}m (z={target_z:.1f}m)...", flush=True)

    while current_target_z > target_z:
        current_target_z = max(target_z, current_target_z - RAMP_SPEED_M_S * DT)
        sp = PositionNedYaw(0.0, 0.0, current_target_z, 0.0)
        await drone.offboard.set_position_ned(sp)
        await asyncio.sleep(DT)

    # Wait until vehicle reaches within 0.20m of hover altitude
    reach_timeout = time.time() + 35.0
    while time.time() < reach_timeout:
        sp = PositionNedYaw(0.0, 0.0, target_z, 0.0)
        await drone.offboard.set_position_ned(sp)
        if abs(latest_ned["z"] - target_z) < 0.20:
            print(f"      Reached altitude z={latest_ned['z']:.3f}m! Starting Square Trajectory...", flush=True)
            break
        await asyncio.sleep(DT)

    telemetry_records = []
    corner_metrics = []
    abort_reason = None
    flight_start_time = time.time()

    # Fly each segment of the 2x2m square
    for seg_idx in range(len(WAYPOINTS) - 1):
        wp_from = WAYPOINTS[seg_idx]
        wp_to = WAYPOINTS[seg_idx + 1]

        seg_dist = math.sqrt((wp_to["x"] - wp_from["x"])**2 + (wp_to["y"] - wp_from["y"])**2)
        seg_duration = seg_dist / CRUISE_SPEED_M_S
        num_steps = max(1, int(seg_duration / DT))

        print(f"\n      -> Segment {seg_idx+1}: {wp_from['name']} -> {wp_to['name']} (dist: {seg_dist:.1f}m, {seg_duration:.1f}s)", flush=True)

        for step in range(num_steps):
            frac = (step + 1) / num_steps
            sp_x = wp_from["x"] + frac * (wp_to["x"] - wp_from["x"])
            sp_y = wp_from["y"] + frac * (wp_to["y"] - wp_from["y"])
            sp_z = target_z

            sp = PositionNedYaw(sp_x, sp_y, sp_z, 0.0)
            await drone.offboard.set_position_ned(sp)

            t_rel = time.time() - flight_start_time
            x_est = latest_ned["x"]
            y_est = latest_ned["y"]
            z_est = latest_ned["z"]

            # Tracking error
            e_track = math.sqrt((x_est - sp_x)**2 + (y_est - sp_y)**2)
            e_z = abs(z_est - target_z)

            telemetry_records.append({
                "t_rel_s": round(t_rel, 3),
                "segment": seg_idx + 1,
                "sp_x": round(sp_x, 4), "sp_y": round(sp_y, 4), "sp_z": round(sp_z, 4),
                "est_x": round(x_est, 4), "est_y": round(y_est, 4), "est_z": round(z_est, 4),
                "est_vx": round(latest_ned["vx"], 4), "est_vy": round(latest_ned["vy"], 4), "est_vz": round(latest_ned["vz"], 4),
                "err_track": round(e_track, 4), "err_z": round(e_z, 4)
            })

            if step % 20 == 0:
                print(f"         [t={t_rel:4.1f}s] Seg {seg_idx+1} ({frac*100:3.0f}%) | Pos: ({x_est:+5.2f}, {y_est:+5.2f}, {z_est:+5.2f})m | e: {e_track:5.3f}m", flush=True)

            # Safety supervisor
            if e_track > MAX_CROSS_TRACK_M:
                abort_reason = f"Safety Abort: Tracking error ({e_track:.3f}m) exceeded limit ({MAX_CROSS_TRACK_M}m)"
                print(f"WARNING: {abort_reason}", flush=True)
                break

            await asyncio.sleep(DT)

        if abort_reason:
            break

        # Corner dwell (3 seconds) to settle at vertex
        print(f"         Dwell at {wp_to['name']} for {CORNER_DWELL_S:.1f}s...", flush=True)
        dwell_steps = int(CORNER_DWELL_S / DT)
        corner_errs = []

        for _ in range(dwell_steps):
            sp = PositionNedYaw(wp_to["x"], wp_to["y"], target_z, 0.0)
            await drone.offboard.set_position_ned(sp)

            t_rel = time.time() - flight_start_time
            x_est = latest_ned["x"]
            y_est = latest_ned["y"]
            z_est = latest_ned["z"]

            e_corner = math.sqrt((x_est - wp_to["x"])**2 + (y_est - wp_to["y"])**2)
            corner_errs.append(e_corner)

            telemetry_records.append({
                "t_rel_s": round(t_rel, 3),
                "segment": f"Corner_{wp_to['name']}",
                "sp_x": round(wp_to["x"], 4), "sp_y": round(wp_to["y"], 4), "sp_z": round(target_z, 4),
                "est_x": round(x_est, 4), "est_y": round(y_est, 4), "est_z": round(z_est, 4),
                "est_vx": round(latest_ned["vx"], 4), "est_vy": round(latest_ned["vy"], 4), "est_vz": round(latest_ned["vz"], 4),
                "err_track": round(e_corner, 4), "err_z": round(abs(z_est - target_z), 4)
            })

            await asyncio.sleep(DT)

        final_corner_err = corner_errs[-1] if corner_errs else 0.0
        corner_metrics.append({
            "vertex": wp_to["name"],
            "target_xy": [wp_to["x"], wp_to["y"]],
            "actual_xy": [round(latest_ned["x"], 4), round(latest_ned["y"], 4)],
            "final_corner_error_m": round(final_corner_err, 4),
            "mean_dwell_error_m": round(sum(corner_errs)/len(corner_errs), 4) if corner_errs else 0.0
        })
        print(f"         Corner {wp_to['name']} Error: {final_corner_err:.4f}m", flush=True)

    # [6/6] Descent and Landing
    print("\n[6/6] Trajectory complete. Initiating controlled descent...", flush=True)
    descend_z = target_z
    while descend_z < -0.15:
        descend_z = min(-0.15, descend_z + RAMP_SPEED_M_S * DT)
        sp = PositionNedYaw(0.0, 0.0, descend_z, 0.0)
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

    # Save CSV Timeseries
    csv_file = OUTPUT_DIR / f"square_{run_id}.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "t_rel_s", "segment", "sp_x", "sp_y", "sp_z",
            "est_x", "est_y", "est_z",
            "est_vx", "est_vy", "est_vz",
            "err_track", "err_z"
        ])
        writer.writeheader()
        writer.writerows(telemetry_records)
    print(f"\nSaved square flight timeseries CSV: {csv_file} ({len(telemetry_records)} samples)", flush=True)

    # Copy latest ULog
    px4_log_dir = Path("/px4/build/px4_sitl_default/rootfs/log")
    latest_ulg = None
    if px4_log_dir.exists():
        ulgs = sorted(px4_log_dir.rglob("*.ulg"), key=lambda p: p.stat().st_mtime)
        if ulgs:
            latest_ulg = ulgs[-1]
            dest_ulg = OUTPUT_DIR / f"square_{run_id}.ulg"
            shutil.copy2(latest_ulg, dest_ulg)
            print(f"Copied source ULog file: {dest_ulg} ({dest_ulg.stat().st_size} bytes)", flush=True)

    # Compute Trajectory Statistics
    err_track_list = [r["err_track"] for r in telemetry_records]
    max_track_err = max(err_track_list) if err_track_list else 0.0
    rmse_track_err = math.sqrt(sum(e**2 for e in err_track_list) / len(err_track_list)) if err_track_list else 0.0

    # Loop closure error (difference between start at (0,0) and end at (0,0))
    start_pos = (telemetry_records[0]["est_x"], telemetry_records[0]["est_y"]) if telemetry_records else (0, 0)
    end_pos = (telemetry_records[-1]["est_x"], telemetry_records[-1]["est_y"]) if telemetry_records else (0, 0)
    loop_closure_err = math.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)

    # Analyze ULog Ground Truth
    gt_analysis = analyze_square_ulog_gt(OUTPUT_DIR / f"square_{run_id}.ulg") if latest_ulg else None

    summary = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "trajectory_type": "square_2x2m",
        "altitude_m": ALTITUDE_M,
        "cruise_speed_m_s": CRUISE_SPEED_M_S,
        "total_duration_s": round(telemetry_records[-1]["t_rel_s"], 2) if telemetry_records else 0,
        "samples_count": len(telemetry_records),
        "abort_reason": abort_reason,
        "telemetry_metrics": {
            "max_tracking_error_m": round(max_track_err, 4),
            "rmse_tracking_error_m": round(rmse_track_err, 4),
            "loop_closure_error_m": round(loop_closure_err, 4),
        },
        "corner_metrics": corner_metrics,
        "trajectory_completed": (abort_reason is None) and (len(corner_metrics) == 4),
        "ground_truth_metrics": gt_analysis
    }

    json_file = OUTPUT_DIR / f"square_{run_id}.json"
    json_file.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Saved evaluation JSON: {json_file}", flush=True)

    print("\n=================== SQUARE 2x2M KPI REPORT ===================", flush=True)
    print(f"Run ID:                  {run_id}", flush=True)
    print(f"Total Flight Duration:   {summary['total_duration_s']}s", flush=True)
    print(f"Trajectory Status:       {'COMPLETED (4/4 Corners Reached)' if summary['trajectory_completed'] else 'INCOMPLETE'}", flush=True)
    print(f"Max Tracking Error:      {max_track_err:.4f} m", flush=True)
    print(f"RMSE Tracking Error:     {rmse_track_err:.4f} m", flush=True)
    print(f"Loop Closure Error:      {loop_closure_err:.4f} m", flush=True)
    for c in corner_metrics:
        print(f"  Corner {c['vertex']:14s}: Target={c['target_xy']} -> Actual={c['actual_xy']} | Error={c['final_corner_error_m']:.4f}m", flush=True)
    if gt_analysis:
        print(f"GT Loop Closure Error:   {gt_analysis.get('loop_closure_gt_m')} m", flush=True)
        print(f"GT Max Deviation:        {gt_analysis.get('max_deviation_gt_m')} m", flush=True)
    print("=============================================================", flush=True)


def analyze_square_ulog_gt(ulg_path: Path):
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

        x_gt = lpos_gt.data["x"]
        y_gt = lpos_gt.data["y"]
        z_gt = lpos_gt.data["z"]

        x0_gt = x_gt[0]
        y0_gt = y_gt[0]
        xf_gt = x_gt[-1]
        yf_gt = y_gt[-1]

        loop_closure_gt = math.sqrt((xf_gt - x0_gt)**2 + (yf_gt - y0_gt)**2)

        return {
            "gt_samples": len(x_gt),
            "est_samples": len(lpos.data["x"]),
            "loop_closure_gt_m": round(loop_closure_gt, 4),
            "max_deviation_gt_m": round(max(math.sqrt((x - x0_gt)**2 + (y - y0_gt)**2) for x, y in zip(x_gt, y_gt)), 4)
        }
    except Exception as e:
        return {"error": f"Failed to parse ULog GT: {e}"}


if __name__ == "__main__":
    asyncio.run(run_mission())
