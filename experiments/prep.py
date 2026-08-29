#!/usr/bin/env python3
"""对 manifest.json 中的每个视频抽 N 帧（2%/35%/70%/95% 时间点），缩到宽 ≤512px。

输出: frames/<key>/f0.jpg ... f3.jpg
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent
N = 4
PTS = [0.02, 0.35, 0.70, 0.95]
W = 512


def extract(video: pathlib.Path, outdir: pathlib.Path):
    outdir.mkdir(parents=True, exist_ok=True)
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(video)]).decode().strip())
    for i, t in enumerate(PTS):
        ts = dur * t
        subprocess.run([
            "ffmpeg", "-v", "quiet", "-y", "-ss", f"{ts:.3f}", "-i", str(video),
            "-frames:v", "1", "-vf", f"scale={W}:-2", str(outdir / f"f{i}.jpg")],
            check=True)


def main():
    m = json.loads((ROOT / "manifest.json").read_text())
    jobs = [(v, "conds_" + k) for k, v in m["conds"].items()] + \
           [(v, "omurice_" + pathlib.Path(v).stem) for v in m["samples"]["omurice"]] + \
           [(v, "namban_" + pathlib.Path(v).stem) for v in m["samples"]["namban"]]
    for v, key in jobs:
        od = ROOT / "frames" / key
        if (od / f"f{N-1}.jpg").exists():
            print("skip", key)
            continue
        extract(pathlib.Path(v), od)
        print("ok", key)


if __name__ == "__main__":
    main()
