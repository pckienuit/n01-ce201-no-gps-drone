#!/usr/bin/env bash
# Chuẩn bị khung hình GUI Gazebo trên :99 trước khi quay (cửa sổ 1280x720, camera bám drone, unpause)
C=${CONTAINER:-n01-sitl}
# GUI client gắn sau khi EKF hội tụ (GUI render CPU làm EKF không hội tụ nếu chạy cùng lúc boot)
docker exec -d -e DISPLAY=:99 $C gz sim -g
sleep 25
gzs(){ docker exec $C gz service -s "$1" --reqtype "$2" --reptype gz.msgs.Boolean --timeout 3000 --req "$3"; }
gzs /world/indoor_flow/control gz.msgs.WorldControl 'pause: false'
gzs /gui/follow gz.msgs.StringMsg "data: 'x500_flow_0'"
gzs /gui/follow/offset gz.msgs.Vector3d 'x: -2.0, y: -2.0, z: 1.6'
python3 - <<'PY'
import ctypes,subprocess
x=ctypes.CDLL('libX11.so.6');d=x.XOpenDisplay(b':99')
for l in subprocess.check_output(['xwininfo','-display',':99','-root','-tree'],text=True).splitlines():
    if '"Gazebo Sim"' in l:
        w=int(l.split()[0],16);x.XMoveResizeWindow(d,w,0,0,1280,720);x.XFlush(d);print('resized',hex(w));break
x.XCloseDisplay(d)
PY
