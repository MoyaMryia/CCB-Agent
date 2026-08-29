# CCB-Agent：涌现式氛围对齐（认真胡扯版）

> **吐槽声明**：这是一个 Sokal 式讽刺论文（hoax paper）的**完整实验套件**。
> 我们以最大规模的严肃性执行了最小规模的真实实验：**所有数字都来自真实模型 API 输出**，
> 但论文的研究对象是一句蛋包饭咒语，基准规模是 OMU-10 / NAMBAN-5（论文骄傲地称作 1K/500）。
> 用一句 Pumera 主义名言概括：*Will any crap we put into the prompt increase its 'atmosphere alignment'?* ——**会的**。

## 这是什么

- `shit_ccb_agent.tex` —— 讽刺论文（IEEEtran 格式，XeLaTeX 编译）
- `experiments/` —— 真实实验装置：训练体（Gemini 3.7 Flash，经 OpenAI 兼容端点）
  在 7+3 个条件 × 15 个样本上生成 60 字文案，裁判模型按固定 rubric 打 VAS/LI/I 分，
  统计脚本输出结果表与 paired t-test p 值。
- 论文中的每个关键数字都可以由本仓库 **一条命令复现**。
- **我们在论文里明确告知读者：规模是 10/5，不是 1K/500。**

## 复现（两步）

```bash
# 1. 下载全部素材（B 站，需要 firefox 登录 cookie，10-20 分钟）
BROWSER=firefox ./experiments/fetch.sh

# 2. 跑实验（约 650 次 Gemini 调用；环境变量 GEMINI_API_KEY + GEMINI_BASE）
cd experiments
export GEMINI_API_KEY="sk-your-key"
export GEMINI_BASE="https://your-ai-gateway/v1"   # 任意 OpenAI 兼容端点
export GEMINI_MODEL="gemini-3.7-flash"            # 也可指定参照模型
python3 run_subject.py   # 条件 × 样本 → 文案（out/subject.jsonl）
python3 run_judge.py     # 5 次裁判采样 × 每条文案（out/judge.jsonl）
python3 stats.py         # → out/results.json + 表格主体
```

零依赖提示：`experiments/.venv` 装有 numpy/scipy/yt-dlp/py-spy；核心 API 调用只用标准库。

## 目录结构

```
Rubbish/
├── README.md                   # 本文档
├── .gitignore
├── paper/
│   ├── shit_ccb_agent.tex/pdf   # 论文中文版（XeLaTeX 编译，目录内编译）
│   ├── rubbish_ccb_agent.tex/pdf# 论文英文版（IEEEtran conference）
│   ├── LOGO1.png / LOGO2.png    # 页眉 Logo
│   └── refs/
│       └── cordis2025-spatiotemporal-composability.pdf  # 引用文献（cordis2025）
└── experiments/
    ├── fetch.sh                 # 素材一键复现（入口）
    ├── manifest.json            # 素材清单与样本编号
    ├── prompts.py               # 全部条件/裁判提示模板与常量
    ├── gemini.py                # OpenAI 兼容客户端（限流/重试/节流）
    ├── init_manifest.py / prep.py / bili_search.py
    ├── run_subject.py / run_judge.py / run_reference.py / run_judge_ref.py
    ├── stats.py                 # 统计与显著性（results.json / 表格）
    ├── scripts/                 # 长程编排：runner.sh / watcher.sh / finalize.sh
    ├── media/                   # 原始素材（git 忽略；fetch.sh 可复现）
    ├── frames/                  # 每视频 4 帧（512px，已入库可验证）
    └── out/                     # 实验原始记录（jsonl 全量入库）
```

## 三个"垃圾"基线的真实实现（不造假，公平输）

| 论文基线 | 实验实现 | 说明 |
|---|---|---|
| 数量聚合（More Agents） | `more_agents` 条件：同一输入 5 次独立采样，聚合取 VAS 最高者 | 真实 ensemble |
| 图式形式化（Flow） | `flow` 条件：显式三步模块化提示（压缩→挑战→输出） | 与顶点活动图同构 |
| 综述堆积（Survey） | `vanilla` 条件：无任何视频/技巧的朴素系统提示 | 综述本来就"无实验"，这就是它的可测量表现 |

## 计分协议（全在 `experiments/protocol.md`）

- 裁判 = Gemini 本体（自评倾向在论文中自豪地公开）
- VAS% = 100·σ(r̄ − k)，k 由 vanilla pilot 校准（真实 pilot 数据，非常拟合，非常蒙对）
- 亲和因子 χ ∈ {0.9, 1.0, 1.1} 按裁判模板显式固定（论文定义 {0.9, 1.1}，扩展为三等分，如实公开）

## 素材来源清单

条件视频：奶龙（BV12hqpYrEdq）、蛋包饭咒语（BV1ov4y167HY 00:41–01:04）、
南蛮大布原文（BV1NWsqzfETn 前 41s）、鸟粪对照组企鹅（BV1pK411H7nM，
"研究称企鹅可将粪便喷射到1.3米外"，企鹅亦鸟，此即鸟粪之替身）、
鸡汤对照组奥利给（BV1Zr4y1D7cf）、1973 配音（BV1CF411G7ME）。
样本：OMU-10 蛋包饭片段、NAMBAN-5 大布二创。全部在 `experiments/manifest.json` + `fetch.sh`。

## 作者

Maxim Wayne & MoyaMryia —— 本文未引用任何基金资助（这正好证明我们的诚实）。
撰写与实验编排辅助于：opencode（deepseek-v4-flash-vision-exp）。
