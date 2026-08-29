#!/usr/bin/env python3
"""Gemini client (OpenAI-compatible). Key: GEMINI_API_KEY env or .uuapi.key."""
import base64
import json
import os
import pathlib
import time
import urllib.error
import urllib.request

BASE = os.environ.get("GEMINI_BASE", "https://uuapi.io/v1")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.7-flash")


def api_key() -> str:
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k:
        kf = pathlib.Path(__file__).with_name(".uuapi.key")
        if kf.exists():
            k = kf.read_text().strip()
    if not k:
        raise SystemExit("未设置 GEMINI_API_KEY，且无 .uuapi.key")
    return k


def img_part(path, mime="image/jpeg"):
    b64 = base64.b64encode(pathlib.Path(path).read_bytes()).decode()
    return {"type": "image_url",
            "image_url": {"url": f"data:{mime};base64,{b64}"}}


def chat(system, user_parts, model=MODEL, temp=0.6, retries=5, timeout=180,
         max_tokens=512):
    messages = [{"role": "user", "content": user_parts}]
    if system:
        messages = [{"role": "system", "content": system}] + messages
    payload = {"model": model, "messages": messages,
               "temperature": temp, "max_tokens": max_tokens}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f"{BASE}/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": "Bearer " + api_key(),
                         "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            return d["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code in (429, 500, 503) and attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {body}")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")
