"""Probe script to test Offboard mode arming readiness in non-GPS SITL."""
import asyncio
from mavsdk import System
from mavsdk.offboard import PositionNedYaw, OffboardError

async def run():
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("Waiting for drone connection...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Connected to drone!")
            break

    print("Checking health...")
    async for h in drone.telemetry.health():
        print(f"Local pos OK: {h.is_local_position_ok}, Armable: {h.is_armable}")
        if h.is_local_position_ok:
            break
        await asyncio.sleep(1)

    print("Setting initial setpoint (0, 0, 0)...")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))

    # Stream setpoints before starting offboard
    for _ in range(15):
        await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
        await asyncio.sleep(0.05)

    try:
        print("Starting offboard mode...")
        await drone.offboard.start()
        print("Offboard mode started successfully!")
    except OffboardError as e:
        print(f"Offboard start failed: {e}")

    # Check armable status now
    async for h in drone.telemetry.health():
        print(f"After offboard stream - Armable: {h.is_armable}")
        break

    try:
        print("Attempting to arm...")
        await drone.action.arm()
        print("ARM SUCCESSFUL!")
        await asyncio.sleep(1)
        print("Disarming...")
        await drone.action.disarm()
        print("DISARM SUCCESSFUL!")
    except Exception as e:
        print(f"Arming failed: {e}")

if __name__ == "__main__":
    asyncio.run(run())
