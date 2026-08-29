#!/usr/bin/env bash
cd "$(dirname "$0")/.."
while pgrep -f "run_subject.py" > /dev/null; do sleep 30; done
echo "[watcher] subject done at $(date)" >> out/watch.log
.venv/bin/python3 run_judge.py >> out/watch.log 2>&1
echo "[watcher] judge done at $(date)" >> out/watch.log
