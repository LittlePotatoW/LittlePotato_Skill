#!/usr/bin/env python3
"""生成符合小土豆代码风格的 Python 包骨架"""
import re
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "assets" / "package_template"
PLACEHOLDER = "{{package}}"


def normalize(name: str) -> str:
    # 非字母数字下划线统一转下划线 得到合法 Python 包名
    return re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())


def scaffold(package_name: str, out_dir: str | Path) -> Path:
    # 复制模板 替换目录名与文件内容中的 {{package}} 占位符
    pkg = normalize(package_name)
    if not pkg:
        raise ValueError(f"非法包名: {package_name!r}")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    created = []
    for src in sorted(TEMPLATE_DIR.rglob("*")):
        rel = src.relative_to(TEMPLATE_DIR)
        rel = Path(str(rel).replace(PLACEHOLDER, pkg))
        dst = out / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8").replace(PLACEHOLDER, pkg)
        dst.write_text(text, encoding="utf-8")
        created.append(dst)
    print(f"Scaffolded package '{pkg}' -> {out}")
    for p in created:
        print(f"  + {p.relative_to(out)}")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[2] != "--path":
        print("Usage: python scaffold_package.py <package-name> --path <output-directory>")
        sys.exit(1)
    scaffold(sys.argv[1], sys.argv[3])
