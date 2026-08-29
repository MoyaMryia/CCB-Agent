#!/usr/bin/env python3
"""参照模型（表3）：GEMINI_MODEL 设为参照模型（如 gemini-2.5-flash），
只跑 vanilla 与 sp_dp 两条件 × 全部样本；裁判仍用 GEMINI_JUDGE_MODEL（默认同主实验 3.7）。

用法: GEMINI_MODEL=gemini-2.5-flash python3 run_reference.py
输出: out/subject_ref.jsonl（再跑 run_judge_ref.py）
"""
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gemini
import prompts

ROOT = pathlib.Path(__file__).parent
CONDS = ["vanilla", "sp_dp"]


def frames_for(prefix, key):
    return sorted((ROOT / "frames" / f"{prefix}_{key}").glob("f*.jpg"))


def main():
    m = json.loads((ROOT / "manifest.json").read_text())
    samples = [(b, pathlib.Path(p).stem) for b, ps in m["samples"].items() for p in ps]
    lines = ROOT / "out" / "subject_ref.jsonl"
    done = set()
    if lines.exists():
        for l in lines.read_text().splitlines():
            done.add(json.loads(l)["_id"])
    with lines.open("a") as f:
        for bench, stem in samples:
            parts = [{"type": "text", "text": prompts.USER_TASK}]
            for p in frames_for(bench, stem):
                parts.append(gemini.img_part(p))
            for cond in CONDS:
                _id = f"{cond}|{bench}|{stem}|0"
                if _id in done:
                    continue
                copy = gemini.chat(prompts.COND_SYSTEM[cond], parts)
                f.write(json.dumps({"_id": _id, "cond": cond, "bench": bench,
                                    "sample": stem, "variant": 0, "copy": copy},
                                   ensure_ascii=False) + "\n")
                f.flush()
                print(f"[ref] {_id}", file=sys.stderr)
    print("ref subject done, rows =", sum(1 for _ in open(lines)))


if __name__ == "__main__":
    main()
