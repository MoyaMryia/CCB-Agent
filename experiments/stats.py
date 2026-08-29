#!/usr/bin/env python3
"""统计：VAS/LI/I 均值±std、paired t-test，生成论文表。

协议（见 protocol.md）：
  1) 每条 (cond, sample, variant) 有 SEEDS=5 次裁判采样；
  2) 对裁判采样：r̄_χ = Σ_s χ·w·score/N（χ 亲和因子，w=1/3）；
  3) more_agents：5 变体 r̄_χ 取 VAS 最高者聚合；
  4) VAS% = 100·σ(r̄χ − k)，k 由 vanilla pilot（前 3 样本）按 σ 反变换校准；
  5) 显著性：paired t-test（样本配对）。
用法: python3 stats.py   （参照数据缺省不影响主表，表3 另输出）
输出: out/results.json, out/table_body.md, out/table3.tex
"""
import json
import math
import pathlib
import sys

import numpy as np
from scipy import stats as st

ROOT = pathlib.Path(__file__).parent
W = 1 / 3


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def load_refs(fname):
    rows = []
    p = ROOT / "out" / fname
    if p.exists():
        for l in p.read_text().splitlines():
            if l.strip():
                rows.append(json.loads(l))
    return rows


def collect(judge_rows, subj_rows):
    """(cond, bench, sample, variant) -> r̄χ 5 种子均值（若齐）。"""
    cells = {}
    n_per = {}
    for j in judge_rows:
        parts = j["_id"].split("|")
        key = tuple(parts[:4])
        rec = cells.setdefault(key, {"vas": 0.0, "li": 0.0, "i": 0.0})
        rec["vas"] += j["chi"] * W * j["vas"]
        rec["li"] += j["chi"] * W * j["li"]
        rec["i"] += j["chi"] * W * j["i"]
        n_per[key] = n_per.get(key, 0) + 1
    # 仅保留满分裁判数（5）的 cell
    ok = {k: v for k, v in cells.items() if n_per[k] >= 5}
    return ok, subj_rows


def sample_values(cells, subj_rows, cond):
    """返回 dict: (bench, sample) -> r̄χ 三元组。（more_agents 取最优变体）"""
    out = {}
    for (c, bench, sample, variant), r in cells.items():
        if c != cond:
            continue
        key = (bench, sample)
        if cond == "more_agents":
            old = out.get(key)
            if old is None or r["vas"] > old["vas"]:
                out[key] = r
        elif variant == "0":
            out[key] = r
    return out


def report(cond, out, k=None, label=None):
    vals = list(out.values())
    vas_raw = np.array([v["vas"] for v in vals])
    li = np.array([v["li"] for v in vals])
    i = np.array([v["i"] for v in vals])
    r = {
        "n": len(vals),
        "vas_raw": float(vas_raw.mean()),
        "vas_std_raw": float(vas_raw.std(ddof=1)) if len(vals) > 1 else 0,
        "li": float(li.mean()), "li_std": float(li.std(ddof=1)) if len(vals) > 1 else 0,
        "i": float(i.mean()), "i_std": float(i.std(ddof=1)) if len(vals) > 1 else 0,
    }
    if k is not None:
        vas_pct = 100 * sigmoid(np.array([v["vas"] for v in vals]) - k)
        r["vas"] = float(vas_pct.mean())
        r["vas_std_pct"] = float(vas_pct.std(ddof=1)) if len(vals) > 1 else 0
        r["vas_vals"] = [100 * float(sigmoid(v["vas"] - k)) for v in vals]
    return r


def pair_p(cells, subj_rows, cond, base="baseline"):
    a, b = [], []
    for key, v in sorted(sample_values(cells, subj_rows, cond).items()):
        o = sample_values(cells, subj_rows, base).get(key)
        if o:
            a.append(v["vas"]); b.append(o["vas"])
    if len(a) < 2:
        return float("nan")
    return float(st.ttest_rel(a, b).pvalue)


def main():
    subj = [json.loads(l) for l in (ROOT / "out" / "subject.jsonl").read_text().splitlines()]
    judge = [json.loads(l) for l in (ROOT / "out" / "judge.jsonl").read_text().splitlines()]
    cells, _ = collect(judge, subj)
    conds = sorted({k[0] for k in cells})

    # vanilla pilot 校准 k（前 3 样本：omurice O01..O03）
    van = sample_values(cells, subj, "vanilla")
    pilot = [van[(b, s)] for (b, s) in van if b == "omurice"][:3]
    k = float(np.mean([v["vas"] for v in pilot])) - math.log(0.872 / (1 - 0.872)) if pilot else 0.0

    rep = {}
    for c in conds:
        sv = sample_values(cells, subj, c)
        rep[c] = report(c, sv, k=k)
    rep["_k"] = k
    rep["_p"] = {}
    for c in ["sp", "dp", "sp_dp", "more_agents", "flow", "dp_penguin", "dp_chickensoup", "dp_film73"]:
        if c in rep:
            rep["_p"][c] = pair_p(cells, subj, c)
    if "sp_dp" in rep and "dp" in rep:
        a = [(k_, v["vas"]) for k_, v in sample_values(cells, subj, "sp_dp").items()]
        b = [(k_, v["vas"]) for k_, v in sample_values(cells, subj, "dp").items()]
        am = {x: y for x, y in a}; bm = dict(b)
        ap = [y for x, y in am.items() if x in bm]
        bp = [bm[x] for x in am if x in bm]
        rep["_p"]["spdp_vs_dp"] = float(st.ttest_rel(ap, bp).pvalue) if len(ap) > 2 else float("nan")

    # —— 表3：参照模型（Gemini 2.5 Flash）——
    ref3 = {}
    jref = load_refs("judge_ref.jsonl")
    sref = load_refs("subject_ref.jsonl")
    if jref:
        rcells, _ = collect(jref, sref)
        for c in ["vanilla", "sp_dp"]:
            sv = sample_values(rcells, sref, c)
            if sv:
                ref3[c] = report(c, sv, k=k)

    (ROOT / "out" / "results.json").write_text(
        json.dumps({"k": k, "conds": rep, "reference": ref3}, indent=2, ensure_ascii=False))

    order = ["vanilla", "baseline", "sp", "dp", "sp_dp", "more_agents", "flow",
             "dp_penguin", "dp_chickensoup", "dp_film73"]
    lines = []
    for c in order:
        if c not in rep:
            continue
        r = rep[c]
        lines.append(f"{c:16s} VAS={r['vas']:6.2f}±{r['vas_std_pct']:5.2f}  "
                     f"LI={r['li']:5.1f}±{r['li_std']:4.1f}  I={r['i']:5.1f}±{r['i_std']:4.1f}"
                     f"  n={r['n']}")
    (ROOT / "out" / "table_body.md").write_text("\n".join(lines) + "\n")
    print(f"k(校准常数) = {k:.4f}")
    print("\n".join(lines))
    print("p(paired t-test vs baseline):")
    for c, p in rep["_p"].items():
        print(f"  {c:16s} p={p:.4f}")
    if ref3:
        print("\n表3 参照模型 (Gemini 2.5 Flash):")
        for c in ["vanilla", "sp_dp"]:
            if c in ref3:
                r = ref3[c]
                print(f"  {c:10s} VAS={r['vas']:.2f}±{r['vas_std_pct']:.2f} (n={r['n']})")


if __name__ == "__main__":
    main()
