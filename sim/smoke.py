"""Read-only MAVSDK smoke check, only inside the isolated n01-sitl container."""
import asyncio
import json
import subprocess
from dataclasses import asdict, is_dataclass
from importlib.metadata import version
from pathlib import Path

from mavsdk import System


def fields(value):
    if is_dataclass(value):
        return asdict(value)
    return {key: val for key, val in vars(value).items() if not key.startswith('_')}


async def main():
    if not Path('/.dockerenv').exists() or not Path('/px4/build/px4_sitl_default/bin/px4').exists():
        raise RuntimeError('Run only via docker exec in the isolated n01-sitl container')
    drone = System()
    await drone.connect(system_address='udpin://0.0.0.0:14540')
    async with asyncio.timeout(45):
        async for state in drone.core.connection_state():
            if state.is_connected:
                break
        # Allow initial estimator and telemetry streams to settle.
        await asyncio.sleep(5)
        result = {'mavsdk': version('mavsdk'), 'connected': True, 'commands_sent': 'none; read-only'}
        result['armed'] = await anext(drone.telemetry.armed())
        result['health'] = fields(await anext(drone.telemetry.health()))
        result['position_velocity_ned'] = str(await anext(drone.telemetry.position_velocity_ned()))
        result['params'] = {}
        for name in ['SYS_AUTOSTART', 'SYS_HAS_GPS', 'SIM_GPS_USED', 'EKF2_GPS_CTRL', 'EKF2_EV_CTRL', 'EKF2_OF_CTRL', 'EKF2_RNG_CTRL']:
            result['params'][name] = await drone.param.get_param_int(name)
        print(json.dumps(result, indent=2, default=str), flush=True)
        assert not result['armed'], 'Smoke check expects disarmed SITL'
        assert result['params']['SYS_AUTOSTART'] == 4021, 'Wrong SITL airframe'
        for name in ['SYS_HAS_GPS', 'SIM_GPS_USED', 'EKF2_GPS_CTRL', 'EKF2_EV_CTRL']:
            assert result['params'][name] == 0, f'Unexpected aiding source: {name}'
        assert result['params']['EKF2_OF_CTRL'] == 1, 'Optical flow not enabled'
        assert result['health']['is_local_position_ok'], 'Local estimate invalid'
        checks = {
            'sensor_optical_flow': ['integration_timespan_us:', 'quality:'],
            'distance_sensor': ['current_distance:'],
            'vehicle_local_position': ['xy_valid: True', 'z_valid: True'],
            'estimator_status_flags': [
                'cs_opt_flow: True', 'cs_rng_hgt: True', 'cs_gnss_pos: False',
                'cs_gnss_vel: False', 'cs_gps_hgt: False', 'cs_ev_pos: False',
                'cs_ev_vel: False', 'cs_ev_hgt: False',
            ],
            'estimator_aid_src_optical_flow': ['fused: True', 'innovation_rejected: False'],
        }
        for topic, required in checks.items():
            output = subprocess.check_output(
                ['/px4/build/px4_sitl_default/bin/px4-listener', topic, '-n', '1'],
                text=True, timeout=5,
            )
            print(output, flush=True)
            for token in required:
                assert token in output, f'{topic}: missing {token}'
        print('SITL_DISARMED_SMOKE_PASS; not hover, square, fault tests or G1', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
