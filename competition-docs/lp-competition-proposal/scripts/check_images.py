#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 md 中的图片引用与 images/ 文件夹的对应关系。

用法:
    python check_images.py 计划书.md [图片文件夹]

输出:
    - 需要但缺失的图片
    - 已引用的图片数量
    - 文件夹里未被引用的图片（用户额外提供）

存在缺失图片时退出码为 1。
"""

import argparse
import os
import re
import sys


IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")


def main(argv=None):
    ap = argparse.ArgumentParser(description="检查 md 图片引用与图片文件夹")
    ap.add_argument("md", help="要检查的 .md 文件")
    ap.add_argument("images_dir", nargs="?", default="images", help="图片文件夹（默认 images/）")
    args = ap.parse_args(argv)

    md_path = os.path.abspath(args.md)
    if not os.path.isfile(md_path):
        print(f"[错误] 找不到文件: {md_path}")
        return 1

    with open(md_path, "r", encoding="utf-8-sig") as f:
        text = f.read()

    refs = [m.group(1).strip() for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text)]
    md_dir = os.path.dirname(md_path)
    missing, found = [], []
    for ref in refs:
        path = ref if os.path.isabs(ref) else os.path.join(md_dir, ref)
        (found if os.path.isfile(path) else missing).append(ref)

    images_dir = os.path.abspath(args.images_dir)
    unused = []
    if os.path.isdir(images_dir):
        existing = {
            name.lower()
            for name in os.listdir(images_dir)
            if name.lower().endswith(IMAGE_EXT)
        }
        unused = sorted(existing - {os.path.basename(r).lower() for r in refs})

    print(f"图片引用 {len(refs)} 个：已有 {len(found)}，缺失 {len(missing)}")
    if missing:
        print("\n[缺失] 需要但找不到的图片：")
        for r in missing:
            print("  -", r)
    if unused:
        print("\n[未引用] 图片文件夹中未被引用的文件（用户额外提供）：")
        for u in unused:
            print("  -", u)
    if missing:
        print("\n[失败] 存在缺失图片，请补图或用文字替代")
        return 1
    print("\n[通过] 所有引用图片均存在")
    return 0


if __name__ == "__main__":
    sys.exit(main())
