#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lp-md2docx 转换入口：一个 .md + 图片文件夹 → .docx。

用法:
    python convert.py 文档.md [输出.docx] [--profile 样式配置] [--images 图片目录]
"""

import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from docx_builder import build_docx
    from md_parser import Heading, ImageBlock, parse_front_matter, parse_md
    from yaml_mini import load_yaml_file
except ImportError as exc:
    print(f"[错误] 缺少依赖: {exc}")
    print("请先安装: pip install python-docx")
    sys.exit(1)


SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(SKILL_ROOT, "assets", "profiles")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Markdown + 图片文件夹 → 带样式表和多级标题的 Word 文档"
    )
    ap.add_argument("input_md", help="输入的 .md 文件路径")
    ap.add_argument("output_docx", nargs="?", help="输出的 .docx 路径（默认与输入同名）")
    ap.add_argument(
        "--profile",
        default="default",
        help="样式表配置名或 yaml 路径（默认 default，即 assets/profiles/default.yaml）",
    )
    ap.add_argument("--images", default=None, help="图片文件夹（默认：md 同目录下的 images/）")
    args = ap.parse_args(argv)

    md_path = os.path.abspath(args.input_md)
    if not os.path.isfile(md_path):
        print(f"[错误] 找不到文件: {md_path}")
        return 1

    # 定位样式表配置
    profile_arg = args.profile
    profile_path = profile_arg if os.path.isfile(profile_arg) else None
    if profile_path is None:
        name = profile_arg if profile_arg.endswith(".yaml") else profile_arg + ".yaml"
        candidate = os.path.join(PROFILES_DIR, name)
        if os.path.isfile(candidate):
            profile_path = candidate
    if profile_path is None:
        print(f"[错误] 找不到样式表配置: {profile_arg}（已尝试 {PROFILES_DIR}）")
        return 1

    cfg = load_yaml_file(profile_path)
    with open(md_path, "r", encoding="utf-8-sig") as f:
        raw_text = f.read()
    meta = parse_front_matter(raw_text)
    blocks = parse_md(raw_text)

    md_dir = os.path.dirname(md_path)
    images_dir = os.path.abspath(args.images) if args.images else os.path.join(md_dir, "images")

    out = os.path.abspath(args.output_docx or os.path.splitext(md_path)[0] + ".docx")
    out_dir = os.path.dirname(out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    build_docx(
        blocks,
        cfg,
        out,
        images_dir=images_dir,
        md_dir=md_dir,
        title=meta.get("title"),
    )

    heads = [b for b in blocks if isinstance(b, Heading)]
    imgs = [b for b in blocks if isinstance(b, ImageBlock)]
    cnt = Counter(b.level for b in heads)
    print(f"完成: {out}")
    print(
        "标题 {} 个: ".format(len(heads))
        + " ".join(f"H{l}={cnt.get(l, 0)}" for l in range(1, 7) if cnt.get(l))
        + f" | 图片 {len(imgs)} 个 | 样式表: {os.path.basename(profile_path)}"
    )
    print("\n标题结构（顺序保持原样）:")
    for b in blocks:
        if isinstance(b, Heading):
            print("  " * (b.level - 1) + f"H{b.level} {b.text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
