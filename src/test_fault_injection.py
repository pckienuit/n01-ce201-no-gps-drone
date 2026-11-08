#!/usr/bin/env python3
"""
N01 CE201 - Fault Injection & Failsafe Verification
Simulates companion computer / MAVLink loss during hover at 1.0m altitude.
Terminates MAVSDK communication process mid-air and verifies that PX4 autopilot
triggers Offboard loss failsafe (COM_OBL_RC_ACT=4 -> Auto-Land) and disarms safely.
"""

import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from mavsdk import System
from mavsdk.offboard import PositionNedYaw, OffboardError

ALTITUDE_M = 1.0
DT = 0.05
OUTPUT_DIR = Path("/workspace/sim/evidence/flight_logs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def run_fault_test():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"==================================================", flush=True)
    print(f"N01 Fault Injection Test (Run ID: {run_id})", flush=True)
    print(f"Simulating: Complete Companion Link Loss during 1.0m hover", flush=True)
    print(f"Expected: PX4 failsafe triggers Land mode & disarms safely", flush=True)
    print(f"==================================================", flush=True)

    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")

    print("[1/5] Connecting to drone...", flush=True)
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("      Connected to PX4!", flush=True)
            break

    print("[2/5] Configuring failsafe parameters...", flush=True)
    await drone.param.set_param_int("COM_OBL_RC_ACT", 4)  # 4 = Land mode on offboard loss
    await drone.param.set_param_float("COM_OF_LOSS_T", 1.0) # 1.0s timeout
    print("      Set COM_OBL_RC_ACT=4 (Land) and COM_OF_LOSS_T=1.0s", flush=True)

    print("[3/5] Starting Offboard stream and arming...", flush=True)
    start_wait = time.time()
    while time.time() - start_wait < 30.0:
        async for h in drone.telemetry.health():
            if h.is_local_position_ok:
                print("      EKF2 Local Position is VALID!", flush=True)
                break
        else:
            await asyncio.sleep(1.0)
            continue
        break

    for _ in range(25):
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
        await asyncio.sleep(DT)

    try:
        await drone.offboard.start()
        await drone.action.arm()
        print("      Armed in Offboard mode!", flush=True)
    except Exception as e:
        print(f"ERROR: Arming failed: {e}", flush=True)
        sys.exit(1)

    # Climb to 1.0m
    print("[4/5] Climbing to 1.0m altitude...", flush=True)
    curr_z = 0.0
    while curr_z > -ALTITUDE_M:
        curr_z = max(-ALTITUDE_M, curr_z - 0.4 * DT)
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, curr_z, 0.0))
        await asyncio.sleep(DT)

    # Stabilize at 1.0m hover
    print("      Reached 1.0m altitude. Stabilizing for 4.0s...", flush=True)
    for _ in range(int(4.0 / DT)):
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, -ALTITUDE_M, 0.0))
        await asyncio.sleep(DT)

    # FAULT INJECTION: Kill MAVSDK communication completely
    print("\n[5/5] >>> FAULT INJECTED: Terminating companion link (killing mavsdk_server)! <<<", flush=True)
    subprocess.run(["pkill", "-9", "-f", "mavsdk_server"], check=False)
    print("      Companion link terminated. Monitoring PX4 uORB state directly...", flush=True)

    t_fault = time.time()
    failsafe_triggered = False
    safe_disarm = False
    transitions = []

    # Monitor directly via PX4 uORB listener for up to 25 seconds
    for _ in range(50):
        time.sleep(0.5)
        elapsed = time.time() - t_fault

        # Read vehicle_status
        out_status = subprocess.run(
            ["/px4/build/px4_sitl_default/bin/px4-listener", "vehicle_status", "-n", "1"],
            capture_output=True, text=True, timeout=5
        ).stdout

        # Read vehicle_local_position
        out_pos = subprocess.run(
            ["/px4/build/px4_sitl_default/bin/px4-listener", "vehicle_local_position", "-n", "1"],
            capture_output=True, text=True, timeout=5
        ).stdout

        nav_state = "UNKNOWN"
        arming_state = "UNKNOWN"
        z_pos = 0.0
        vz = 0.0

        for line in out_status.splitlines():
            if "nav_state:" in line:
                nav_state = line.split(":")[1].strip()
            if "arming_state:" in line:
                arming_state = line.split(":")[1].strip()

        for line in out_pos.splitlines():
            line_str = line.strip()
            if line_str.startswith("z:"):
                z_pos = float(line_str.split(":")[1].strip())
            if line_str.startswith("vz:"):
                vz = float(line_str.split(":")[1].strip())

        nav_name = {
            "14": "OFFBOARD",
            "18": "AUTO_LAND",
            "4": "AUTO_LOITER",
            "2": "POSCTL",
            "1": "ALTCTL"
        }.get(nav_state, f"STATE_{nav_state}")
        arm_name = {"2": "ARMED", "1": "DISARMED"}.get(arming_state, f"STATE_{arming_state}")

        transitions.append({
            "elapsed_s": round(elapsed, 2),
            "nav_state": nav_name,
            "arming_state": arm_name,
            "z_m": round(z_pos, 3),
            "vz_m_s": round(vz, 3)
        })

        print(f"      [t+{elapsed:4.1f}s] Mode: {nav_name:12s} | Alt AGL: {-z_pos:5.2f}m | vz: {vz:+5.2f}m/s | Arm: {arm_name}", flush=True)

        if nav_name == "AUTO_LAND" or nav_state == "18":
            failsafe_triggered = True

        if arm_name == "DISARMED" or arming_state == "1":
            safe_disarm = True
            print(f"      [t+{elapsed:4.1f}s] Autopilot safely LANDED and DISARMED on ground!", flush=True)
            break

    test_pass = failsafe_triggered and safe_disarm

    summary = {
        "run_id": run_id,
        "test_name": "companion_link_loss_fault_injection",
        "altitude_at_fault_m": ALTITUDE_M,
        "failsafe_mode_triggered": failsafe_triggered,
        "safe_disarm_on_ground": safe_disarm,
        "test_result": "PASS" if test_pass else "FAIL",
        "state_transitions": transitions
    }

    out_file = OUTPUT_DIR / f"fault_test_{run_id}.json"
    out_file.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\nSaved fault injection report: {out_file}", flush=True)
    print(f"FAULT INJECTION RESULT: {'PASS (Safe failsafe confirmed)' if test_pass else 'FAIL'}", flush=True)
    print("==================================================", flush=True)


if __name__ == "__main__":
    asyncio.run(run_fault_test())
