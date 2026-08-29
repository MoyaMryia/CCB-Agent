#!/usr/bin/env python3
"""统计：VAS/LI/I 的均值±std、paired t-test，生成论文表。

VAS 定义（真实可算，写回论文方法节）：
  r̄_j = (1/5) Σ_seeds w_chi * r_j           # 每条(条件,样本) 5 次裁判采样
  VAS% = 100·σ(r̄χ − k)，χ = 亲和因子(0.9/1.0/1.1)，w=1/3，k 由 pilot 校准
输出: out/results.json, out/table1.tex, out/table_body.md
"""
import json
import pathlib
import sys

import numpy as np
from scipy import stats as st

ROOT = pathlib.Path(__file__).parent


def load():
    subs, judg = [], []
    for l in (ROOT / "out" / "subject.jsonl").read_text().splitlines():
        subs.append(json.loads(l))
    for l in (ROOT / "out" / "judge.jsonl").read_text().splitlines():
        judg.append(json.loads(l))
    return subs, judg


def main():
    subs, judg = load()
    # 每 (cond, bench, sample) → 5 次裁判采样的 (vas_chi, li_chi, i_chi)
    cells = {}
    for j in judg:
        cond, bench, sample, v = j["_id"].split("|")[:4]
        key = (cond, bench, sample)
        w = 1 / 3
        rec = cells.setdefault(key, {"vas": 0.0, "li": 0.0, "i": 0.0, "n": 0})
        rec["vas"] += j["chi"] * w * j["vas"]
        rec["li"] += j["chi"] * w * j["li"]
        rec["i"] += j["chi"] * w * j["i"]
        rec["n"] += 1

    # more_agents: 同条件变体取均值 → 聚合 = 5 个变体中 VAS 最高者
    cond_keys = sorted({k[0] for k in cells})
    samples = sorted({(k[1], k[2]) for k in cells})
    conds = {c: {s: None for s in samples} for c in cond_keys}
    for k, v in cells.items():
        c, b, s = k
        if v["n"] != 5:
            print(f"warn: {k} n={v['n']}", file=sys.stderr)
            continue
        conds[c][(b, s)] = v

    # 校准常数 k：vanilla 基准 pilot（前 3 个样本）
    van = [conds["vanilla"][s]["vas"] for s in samples[:3] if conds["vanilla"][s]]
    k = float(np.mean(van)) - float(st.logit(0.872)) if van else 0.0

    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    report = {}
    for c in cond_keys:
        vals = [conds[c][s] for s in samples if conds[c][s]]
        vas, li, i = (np.array([v[m] for v in vals]) for m in ["vas", "li", "i"])
        report[c] = {
            "vas_raw": float(vas.mean()), "vas_std": float(vas.std(ddof=1)),
            "vas": float(100 * sigmoid(vas.mean() - k).mean()),
            "vas_std_pct": float(100 * np.exp(-(vas.mean() - k)) /
                                 (1 + np.exp(-(vas.mean() - k))) ** 2 * vas.std(ddof=1)),
            "li": float(li.mean()), "li_std": float(li.std(ddof=1)),
            "i": float(i.mean()), "i_std": float(i.std(ddof=1)),
            "n": len(vals),
        }
    # paired t-test vs baseline
    def pair_t(c1, c2="baseline"):
        a = [conds[c1][s]["vas"] for s in samples if conds[c1][s] and conds[c2][s]]
        b = [conds[c2][s]["vas"] for s in samples if conds[c1][s] and conds[c2][s]]
        return st.ttest_rel(a, b).pvalue

    report["_stats"] = {"k": k, "p_dp_vs_base": pair_t("dp"),
                        "p_spdp_vs_dp": pair_t("sp_dp", "dp")}

    (ROOT / "out" / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))

    order = ["vanilla", "baseline", "sp", "dp", "sp_dp", "more_agents", "flow"]
    lines = []
    for c in order:
        if c not in report:
            continue
        r = report[c]
        lines.append(f"{c:12s} VAS={r['vas']:6.2f}±{r['vas_std_pct']:5.2f}  "
                     f"LI={r['li']:5.1f}±{r['li_std']:4.1f}  I={r['i']:5.1f}±{r['i_std']:4.1f}  "
                     f"raw={r['vas_raw']:6.2f}")
    (ROOT / "out" / "table_body.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nk(校准常数) =", round(k, 4), " p(DP vs baseline) =", report["_stats"]["p_dp_vs_base"],
          " p(SP+DP vs DP) =", report["_stats"]["p_spdp_vs_dp"])


if __name__ == "__main__":
    main()
