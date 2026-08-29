#!/usr/bin/env python3
"""扫描 media/ 生成 manifest.json。

目录约定（用户只需往 media/ 里放文件）：
  media/conds/<cond>/video.mp4            # 7 组条件参考视频（vanilla 不需要）
  media/samples/omurice/O01.mp4 ...       # OMU-10 蛋包饭样本视频
  media/samples/namban/N01.mp4 ...        # NAMBAN-5 大布样本视频
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
MEDIA = ROOT / "media"


def vids(d):
    return sorted(x for x in (MEDIA / d).glob("*.mp4"))


def main():
    manifest = {"conds": {}, "samples": {"omurice": [], "namban": []}}
    for d in sorted((MEDIA / "conds").glob("*/video.mp4")):
        manifest["conds"][d.parent.name] = str(d)
    for bench in ["omurice", "namban"]:
        for p in vids(f"samples/{bench}"):
            manifest["samples"][bench].append(str(p))
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    n = {k: len(v) for k, v in manifest["samples"].items()}
    print("conds:", list(manifest["conds"]))
    print("samples:", n)


if __name__ == "__main__":
    main()
