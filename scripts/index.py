#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LittlePotato 个人工具库 —— 索引维护脚本。

自动扫描 skills/、mcp/、tools/、plugins/、workflows/、prompts/ 下的真实条目，
重新生成各 README 中位于标记对之间的索引块：

    <!-- lp:index:begin:<key> -->
    ...自动生成...
    <!-- lp:index:end:<key> -->

用法：
    python scripts/index.py            # 重新生成所有索引块并写回文件
    python scripts/index.py --check    # 只检查索引是否最新；有漂移则退出码 1
    python scripts/index.py --dry-run  # 打印将要更新的文件，不写入

约定：
    - 只索引真实存在的条目，不会凭空生成内容。
    - 技能条目以 skills/<分类>/<条目>/SKILL.md 为准，说明取自 front-matter 的 description。
    - 其他条目以 <分类>/<条目>/README.md 为准，说明取自 README 首个标题后的第一段。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_DESC = 160


class MarkerError(RuntimeError):
    pass


# ---------- 文本工具 ----------

def _read(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _clean(desc: str) -> str:
    """把说明整理成适合表格单元格的单行文本。"""
    desc = re.sub(r"[*_`>]", "", desc)
    desc = re.sub(r"\s+", " ", desc).strip()
    if len(desc) > MAX_DESC:
        desc = desc[: MAX_DESC - 1].rstrip() + "…"
    return desc


def _pipe(text: str) -> str:
    return str(text).replace("|", "\\|")


def _cell(text: str) -> str:
    return _pipe(_clean(text))


def first_paragraph(text: str) -> str:
    """README 中首个标题之后的第一个非空段落。"""
    lines = text.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        if ln.startswith("#"):
            start = i + 1
            break
    buf: list[str] = []
    for ln in lines[start:]:
        s = ln.strip()
        if not s:
            if buf:
                break
            continue
        if s.startswith("#"):
            break
        buf.append(s)
    return " ".join(buf).strip()


def parse_front_matter(text: str) -> dict[str, str]:
    """解析 SKILL.md 的 YAML front-matter（兼容 >- 折叠的多行 description）。"""
    m = re.match(r"\A---\s*\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return {}
    fm: dict[str, str] = {}
    key: str | None = None
    for ln in m.group(1).splitlines():
        if ln.startswith((" ", "\t")):
            if key and ln.strip():
                fm[key] = (fm.get(key, "") + " " + ln.strip()).strip()
            continue
        if ":" in ln:
            k, v = ln.split(":", 1)
            key = k.strip()
            v = v.strip().strip('"\'')
            fm[key] = "" if v in {">", ">-", "|", "|-", "|+", ">+"} else v
        else:
            key = None
    return {k: v.strip() for k, v in fm.items() if v}


# ---------- 条目发现 ----------

def skill_items() -> list[dict]:
    items = []
    root = REPO_ROOT / "skills"
    if not root.exists():
        return items
    for skill_md in sorted(root.rglob("SKILL.md")):
        item_dir = skill_md.parent
        rel = item_dir.relative_to(REPO_ROOT)
        parts = rel.parts
        category = parts[1] if len(parts) >= 3 else ""
        text = _read(skill_md)
        fm = parse_front_matter(text)
        desc = fm.get("description") or first_paragraph(text) or "（未填写说明）"
        items.append(
            {
                "name": fm.get("name") or item_dir.name,
                "category": category,
                "rel": rel.as_posix() + "/",
                "desc": desc,
            }
        )
    return items


def dir_items(category: str) -> list[dict]:
    items = []
    root = REPO_ROOT / category
    if not root.exists():
        return items
    for d in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        readme = d / "README.md"
        if not readme.exists():
            continue
        items.append(
            {
                "name": d.name,
                "rel": f"{category}/{d.name}/",
                "desc": first_paragraph(_read(readme)) or "（未填写说明）",
            }
        )
    return items


def plugin_items() -> list[dict]:
    items = []
    root = REPO_ROOT / "plugins"
    if not root.exists():
        return items
    for d in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        readme = d / "README.md"
        desc = first_paragraph(_read(readme)) if readme.exists() else "平台插件"
        has_items = any(p.is_dir() and not p.name.startswith(".") for p in d.iterdir())
        items.append(
            {
                "name": d.name,
                "rel": f"plugins/{d.name}/",
                "desc": desc,
                "status": "已有条目" if has_items else "空，待填充",
            }
        )
    return items


def prompt_items() -> list[dict]:
    items = []
    root = REPO_ROOT / "prompts"
    if not root.exists():
        return items
    for p in sorted(root.iterdir()):
        if p.name == "README.md" or p.name.startswith("."):
            continue
        if p.is_dir():
            readme = p / "README.md"
            desc = first_paragraph(_read(readme)) if readme.exists() else "提示词模板目录"
            rel = f"prompts/{p.name}/"
        else:
            desc = first_paragraph(_read(p)) if p.suffix.lower() == ".md" else ""
            rel = f"prompts/{p.name}"
        items.append({"name": p.name, "rel": rel, "desc": desc or "（未填写说明）"})
    return items


# ---------- 表格生成 ----------

def link(name: str, rel: str) -> str:
    return f"[{name}]({rel})"


def table(rows: list[list[str]], header: list[str] | None = None) -> str:
    """rows: 每行为单元格列表，首列是含链接的显示文本。"""
    if not rows:
        return "当前为空（尚无条目）。"
    cols = len(rows[0])
    header = header or (["名称"] + ["说明"] * (cols - 1))
    lines = ["| " + " | ".join(header) + " |", "|" + "------|" * cols]
    for r in rows:
        cells = [_pipe(r[0])] + [_cell(c) for c in r[1:]]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def gen_skills_root() -> str:
    items = skill_items()
    if not items:
        return "当前为空（尚无技能）。"
    cats: list[str] = []
    for it in items:
        if it["category"] not in cats:
            cats.append(it["category"])
    blocks = []
    for cat in cats:
        display = cat.replace("-", " ").title()
        rows = [[link(it["name"], it["rel"]), it["desc"]] for it in items if it["category"] == cat]
        blocks.append(f"### {display}\n\n{table(rows)}")
    return "\n\n".join(blocks)


def gen_skills_index() -> str:
    items = skill_items()
    if not items:
        return "当前为空（尚无技能）。"
    lines = ["| 技能 | 分类 | 说明 |", "|------|------|------|"]
    for it in items:
        rel = it["rel"].split("skills/", 1)[-1]
        lines.append(
            f"| {_pipe(link(it['name'], rel))} | {_cell(it['category'])} | {_cell(it['desc'])} |"
        )
    return "\n".join(lines)


def gen_simple(category: str, strip: str | None = None) -> str:
    rows = []
    for it in dir_items(category):
        rel = it["rel"]
        if strip and rel.startswith(strip + "/"):
            rel = rel[len(strip) + 1 :]
        rows.append([link(it["name"], rel), it["desc"]])
    return table(rows)


def gen_plugins() -> str:
    rows = [
        [link(it["name"], it["rel"].split("plugins/", 1)[-1]), it["desc"], it["status"]]
        for it in plugin_items()
    ]
    return table(rows, header=["平台", "说明", "状态"])


def gen_prompts() -> str:
    rows = [
        [link(it["name"], it["rel"].split("prompts/", 1)[-1]), it["desc"]]
        for it in prompt_items()
    ]
    return table(rows)


# ---------- 生成规格 ----------

SPEC = [
    ("README.md", "skills", gen_skills_root),
    ("README.md", "mcp", lambda: gen_simple("mcp")),
    ("README.md", "tools", lambda: gen_simple("tools")),
    ("skills/README.md", "skills", gen_skills_index),
    ("mcp/README.md", "mcp", lambda: gen_simple("mcp", strip="mcp")),
    ("tools/README.md", "tools", lambda: gen_simple("tools", strip="tools")),
    ("plugins/README.md", "plugins", gen_plugins),
    ("workflows/README.md", "workflows", lambda: gen_simple("workflows", strip="workflows")),
    ("prompts/README.md", "prompts", gen_prompts),
]


def splice(text: str, key: str, content: str, nl: str) -> str:
    begin = f"<!-- lp:index:begin:{key} -->"
    end = f"<!-- lp:index:end:{key} -->"
    start = text.find(begin)
    if start < 0:
        raise MarkerError(f"缺少开始标记: {begin}")
    end_pos = text.find(end, start + len(begin))
    if end_pos < 0:
        raise MarkerError(f"缺少结束标记: {end}")
    block = begin + nl + nl + content.replace("\n", nl) + nl + nl + end
    return text[:start] + block + text[end_pos + len(end) :]


def run(dry_run: bool, check: bool) -> int:
    changed: list[str] = []
    for rel, key, gen in SPEC:
        path = REPO_ROOT / rel
        if not path.exists():
            raise MarkerError(f"文件不存在: {rel}")
        text = _read(path)
        new_text = splice(text, key, gen(), _newline(text))
        if new_text == text:
            continue
        changed.append(rel)
        if not (dry_run or check):
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(new_text)
    changed_unique = list(dict.fromkeys(changed))
    if dry_run:
        for rel in changed_unique:
            print(f"[dry-run] 将更新: {rel}")
        if not changed:
            print("索引全部最新，无需更新。")
        return 0
    if check:
        if changed_unique:
            print("索引需要更新:", ", ".join(changed_unique))
            return 1
        print("索引全部最新。")
        return 0
    for rel in changed_unique:
        print(f"已更新: {rel}")
    if not changed:
        print("索引全部最新，无需更新。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="LittlePotato 仓库索引维护脚本")
    ap.add_argument("--check", action="store_true", help="只检查，有漂移时退出码 1")
    ap.add_argument("--dry-run", action="store_true", help="只预览将更新的文件，不写入")
    args = ap.parse_args()
    try:
        return run(dry_run=args.dry_run, check=args.check)
    except MarkerError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        print("提示：在对应 README 中加入标记对后重试。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
