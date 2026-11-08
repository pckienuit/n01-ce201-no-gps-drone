#!/usr/bin/env bash
# Quay hover + square + fault trên GUI Gazebo thật, mỗi đoạn một file, container sạch mỗi lần.
# EKF phải hội tụ (ekf_gate.sh) trước khi quay; thử lại tối đa 3 lần mỗi đoạn.
cd "$(dirname "$0")/.."
for M in ${MISSIONS:-hover square fault}; do
  for try in 1 2 3; do
    echo "=== $M (lần $try) ==="
    bash sim/sitl.sh stop >/dev/null 2>&1
    bash sim/sitl.sh rec >/dev/null 2>&1
    sleep 50
    bash sim/rec_setup.sh >/dev/null 2>&1
    docker exec n01-sitl gz service -s /gui/follow/offset --reqtype gz.msgs.Vector3d --reptype gz.msgs.Boolean --timeout 3000 --req "x: -1.6, y: 0, z: 0.9" >/dev/null 2>&1
    if ! bash sim/ekf_gate.sh 120; then continue; fi
    timeout 420 bash sim/rec_run.sh $M sim/evidence/gui_$M.mp4 > /tmp/rec_$M.log 2>&1
    pkill -INT -x ffmpeg 2>/dev/null; sleep 2
    docker exec n01-sitl pkill -9 -f mavsdk_server 2>/dev/null
    if grep -qE "KPI Status: +PASS|mission_exit=0" /tmp/rec_$M.log && ! grep -q "^ERROR" /tmp/rec_$M.log; then
      echo "$M OK: $(grep -E 'KPI Status|Max Horizontal' /tmp/rec_$M.log | tr -s ' \n' ' ')"; break
    fi
    echo "$M thất bại lần $try: $(grep -E '^ERROR' /tmp/rec_$M.log | head -1)"
  done
done
echo ALL_DONE
