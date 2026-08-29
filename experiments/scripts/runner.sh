#!/usr/bin/env bash
cd "$(dirname "$0")/.."
echo "[runner] start $(date)" >> out/runner.log
.venv/bin/python3 run_subject.py >> out/runner.log 2>&1
echo "[runner] subject done $(date)" >> out/runner.log
.venv/bin/python3 run_judge.py >> out/runner.log 2>&1
echo "[runner] judge done $(date)" >> out/runner.log
.venv/bin/python3 stats.py >> out/runner.log 2>&1
echo "[runner] stats done $(date)" >> out/runner.log
