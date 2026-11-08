#!/usr/bin/env bash
# Chờ EKF hội tụ: bit 17 (local_position_estimate) trong arming_check_error_flags phải xoá.
# Dùng: bash sim/ekf_gate.sh [giây]. Exit 0 nếu hội tụ.
T=${1:-150}; end=$((SECONDS+T))
while [ $SECONDS -lt $end ]; do
  f=$(docker exec n01-sitl /px4/build/px4_sitl_default/bin/px4-listener health_report -n 1 2>/dev/null | grep arming_check_error | grep -oE ': [0-9]+' | tr -d ': ')
  if [ -n "$f" ] && [ $(( (f >> 17) & 1 )) -eq 0 ]; then echo "EKF OK flags=$f"; exit 0; fi
  sleep 3
done
echo "EKF not converged"; exit 1
