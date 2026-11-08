#!/usr/bin/env bash
# Local Docker-only SITL. No serial devices or host network access.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SOURCE=${N01_PX4_SOURCE:-"$HOME/.local/share/n01-sitl/PX4-Autopilot"}
IMAGE=n01-px4-sitl:v1.16.0
CONTAINER=n01-sitl
COMMIT=6ea3539157ca358c70a515878b77077af7d4611d
case "${1:-help}" in
  image)
    docker build --build-arg USER_ID="$(id -u)" --build-arg GROUP_ID="$(id -g)" -t "$IMAGE" "$ROOT/sim"
    ;;
  build)
    test "$(git -C "$SOURCE" rev-parse HEAD)" = "$COMMIT"
    docker run --rm --cpus=6 --memory=7g --mount "type=bind,src=$SOURCE,dst=/px4" "$IMAGE" \
      bash -lc 'export PATH=/opt/n01-venv/bin:$PATH; make px4_sitl_default -j6'
    ;;
  start)
    test "$(git -C "$SOURCE" rev-parse HEAD)" = "$COMMIT"
    test -x "$SOURCE/build/px4_sitl_default/bin/px4"
    # Clean stale parameter files to prevent uncalibrated IMU skips
    rm -f "$SOURCE/build/px4_sitl_default/rootfs/parameters"*.bson
    # Internal network deliberately excludes physical FC and outbound UDP routes.
    docker network inspect n01-sim >/dev/null 2>&1 || docker network create --internal n01-sim >/dev/null
    docker run --init -dit --name "$CONTAINER" --network n01-sim --cpus=6 --memory=7g --shm-size=512m \
      -p 14550:14550/udp \
      --mount "type=bind,src=$SOURCE,dst=/px4" \
      --mount "type=bind,src=$ROOT,dst=/workspace" \
      --mount "type=bind,src=$ROOT/sim,dst=/n01,readonly" \
      -e HEADLESS=1 -e LIBGL_ALWAYS_SOFTWARE=1 -e GZ_IP=127.0.0.1 -e GZ_PARTITION=n01 \
      -e PX4_GZ_MODELS=/px4/Tools/simulation/gz/models \
      -e PX4_GZ_WORLDS=/px4/Tools/simulation/gz/worlds \
      -e PX4_GZ_PLUGINS=/px4/build/px4_sitl_default/src/modules/simulation/gz_plugins \
      -e GZ_SIM_RESOURCE_PATH=/px4/Tools/simulation/gz/models:/px4/Tools/simulation/gz/worlds \
      -e GZ_SIM_SYSTEM_PLUGIN_PATH=/px4/build/px4_sitl_default/src/modules/simulation/gz_plugins \
      -e GZ_SIM_SERVER_CONFIG_PATH=/px4/src/modules/simulation/gz_bridge/server.config \
      -e PX4_GZ_WORLD=indoor_flow \
      -e PX4_PARAM_SYS_HAS_GPS=0 -e PX4_PARAM_SIM_GPS_USED=0 \
      -e PX4_PARAM_EKF2_GPS_CTRL=0 -e PX4_PARAM_EKF2_EV_CTRL=0 \
      -e PX4_PARAM_EKF2_OF_CTRL=1 -e PX4_PARAM_COM_ARM_WO_GPS=1 \
      -e PX4_PARAM_NAV_DLL_ACT=0 \
      -e PX4_PARAM_COM_OBL_RC_ACT=4 -e PX4_PARAM_COM_OF_LOSS_T=1.0 \
      "$IMAGE" bash -lc 'export PATH=/opt/n01-venv/bin:$PATH; exec xvfb-run -a make px4_sitl gz_x500_flow'
    ;;
  gui|rec)
    [ "$1" = rec ] && REC_DISPLAY=:99
    test "$(git -C "$SOURCE" rev-parse HEAD)" = "$COMMIT"
    test -x "$SOURCE/build/px4_sitl_default/bin/px4"
    rm -f "$SOURCE/build/px4_sitl_default/rootfs/parameters"*.bson
    xhost +local:docker >/dev/null 2>&1 || true
    docker network inspect n01-sim >/dev/null 2>&1 || docker network create --internal n01-sim >/dev/null
    DRI_FLAG=()
    if [ -d /dev/dri ]; then
      DRI_FLAG=(--device /dev/dri:/dev/dri)
      for g in video render; do
        gid=$(getent group "$g" 2>/dev/null | cut -d: -f3 || true)
        [ -n "$gid" ] && DRI_FLAG+=(--group-add "$gid")
      done
    fi
    docker run --init -dit --name "$CONTAINER" --network n01-sim --cpus=6 --memory=7g --shm-size=1g \
      "${DRI_FLAG[@]}" \
      -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
      -e DISPLAY="${REC_DISPLAY:-${DISPLAY:-:0}}" ${REC_DISPLAY:+-e HEADLESS=1} \
      -p 14550:14550/udp \
      --mount "type=bind,src=$SOURCE,dst=/px4" \
      --mount "type=bind,src=$ROOT,dst=/workspace" \
      --mount "type=bind,src=$ROOT/sim,dst=/n01,readonly" \
      -e GZ_IP=127.0.0.1 -e GZ_PARTITION=n01 \
      -e PX4_GZ_MODELS=/px4/Tools/simulation/gz/models \
      -e PX4_GZ_WORLDS=/px4/Tools/simulation/gz/worlds \
      -e PX4_GZ_PLUGINS=/px4/build/px4_sitl_default/src/modules/simulation/gz_plugins \
      -e GZ_SIM_RESOURCE_PATH=/px4/Tools/simulation/gz/models:/px4/Tools/simulation/gz/worlds \
      -e GZ_SIM_SYSTEM_PLUGIN_PATH=/px4/build/px4_sitl_default/src/modules/simulation/gz_plugins \
      -e GZ_SIM_SERVER_CONFIG_PATH=/px4/src/modules/simulation/gz_bridge/server.config \
      -e PX4_GZ_WORLD=indoor_flow \
      -e PX4_PARAM_SYS_HAS_GPS=0 -e PX4_PARAM_SIM_GPS_USED=0 \
      -e PX4_PARAM_EKF2_GPS_CTRL=0 -e PX4_PARAM_EKF2_EV_CTRL=0 \
      -e PX4_PARAM_EKF2_OF_CTRL=1 -e PX4_PARAM_COM_ARM_WO_GPS=1 \
      -e PX4_PARAM_NAV_DLL_ACT=0 \
      -e PX4_PARAM_COM_OBL_RC_ACT=4 -e PX4_PARAM_COM_OF_LOSS_T=1.0 \
      "$IMAGE" bash -lc "export PATH=/opt/n01-venv/bin:\$PATH; $([ "$1" = rec ] && echo 'Xvfb :99 -screen 0 1280x720x24 -ac +extension GLX +render -noreset & sleep 2;') exec make px4_sitl gz_x500_flow"
    ;;
  console)
    docker attach --detach-keys=ctrl-] "$CONTAINER"
    ;;
  logs)
    docker logs --tail 120 "$CONTAINER"
    ;;
  smoke)
    docker exec "$CONTAINER" /opt/n01-venv/bin/python /n01/smoke.py
    ;;
  hover)
    docker exec "$CONTAINER" /opt/n01-venv/bin/python /workspace/src/mission_hover.py "${@:2}"
    ;;
  square)
    docker exec "$CONTAINER" /opt/n01-venv/bin/python /workspace/src/mission_square.py "${@:2}"
    ;;
  fault)
    docker exec "$CONTAINER" /opt/n01-venv/bin/python /workspace/src/test_fault_injection.py "${@:2}"
    ;;
  stop)
    docker stop --time 15 "$CONTAINER"
    docker rm "$CONTAINER"
    ;;
  *)
    printf 'Usage: bash sim/sitl.sh {image|build|start|gui|console|logs|smoke|hover|square|fault|stop}\n'
    ;;
esac
