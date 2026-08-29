#!/usr/bin/env bash
cd "$(dirname "$0")/.."
while ! grep -q "\[runner\] judge done" out/runner.log 2>/dev/null; do sleep 20; done
echo "[finalize] judge done detected $(date)" >> out/runner.log
GEMINI_MODEL=gemini-2.5-flash .venv/bin/python3 run_reference.py >> out/runner.log 2>&1
echo "[finalize] ref subject done $(date)" >> out/runner.log
.venv/bin/python3 run_judge_ref.py >> out/runner.log 2>&1
echo "[finalize] ref judge done $(date)" >> out/runner.log
.venv/bin/python3 stats.py >> out/runner.log 2>&1
echo "[finalize] stats done $(date)" >> out/runner.log
