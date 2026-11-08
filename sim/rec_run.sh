#!/usr/bin/env bash
# Quay GUI Gazebo thật trên :99 trong lúc chạy một mission.
# Dùng: bash sim/rec_run.sh <hover|square|fault> <out.mp4>
set -u
cd "$(dirname "$0")/.."
M=$1; OUT=$2
ffmpeg -y -loglevel error -f x11grab -draw_mouse 0 -framerate 20 -video_size 1280x720 -i :99.0 \
  -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p "$OUT" &
F=$!; sleep 3
timeout 300 bash sim/sitl.sh "$M"; echo "mission_exit=$?"
sleep 4; kill -INT $F; wait $F
echo REC_DONE
