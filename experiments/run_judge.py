#!/usr/bin/env python3
"""裁判实验：对 subject.jsonl 每条文案做 SEEDS(=5) 次独立裁判采样。

用法: python3 run_judge.py
输出: out/judge.jsonl   列为 {_id, judge, chi, seed, vas, li, i, raw}
裁判模板轮流 (J1,J2,J3)，权重 w=1/3，亲和因子 chi 按模板固定；seed 轮换即“5 个随机种子”。
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gemini
import prompts

ROOT = pathlib.Path(__file__).parent
JUDGE_MODEL = __import__("os").environ.get("GEMINI_JUDGE_MODEL",
                                           __import__("os").environ.get(
                                               "GEMINI_MODEL", "gemini-3.7-flash"))


def parse_score(s):
    m = re.search(r"\{\s*\"VAS\"\s*:\s*([\d.]+).*?\"LI\"\s*:\s*([\d.]+).*?\"I\"\s*:\s*([\d.]+)",
                  s, re.S)
    if not m:
        m = re.search(r"(\d+)\s*[^\d]*(\d+)\s*[^\d]*(\d+)", s)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2)), float(m.group(3))


def main():
    lines = OUT = ROOT / "out"
    lines.mkdir(exist_ok=True)
    jlines = OUT / "judge.jsonl"
    done = set()
    if jlines.exists():
        for l in jlines.read_text().splitlines():
            done.add(json.loads(l)["_id"])
    with jlines.open("a") as f:
        for l in (OUT / "subject.jsonl").read_text().splitlines():
            rec = json.loads(l)
            parts = [{"type": "text", "text": prompts.JUDGE_USER.format(copy=rec["copy"][:300])}]
            # 裁判只看样本帧（与条件视频无关，理由：裁判只评价成品）
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
                    print(f"[judge:parse-fail] {_id}: {out[:120]}", file=sys.stderr)
                    continue
                jl = {"_id": _id, "judge": tpl["name"], "chi": tpl["chi"], "seed": seed,
                      "vas": sc[0], "li": sc[1], "i": sc[2], "raw": out}
                f.write(json.dumps(jl, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[judge] {_id}", file=sys.stderr)


if __name__ == "__main__":
    main()
