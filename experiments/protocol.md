# CCB-Agent 真实实验协议（satire-to-real）

> 论文《涌现式氛围对齐》的数据从"编的"转为"真跑的"。规模按荒诞最小可行：**OMU-10 / NAMBAN-5**。
> 一切定义、常数、代码均在本目录，可复现。任何不真实的地方（如数据量）均在论文中如实披露。

## 规模

| 项 | 值 |
|---|---|
| 基准 | OMU-10（蛋包饭片段）、NAMBAN-5（大布片段）——论文标注 OMU-1K/NAMBAN-500，方法节如实写 "illustrative subset, n=10/5" |
| 条件 | vanilla（无视频）、baseline（奶龙）、+SP、+DP、+SP+DP、More Agents、Flow，共 7 |
| 种子 | 每个（条件, 样本）做 5 次独立裁判采样（temp=0.9，J1/J2/J3 模板轮换），即论文的"5 个随机种子" |
| 调用量 | 主体：15×6 + more_agents 额外 4×15 = 150 次左右；裁判：15×6×5 ≈ 450 次 |

## 流程

1. `media/` 放入素材：`conds/<cond>/video.mp4`（7 条件参考视频）+ `samples/omurice/O0*.mp4` ×10 + `samples/namban/N0*.mp4` ×5
2. `python3 init_manifest.py` → manifest.json
3. `python3 prep.py` → 每视频抽 4 帧（2%/35%/70%/95%，宽≤512）
4. `export GEMINI_API_KEY=...`（GEMINI_BASE / GEMINI_MODEL 可选）
5. `python3 run_subject.py` → out/subject.jsonl
6. `python3 run_judge.py` → out/judge.jsonl
7. `python3 stats.py` → out/results.json + table_body.md

## 计分定义（写回方法节）

- 裁判模板 J1/J2/J3，亲和因子 χ ∈ {0.9, 1.0, 1.1} 显式固定（论文定义 {0.9,1.1} 处扩展为三等份并说明），权重 w=1/3。
- 每条（条件, 样本）5 次裁判采样：r̄ = (1/5)Σ s χ·w·r_s
- VAS% = 100·σ(r̄ − k)，k 由 vanilla 条件 pilot（前 3 样本均值）经 σ 反变换校准：k = r̄_pilot − logit(0.872)。这是"为把分数变得有区分度而校准常数"的诚实做法——k 固定后对全部条件通用，非拟合。
- LI / I 直接报告平均原始分。
- 显著性：对（条件 vs baseline、SP+DP vs DP）做 paired t-test（样本配对），报告 p 值。

## 已知局限（论文中如实披露）

- n=10/5，任何显著性与泛化均为笑话性质；方差故意巨大，此即论文的荒诞性来源之一。
- 视频均以 4 关键帧图片表示（"一帧胜千言"），非真正视频输入。
- 裁判用 Gemini 本体，存在自评倾向——论文已预言（"裁判亲和因子"），如实标注。
- more_agents：5 个变体聚合取 VAS 最高者；flow：模板化多步提示。
