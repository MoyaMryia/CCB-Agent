#!/usr/bin/env bash
# 素材复现下载：从 B 站拉取全部实验素材（含咒语/大布段裁剪）。
# 依赖: yt-dlp + ffmpeg；B 站风控需要登录 cookie（默认 firefox，可改 --cookies-from-browser）
set -euo pipefail
cd "$(dirname "$0")/experiments"
BROWSER="${BROWSER:-firefox}"

dl() { # <输出> <BV>
  mkdir -p "$(dirname "$1")"
  yt-dlp --cookies-from-browser "$BROWSER" --no-check-certificates \
    -f "bv*+ba/best" -o "$1" "https://www.bilibili.com/video/$2"
  echo "  [ok] $2 -> $1"
}

echo "== 条件视频 =="
dl /tmp/ccb_baseline_full.mp4 BV12hqpYrEdq && cp /tmp/ccb_baseline_full.mp4 media/conds/baseline/video.mp4
dl /tmp/ccb_sp_full.mp4 BV1ov4y167HY && ffmpeg -v quiet -y -ss 41 -i /tmp/ccb_sp_full.mp4 -t 23 -c copy media/conds/sp/video.mp4
dl /tmp/ccb_dp_full.mp4 BV1NWsqzfETn && ffmpeg -v quiet -y -i /tmp/ccb_dp_full.mp4 -t 41 -c copy media/conds/dp/video.mp4
dl media/conds/penguin/video.mp4 BV1pK411H7nM
dl media/conds/chickensoup/video.mp4 BV1Zr4y1D7cf
dl media/conds/film73/video.mp4 BV1CF411G7ME

echo "== OMU-10 =="
I=1
for bv in BV1Bf4y1s7Rc BV1PZby6VEYx BV19Y4y1i7Gm BV1QB4y147xX BV1A24y1a74Q \
         BV1mx2FBtEyn BV1LW411M7JS BV11P41187xx BV1ZggN6TE2o BV1yJ411L7qV; do
  dl "media/samples/omurice/O0${I}.mp4" "$bv"; I=$((I+1))
done

echo "== NAMBAN-5 =="
I=1
for bv in BV13TVJz4EBi BV1Nv4y1u7qc BV1Ha1cBJExg BV12k8W6dEUJ BV1yWozBbEf2; do
  dl "media/samples/namban/N0${I}.mp4" "$bv"; I=$((I+1))
done

echo "== 抽帧 =="
python3 init_manifest.py
python3 prep.py
echo "全部素材就绪"
