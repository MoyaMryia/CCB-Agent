#!/usr/bin/env python3
"""参照模型裁判（表3）：对 subject_ref.jsonl 用主裁判（默认 gemini-3.7-flash）5 次采样。"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gemini
import prompts
from run_judge import parse_score

ROOT = pathlib.Path(__file__).parent
JUDGE_MODEL = __import__("os").environ.get("GEMINI_JUDGE_MODEL", gemini.MODEL)


def main():
    jlines = ROOT / "out" / "judge_ref.jsonl"
    done = set()
    if jlines.exists():
        for l in jlines.read_text().splitlines():
            done.add(json.loads(l)["_id"])
    with jlines.open("a") as f:
        for l in (ROOT / "out" / "subject_ref.jsonl").read_text().splitlines():
            rec = json.loads(l)
            parts = [{"type": "text", "text": prompts.JUDGE_USER.format(copy=rec["copy"][:300])}]
            for p in sorted((ROOT / "frames" / f"{rec['bench']}_{rec['sample']}").glob("f*.jpg")):
                parts.append(gemini.img_part(p))
            for seed in range(prompts.SEEDS):
                tpl = prompts.JUDGE_TEMPLATES[seed % len(prompts.JUDGE_TEMPLATES)]
                _id = f"{rec['_id']}|{seed}"
                if _id in done:
                    continue
                out = gemini.chat(tpl["system"], parts, model=JUDGE_MODEL, temp=0.9)
                sc = parse_score(out)
                if not sc:
                    print(f"[judge-ref:parse-fail] {_id}: {out[:120]}", file=sys.stderr)
                    continue
                f.write(json.dumps({"_id": _id, "judge": tpl["name"], "chi": tpl["chi"],
                                    "seed": seed, "vas": sc[0], "li": sc[1], "i": sc[2],
                                    "raw": out}, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[judge-ref] {_id}", file=sys.stderr)
    print("ref judge done")


if __name__ == "__main__":
    main()
