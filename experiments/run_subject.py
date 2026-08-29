#!/usr/bin/env python3
"""主体实验：每条件 × 每样本 → 生成 60 字氛围文案。

用法: python3 run_subject.py
输出: out/subject.jsonl   列为 {cond, bench, sample, variant, copy}
more_agents 条件跑 5 个变体（真实数量聚合）；其余跑 1 次。
"""
import json
import pathlib
import sys

pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gemini
import prompts

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)


def frames_for(prefix, key, sample_stem=None):
    base = ROOT / "frames" / f"{prefix}_{key}" if sample_stem is None \
        else ROOT / "frames" / f"{prefix}_{sample_stem}"
    return sorted(base.glob("f*.jpg"))


def main():
    m = json.loads((ROOT / "manifest.json").read_text())
    samples = [(b, pathlib.Path(p).stem) for b, ps in m["samples"].items() for p in ps]
    print("样本数:", len(samples), file=sys.stderr)
    lines = OUT / "subject.jsonl"
    exist = 0
    done_lines = set()
    if lines.exists():
        for l in lines.read_text().splitlines():
            done_lines.add(json.loads(l)["_id"])
    with lines.open("a") as f:
        for bench, stem in samples:
            parts = [{"type": "text", "text": prompts.USER_TASK}]
            for p in frames_for(bench, stem):
                parts.append(gemini.img_part(p))
            for cond in prompts.COND_SYSTEM:
                variants = 5 if cond == "more_agents" else 1
                for v in range(variants):
                    _id = f"{cond}|{bench}|{stem}|{v}"
                    if _id in done_lines:
                        continue
                    cond_parts = []
                    cfr = m["conds"].get(cond)
                    if cfr:
                        for p in frames_for("conds", cond):
                            cond_parts.append(gemini.img_part(p))
                    sys_parts = [{"type": "text", "text": prompts.COND_SYSTEM[cond]}]
                    user_parts = cond_parts + parts if cond_parts else parts
                    if cond_parts:
                        user_parts = cond_parts + parts
                    try:
                        copy = gemini.chat(sys_parts[0]["text"], user_parts)
                    except Exception as e:
                        print(f"[subject:skip] {_id}: {e}", file=sys.stderr)
                        continue
                    rec = {"_id": _id, "cond": cond, "bench": bench, "sample": stem,
                           "variant": v, "copy": copy}
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    exist += 1
                    print(f"[subject] {_id}", file=sys.stderr)
    print("新增:", exist, file=sys.stderr)


if __name__ == "__main__":
    main()
