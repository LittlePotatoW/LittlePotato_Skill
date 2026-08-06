# -*- coding: utf-8 -*-
"""Markdown 块解析器（保持顺序，不改动内容）。

输出模型：
- Heading(level, text)      # 标题，level 1~6
- Paragraph(text)           # 正文段落
- ListItem(text, ordered, number, level)   # 列表项（level 为缩进层级）
- ImageBlock(src, alt)      # 独立成行的图片
- TableBlock(header, rows, caption)        # GFM 管道表格
- CodeBlock(text)           # 围栏代码块

本解析器专注结构：标题层级、段落顺序、图片引用。
表格注：紧贴表格上方、以"表："开头的段落会被识别为表格标题（表注）。
脚注、行内加粗/斜体（转为纯文本）暂未完整支持。
"""

import re
from dataclasses import dataclass


@dataclass
class Heading:
    level: int
    text: str


@dataclass
class Paragraph:
    text: str


@dataclass
class ListItem:
    text: str
    ordered: bool = False
    number: int = 1
    level: int = 0


@dataclass
class ImageBlock:
    src: str
    alt: str = ""


@dataclass
class TableBlock:
    header: list
    rows: list
    caption: str = ""


@dataclass
class CodeBlock:
    text: str


def _split_row(line):
    """把管道表格行拆成单元格。"""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [_strip_inline(cell.strip()) for cell in line.split("|")]


def _attach_table_captions(blocks):
    """把紧贴表格上方、以'表：'开头的段落合并为表格标题（表注）。"""
    result = []
    i = 0
    while i < len(blocks):
        block = blocks[i]
        if (
            isinstance(block, Paragraph)
            and i + 1 < len(blocks)
            and isinstance(blocks[i + 1], TableBlock)
            and re.match(r"^表\s*[:：]", block.text.strip())
        ):
            caption = re.sub(r"^表\s*[:：]\s*", "", block.text.strip())
            blocks[i + 1].caption = caption
            i += 1
            continue
        result.append(block)
        i += 1
    return result


def _strip_inline(text):
    """行内 Markdown 语法转纯文本：图片/链接取文字，粗斜体去标记，代码去反引号。"""
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*\n]+)\*", r"\1", text)
    return text


def parse_front_matter(text):
    """提取 YAML front matter 中的键值（目前只用 title）。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        line = lines[i].strip()
        if line and not line.startswith("#") and ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip("\"'")
        i += 1
    return meta


def parse_md(text):
    """解析 md 文本，返回按顺序排列的块列表。"""
    lines = text.splitlines()
    blocks = []
    i = 0

    # 跳过 YAML front matter
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        i += 1

    para = []

    def flush_para():
        nonlocal para
        if para:
            joined = re.sub(r"\s+", " ", " ".join(p.strip() for p in para)).strip()
            if joined:
                blocks.append(Paragraph(_strip_inline(joined)))
            para = []

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        # 围栏代码块
        m = re.match(r"^(```|~~~)", stripped)
        if m:
            flush_para()
            fence = m.group(1)
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith(fence):
                code.append(lines[i])
                i += 1
            i += 1  # 跳过结束围栏
            blocks.append(CodeBlock("\n".join(code)))
            continue

        # ATX 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para()
            blocks.append(Heading(len(m.group(1)), _strip_inline(m.group(2).strip())))
            i += 1
            continue

        # 空行：结束段落
        if not stripped:
            flush_para()
            i += 1
            continue

        # 独立成行的图片
        m = re.match(r"^!\[(.*?)\]\((.+?)\)\s*$", stripped)
        if m:
            flush_para()
            blocks.append(ImageBlock(m.group(2).strip(), m.group(1).strip()))
            i += 1
            continue

        # 引用
        if stripped.startswith(">"):
            flush_para()
            quoted = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quoted.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            text = re.sub(r"\s+", " ", " ".join(l.strip() for l in quoted)).strip()
            if text:
                blocks.append(Paragraph(_strip_inline(text)))
            continue

        # 列表项（保留缩进以支持嵌套层级）
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", raw)
        if m:
            flush_para()
            indent_str, marker, item_text = m.group(1), m.group(2), m.group(3)
            ordered = bool(re.fullmatch(r"\d+[.)]", marker))
            number = int(re.search(r"\d+", marker).group()) if ordered else 1
            level = min(len(indent_str) // 2, 8)
            blocks.append(
                ListItem(_strip_inline(item_text.strip()), ordered, number, level)
            )
            i += 1
            continue

        # 水平线
        if re.fullmatch(r"([-*_])\1{2,}\s*", stripped):
            flush_para()
            i += 1
            continue

        # GFM 管道表格
        if "|" in stripped:
            start = i
            rows = []
            while i < len(lines) and "|" in lines[i]:
                rows.append(lines[i].strip())
                i += 1
            is_table = (
                len(rows) >= 2
                and "-" in rows[1]
                and re.fullmatch(r"\|?[\s:|-]+\|?", rows[1])
            )
            if is_table:
                flush_para()
                body = [_split_row(r) for r in rows[2:]]
                body = [r for r in body if any(c.strip() for c in r)]
                blocks.append(TableBlock(_split_row(rows[0]), body))
                continue
            i = start  # 不是表格，回退按段落处理

        # 普通段落行
        para.append(raw)
        i += 1

    flush_para()
    return _attach_table_captions(blocks)


def parse_md_file(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return parse_md(f.read())
