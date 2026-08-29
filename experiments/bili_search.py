#!/usr/bin/env python3
"""B 站搜索工具：借用 firefox cookie + wbi 签名，输出视频候选。

用法: python3 bili_search.py <关键词>... [--limit 8]
输出: bvid | 时长 | UP主 | 标题
"""
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request

import yt_dlp.cookies

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
COOKIES = yt_dlp.cookies.extract_cookies_from_browser("firefox")

MIXIN_KEY = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
             27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
             37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22,
             25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIES))
    with opener.open(req, timeout=20) as r:
        return json.load(r)


def mixin_key():
    d = get("https://api.bilibili.com/x/web-interface/nav")["data"]["wbi_img"]
    img = d["img_url"].rsplit("/", 1)[-1].split(".")[0]
    sub = d["sub_url"].rsplit("/", 1)[-1].split(".")[0]
    raw = img + sub
    return "".join(raw[i] for i in MIXIN_KEY)[:32]


def search(keyword, mk, limit=8):
    params = {"keyword": keyword, "search_type": "video", "page": 1, "page_size": 20}
    params["wts"] = int(time.time())
    qs = urllib.parse.urlencode(sorted(params.items()))
    params["w_rid"] = hashlib.md5((qs + mk).encode()).hexdigest()
    url = "https://api.bilibili.com/x/web-interface/wbi/search/type?" + urllib.parse.urlencode(params)
    d = get(url)
    return [r for r in d.get("data", {}).get("result") or [] if r.get("type") == "video"][:limit]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mk = mixin_key()
    for kw in args:
        print(f"===== {kw} =====")
        try:
            for r in search(kw, mk):
                dur = r.get("duration") or ""
                print(f"{r.get('bvid')} | {dur} | {r.get('author','')} | {r.get('title','')}")
        except Exception as e:
            print("ERR:", str(e)[:200])


if __name__ == "__main__":
    main()
