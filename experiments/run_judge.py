#!/usr/bin/env python3
"""裁判实验：对 subject.jsonl 每条文案做 SEEDS(=5) 次独立裁判采样（5 线程并发）。

用法: python3 run_judge.py
输出: out/judge.jsonl   列为 {_id, judge, chi, seed, vas, li, i, raw}
裁判模板轮流 (J1,J2,J3)，权重 w=1/3，亲和因子 chi 按模板固定；seed 轮换即“5 个随机种子”。
重跑安全：已完成条目自动跳过。
"""
import json
import os
import pathlib
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gemini
import prompts

ROOT = pathlib.Path(__file__).parent
JUDGE_MODEL = os.environ.get("GEMINI_JUDGE_MODEL", gemini.MODEL)
N_WORKERS = int(os.environ.get("JUDGE_WORKERS", "5"))


def parse_score(s):
    m = re.search(r"\{\s*\"VAS\"\s*:\s*([\d.]+).*?\"LI\"\s*:\s*([\d.]+).*?\"I\"\s*:\s*([\d.]+)",
                  s, re.S)
    if not m:
        m = re.search(r"(\d+)\s*[^\d]*(\d+)\s*[^\d]*(\d+)", s)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2)), float(m.group(3))


def build_parts(rec):
    parts = [{"type": "text", "text": prompts.JUDGE_USER.format(copy=rec["copy"][:300])}]
    for p in sorted((ROOT / "frames" / f"{rec['bench']}_{rec['sample']}").glob("f*.jpg")):
        parts.append(gemini.img_part(p))
    return parts


def judge_one(rec, tpl, seed):
    _id = f"{rec['_id']}|{seed}"
    try:
        out = gemini.chat(tpl["system"], build_parts(rec), model=JUDGE_MODEL, temp=0.9)
    except Exception as e:
        return ("skip", _id, str(e)[:150])
    sc = parse_score(out)
    if not sc:
        return ("fail", _id, out[:150])
    return ("ok", {"_id": _id, "judge": tpl["name"], "chi": tpl["chi"], "seed": seed,
                   "vas": sc[0], "li": sc[1], "i": sc[2], "raw": out})


def main():
    out = ROOT / "out"
    jlines = out / "judge.jsonl"
    done = set()
    if jlines.exists():
        for l in jlines.read_text().splitlines():
            done.add(json.loads(l)["_id"])
    tasks = []
    for l in (out / "subject.jsonl").read_text().splitlines():
        rec = json.loads(l)
        for seed in range(prompts.SEEDS):
            _id = f"{rec['_id']}|{seed}"
            if _id in done:
                continue
            tpl = prompts.JUDGE_TEMPLATES[seed % len(prompts.JUDGE_TEMPLATES)]
            tasks.append((rec, tpl, seed))
    print(f"待判 {len(tasks)} / {prompts.SEEDS} 种子并发={N_WORKERS}", file=sys.stderr)
    n_ok = n_skip = n_fail = 0
    with jlines.open("a") as f, ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = [ex.submit(judge_one, *t) for t in tasks]
        for fut in as_completed(futs):
            kind, payload, info = fut.result()
            if kind == "ok":
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
                f.flush()
                n_ok += 1
            elif kind == "skip":
                n_skip += 1
                print(f"[judge:skip] {payload}: {info}", file=sys.stderr)
            else:
                n_fail += 1
                print(f"[judge:fail] {payload}: {info}", file=sys.stderr)
    print(f"judge done: ok={n_ok} skip={n_skip} fail={n_fail}", file=sys.stderr)


if __name__ == "__main__":
    main()
