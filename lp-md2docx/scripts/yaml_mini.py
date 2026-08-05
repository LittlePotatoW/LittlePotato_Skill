# -*- coding: utf-8 -*-
"""极简 YAML 子集解析器。

只覆盖本技能样式表配置所需的语法：
- 空格缩进嵌套的映射（map）
- 行内流映射 {a: 1, b: 2} 和流列表 [a, b]
- 标量：字符串、整数、浮点数、布尔、null、带引号字符串
- 注释（# 开头或行尾，引号内不解析）

不支持的语法会直接报错，便于尽早发现配置问题。
"""

import re


def _strip_comment(line):
    """去掉行尾注释，忽略引号内的 #。"""
    quote = None
    for i, ch in enumerate(line):
        if ch in ("'", '"'):
            if quote == ch:
                quote = None
            elif quote is None:
                quote = ch
        elif ch == "#" and quote is None:
            return line[:i]
    return line


def _scalar(text):
    text = text.strip()
    if text == "" or text.lower() in ("null", "none", "~"):
        return None
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    return text


def _split_top_level(text, sep=","):
    """按分隔符切分，忽略引号和嵌套括号内的分隔符。"""
    parts, depth, quote, cur = [], 0, None, ""
    for ch in text:
        if ch in ("'", '"'):
            if quote == ch:
                quote = None
            elif quote is None:
                quote = ch
        elif quote is None:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == sep and depth == 0:
                parts.append(cur)
                cur = ""
                continue
        cur += ch
    parts.append(cur)
    return parts


def _parse_flow_map(text):
    inner = text.strip()[1:-1].strip()
    result = {}
    if not inner:
        return result
    for part in _split_top_level(inner):
        if ":" not in part:
            raise ValueError(f"无效的 flow map 项: {part!r}")
        key, _, value = part.partition(":")
        result[key.strip().strip("\"'")] = _scalar(value)
    return result


def _parse_flow_list(text):
    inner = text.strip()[1:-1].strip()
    if not inner:
        return []
    return [_scalar(p) for p in _split_top_level(inner)]


def _parse_block(lines, idx, indent):
    result = {}
    while idx < len(lines):
        raw = lines[idx]
        if not raw.strip() or raw.strip().startswith("#"):
            idx += 1
            continue
        if raw.startswith("\t"):
            raise ValueError(f"第 {idx + 1} 行使用了 Tab 缩进，请改用空格")
        cur_indent = len(raw) - len(raw.lstrip(" "))
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise ValueError(f"第 {idx + 1} 行缩进错误: {raw!r}")
        content = _strip_comment(raw.strip())
        m = re.match(r"^([^:]+):(.*)$", content)
        if not m:
            raise ValueError(f"第 {idx + 1} 行不是合法的键值对: {content!r}")
        key = m.group(1).strip().strip("\"'")
        rest = m.group(2).strip()
        idx += 1
        if rest == "":
            peek = idx
            while peek < len(lines) and (
                not lines[peek].strip() or lines[peek].strip().startswith("#")
            ):
                peek += 1
            if peek < len(lines):
                nxt_indent = len(lines[peek]) - len(lines[peek].lstrip(" "))
                if nxt_indent > indent:
                    value, idx = _parse_block(lines, peek, nxt_indent)
                    result[key] = value
                    continue
            result[key] = None
        elif rest.startswith("{") and rest.endswith("}"):
            result[key] = _parse_flow_map(rest)
        elif rest.startswith("[") and rest.endswith("]"):
            result[key] = _parse_flow_list(rest)
        else:
            result[key] = _scalar(rest)
    return result, idx


def loads(text):
    """解析 YAML 文本，返回 dict。"""
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    result, _ = _parse_block(lines, 0, 0)
    return result


def load_yaml_file(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return loads(f.read())
