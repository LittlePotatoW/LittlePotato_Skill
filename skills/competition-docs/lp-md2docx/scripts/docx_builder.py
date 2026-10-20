# -*- coding: utf-8 -*-
"""根据样式表配置生成 .docx。

核心步骤（第一步）：
1. 在文档中生成样式表：正文样式 + 标题样式（中文字体、outline 层级、间距）
2. 生成多级列表编号（最多四级，Word 原生编号，不写死在标题文本里）
3. 按顺序把 md 块写入文档：标题套 Heading 样式，正文套 Normal 样式
"""

import os
import ntpath
import re

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.image.image import Image as DocxImage
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Mm, Pt, RGBColor

from md_parser import CodeBlock, Heading, ImageBlock, ListItem, Paragraph, TableBlock


HEADING_STYLE_NAMES = {
    1: "一级标题",
    2: "二级标题",
    3: "三级标题",
    4: "四级标题",
    5: "五级标题",
    6: "六级标题",
}


# 中文字号 → 磅值
CN_SIZE = {
    "初号": 42, "小初": 36, "一号": 26, "小一": 24, "二号": 22, "小二": 18,
    "三号": 16, "小三": 15, "四号": 14, "小四": 12, "五号": 10.5, "小五": 9,
    "六号": 7.5, "小六": 6.5, "七号": 5.5, "八号": 5,
}

_ALIGN = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _pt(value, default=None):
    """把 '16pt' / '三号' / 16 解析成 Pt 对象。"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return Pt(float(value))
    s = str(value).strip().lower()
    if s in CN_SIZE:
        return Pt(CN_SIZE[s])
    m = re.fullmatch(r"([\d.]+)\s*pt", s)
    if m:
        return Pt(float(m.group(1)))
    raise ValueError(f"无法解析字号: {value!r}")


def _length(value, default=None):
    """把 '25mm' / '14.5cm' / 数值(默认 mm) 解析成 Length 对象。"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return Mm(float(value))
    s = str(value).strip().lower()
    for unit, cls in (("mm", Mm), ("cm", Cm), ("pt", Pt)):
        m = re.fullmatch(r"([\d.]+)\s*" + unit, s)
        if m:
            return cls(float(m.group(1)))
    m = re.fullmatch(r"([\d.]+)\s*in", s)
    if m:
        return Pt(float(m.group(1)) * 72)
    raise ValueError(f"无法解析长度: {value!r}")


def _set_style_font(style, east_asia, latin, size_pt=None, bold=None, color=None):
    style.font.name = latin
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)
    rfonts.set(qn("w:eastAsia"), east_asia)
    if size_pt is not None:
        style.font.size = size_pt
    if bold is not None:
        style.font.bold = bold
    if color is not None:
        style.font.color.rgb = RGBColor.from_string(color)


def _style_pPr(style):
    return style.element.get_or_add_pPr()


def _insert_pPr_child(pPr, elm, successors):
    """按 OOXML 规定的子元素顺序插入 pPr 子元素。"""
    pPr.insert_element_before(elm, *successors)


def _replace_pPr_child(pPr, tag, make):
    """删除同标签旧元素后按顺序插入新元素（避免重复）。"""
    for old in pPr.findall(qn(tag)):
        pPr.remove(old)
    _insert_pPr_child(pPr, make(), _NUMPR_SUCCESSORS if tag == "w:numPr" else _OUTLINE_SUCCESSORS)


def _mark_style_visible(style, priority=99):
    """给样式加上 uiPriority / qFormat，确保在 Word 样式面板里可见。"""
    el = style.element
    for tag in ("w:uiPriority", "w:qFormat"):
        for old in el.findall(qn(tag)):
            el.remove(old)
    successors = [
        "w:autoRedefine", "w:hidden", "w:semiHidden", "w:unhideWhenUsed",
        "w:locked", "w:personal", "w:personalCompose", "w:personalReply",
        "w:rsid", "w:pPr", "w:rPr", "w:tblPr", "w:trPr", "w:tcPr", "w:tblStylePr",
    ]
    up = OxmlElement("w:uiPriority")
    up.set(qn("w:val"), str(priority))
    qf = OxmlElement("w:qFormat")
    el.insert_element_before(up, *successors)
    el.insert_element_before(qf, *successors)


_NUMPR_SUCCESSORS = [
    "w:suppressLineNumbers", "w:pBdr", "w:shd", "w:tabs", "w:suppressAutoHyphens",
    "w:kinsoku", "w:wordWrap", "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE",
    "w:autoSpaceDN", "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing",
    "w:ind", "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
]

_IND_SUCCESSORS = [
    "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
]

_OUTLINE_SUCCESSORS = [
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
]


def _setup_page(document, page_cfg):
    sec = document.sections[0]
    size = page_cfg.get("size", "A4")
    if str(size).upper() == "A4":
        sec.page_width = Mm(210)
        sec.page_height = Mm(297)
    margins = page_cfg.get("margins", {})
    sec.top_margin = _length(margins.get("top", "25mm"))
    sec.bottom_margin = _length(margins.get("bottom", "25mm"))
    sec.left_margin = _length(margins.get("left", "30mm"))
    sec.right_margin = _length(margins.get("right", "25mm"))


def _get_style(document, name):
    try:
        return document.styles[name]
    except KeyError:
        return document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)


def _build_numbering(root, heading_cfg, east_base, latin, abstract_id, num_id):
    """生成四级多级列表（abstractNum + num）。"""
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    for ilvl in range(9):
        level = ilvl + 1
        lvl_cfg = heading_cfg.get(str(level), {})
        if ilvl < 4:
            lvl_text = lvl_cfg.get("num_format") or (
                "%1" if level == 1 else ".".join(f"%{i}" for i in range(1, level + 1))
            )
            num_fmt = lvl_cfg.get("num_fmt", "decimal")
        else:
            lvl_text = ".".join(f"%{i}" for i in range(1, level + 1))
            num_fmt = "decimal"
        east = lvl_cfg.get("font", east_base) or east_base

        lvl = OxmlElement("w:lvl")
        lvl.set(qn("w:ilvl"), str(ilvl))
        start = OxmlElement("w:start")
        start.set(qn("w:val"), "1")
        fmt = OxmlElement("w:numFmt")
        fmt.set(qn("w:val"), num_fmt)
        suff = OxmlElement("w:suff")
        suff.set(qn("w:val"), "space")
        txt = OxmlElement("w:lvlText")
        txt.set(qn("w:val"), lvl_text)
        jc = OxmlElement("w:lvlJc")
        jc.set(qn("w:val"), "left")

        ppr = OxmlElement("w:pPr")
        ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), "0")
        ind.set(qn("w:hanging"), "0")
        ppr.append(ind)

        rpr = OxmlElement("w:rPr")
        rfonts = OxmlElement("w:rFonts")
        rfonts.set(qn("w:ascii"), latin)
        rfonts.set(qn("w:hAnsi"), latin)
        rfonts.set(qn("w:eastAsia"), east)
        rpr.append(rfonts)

        for el in (start, fmt, suff, txt, jc):
            lvl.append(el)
        lvl.append(ppr)
        lvl.append(rpr)
        abstract.append(lvl)

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    ref = OxmlElement("w:abstractNumId")
    ref.set(qn("w:val"), str(abstract_id))
    num.append(ref)

    root.append(abstract)
    root.append(num)


def _build_list_numbering(root, kind, abstract_id, num_id):
    """生成原生列表编号：bullet（无序）或 decimal（有序）。"""
    bullets = ["•", "○", "■"]
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    for ilvl in range(9):
        lvl = OxmlElement("w:lvl")
        lvl.set(qn("w:ilvl"), str(ilvl))
        start = OxmlElement("w:start")
        start.set(qn("w:val"), "1")
        fmt = OxmlElement("w:numFmt")
        fmt.set(qn("w:val"), "bullet" if kind == "bullet" else "decimal")
        suff = OxmlElement("w:suff")
        suff.set(qn("w:val"), "space")
        txt = OxmlElement("w:lvlText")
        txt.set(
            qn("w:val"),
            bullets[min(ilvl, len(bullets) - 1)] if kind == "bullet" else "%1.",
        )
        jc = OxmlElement("w:lvlJc")
        jc.set(qn("w:val"), "left")
        ppr = OxmlElement("w:pPr")
        ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), str((ilvl + 1) * 360))
        ind.set(qn("w:hanging"), "360")
        ppr.append(ind)
        rpr = OxmlElement("w:rPr")
        rfonts = OxmlElement("w:rFonts")
        rfonts.set(qn("w:eastAsia"), "宋体")
        rpr.append(rfonts)
        for el in (start, fmt, suff, txt, jc):
            lvl.append(el)
        lvl.append(ppr)
        lvl.append(rpr)
        abstract.append(lvl)

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    ref = OxmlElement("w:abstractNumId")
    ref.set(qn("w:val"), str(abstract_id))
    num.append(ref)
    root.append(abstract)
    root.append(num)


def _build_caption_numbering(root, prefix, abstract_id, num_id):
    """生成图/表题注编号：图%1、表%1（Word 原生编号，自动递增）。"""
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    for ilvl in range(9):
        lvl = OxmlElement("w:lvl")
        lvl.set(qn("w:ilvl"), str(ilvl))
        start = OxmlElement("w:start")
        start.set(qn("w:val"), "1")
        fmt = OxmlElement("w:numFmt")
        fmt.set(qn("w:val"), "decimal")
        suff = OxmlElement("w:suff")
        suff.set(qn("w:val"), "space")
        txt = OxmlElement("w:lvlText")
        txt.set(
            qn("w:val"),
            f"{prefix}%1" if ilvl == 0 else ".".join(f"%{i}" for i in range(1, ilvl + 2)),
        )
        jc = OxmlElement("w:lvlJc")
        jc.set(qn("w:val"), "center")
        ppr = OxmlElement("w:pPr")
        ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), str(440 + ilvl * 440))
        ind.set(qn("w:hanging"), "440")
        ppr.append(ind)
        rpr = OxmlElement("w:rPr")
        for el in (start, fmt, suff, txt, jc):
            lvl.append(el)
        lvl.append(ppr)
        lvl.append(rpr)
        abstract.append(lvl)

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    ref = OxmlElement("w:abstractNumId")
    ref.set(qn("w:val"), str(abstract_id))
    num.append(ref)
    root.append(abstract)
    root.append(num)


def _get_numbering_root(document):
    """拿到 numbering.xml 根元素（默认模板自带，缺省时手动建一个）。"""
    try:
        numbering_part = document.part.numbering_part
    except Exception:
        from docx.opc.packuri import PackURI
        from docx.oxml import parse_xml
        from docx.oxml.ns import nsdecls
        from docx.parts.numbering import NumberingPart

        root = parse_xml("<w:numbering %s/>" % nsdecls("w"))
        numbering_part = NumberingPart(
            PackURI("/word/numbering.xml"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml",
            root,
            document.part.package,
        )
        document.part.relate_to(numbering_part, RT.NUMBERING)
    return numbering_part.element


def _next_ids(root):
    """分配不冲突的 abstractNumId / numId。"""
    abstract_ids = [
        int(a.get(qn("w:abstractNumId"))) for a in root.findall(qn("w:abstractNum"))
    ]
    num_ids = [int(n.get(qn("w:numId"))) for n in root.findall(qn("w:num"))]
    abstract_id = (max(abstract_ids) + 1) if abstract_ids else 0
    num_id = (max(num_ids) + 1) if num_ids else 1
    return abstract_id, num_id


def _apply_paragraph_numpr(paragraph, num_id, ilvl):
    """给段落挂上原生列表编号。"""
    pPr = paragraph._p.get_or_add_pPr()

    def make():
        numpr = OxmlElement("w:numPr")
        i = OxmlElement("w:ilvl")
        i.set(qn("w:val"), str(ilvl))
        n = OxmlElement("w:numId")
        n.set(qn("w:val"), str(num_id))
        numpr.append(i)
        numpr.append(n)
        return numpr

    _replace_pPr_child(pPr, "w:numPr", make)


def _build_table_style(document, cfg):
    """注入表格样式：grid=全框线 0.5pt（默认），three_line=三线表。"""
    tbl_cfg = cfg.get("table", {})
    style_name = tbl_cfg.get("style_name", "标准表格")
    kind = tbl_cfg.get("style_kind", "grid")
    header_bold = bool(tbl_cfg.get("header_bold", False))
    style = document.styles.add_style(style_name, WD_STYLE_TYPE.TABLE)
    try:
        style.base_style = document.styles["Normal Table"]
    except KeyError:
        pass
    _mark_style_visible(style, 59)

    font_cfg = tbl_cfg.get("font", {})
    east = font_cfg.get("east_asia", "宋体")
    latin = font_cfg.get("latin", "Times New Roman")
    size = _pt(font_cfg.get("size", "五号"), Pt(10.5))

    rpr = OxmlElement("w:rPr")
    rf = OxmlElement("w:rFonts")
    rf.set(qn("w:ascii"), latin)
    rf.set(qn("w:hAnsi"), latin)
    rf.set(qn("w:eastAsia"), east)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size.pt * 2)))
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), str(int(size.pt * 2)))
    rpr.append(rf)
    rpr.append(sz)
    rpr.append(szCs)

    def border(tag, val, szv, color="auto"):
        el = OxmlElement(tag)
        el.set(qn("w:val"), val)
        el.set(qn("w:sz"), str(szv))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        return el

    tblPr = OxmlElement("w:tblPr")
    borders = OxmlElement("w:tblBorders")
    if kind == "three_line":
        borders.append(border("w:top", "single", 12, "000000"))
        borders.append(border("w:bottom", "single", 12, "000000"))
        borders.append(border("w:left", "none", 0))
        borders.append(border("w:right", "none", 0))
        borders.append(border("w:insideH", "none", 0))
        borders.append(border("w:insideV", "none", 0))
    else:
        for tag in ("w:top", "w:left", "w:bottom", "w:right", "w:insideH", "w:insideV"):
            borders.append(border(tag, "single", 4))
    tblPr.append(borders)
    cellmar = OxmlElement("w:tblCellMar")
    for side, w in (("w:top", "60"), ("w:left", "80"), ("w:bottom", "60"), ("w:right", "80")):
        el = OxmlElement(side)
        el.set(qn("w:w"), w)
        el.set(qn("w:type"), "dxa")
        cellmar.append(el)
    tblPr.append(cellmar)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "center")
    tblPr.append(jc)

    tsp = None
    if kind == "three_line" or header_bold:
        tsp = OxmlElement("w:tblStylePr")
        tsp.set(qn("w:type"), "firstRow")
        tcPr = OxmlElement("w:tcPr")
        if kind == "three_line":
            tcb = OxmlElement("w:tcBorders")
            tcb.append(border("w:bottom", "single", 6, "000000"))
            tcPr.append(tcb)
        tsp.append(tcPr)
        tsp_rpr = OxmlElement("w:rPr")
        if header_bold or kind == "three_line":
            tsp_rpr.append(OxmlElement("w:b"))
        tsp.append(tsp_rpr)

    style.element.append(rpr)
    style.element.append(tblPr)
    if tsp is not None:
        style.element.append(tsp)


def _setup_styles(document, cfg):
    fonts = cfg.get("fonts", {})
    east = fonts.get("east_asia", "宋体")
    latin = fonts.get("latin", "Times New Roman")
    body_cfg = cfg.get("body", {})
    heading_cfg = cfg.get("heading", {})
    east_base = heading_cfg.get("base", east)
    heading_color = str(heading_cfg.get("color", "000000")).lstrip("#")

    # ---- 基础字体（Normal：等线五号，供其他样式继承）----
    normal = document.styles["Normal"]
    _set_style_font(normal, east, latin, Pt(10.5), None)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # ---- 正文样式（论文正文：完全复刻参考文档定义，不设 basedOn/字体）----
    size_pt = _pt(body_cfg.get("size"), Pt(12)).pt
    ls = body_cfg.get("line_spacing", 1.5)
    if isinstance(ls, (int, float)):
        line = str(int(float(ls) * 240))
        line_rule = "auto"
    else:
        line = str(int(_length(ls).twips))
        line_rule = "exact"
    fli = str(body_cfg.get("first_line_indent", "2ch"))
    if fli.endswith("ch"):
        first_line_chars = str(int(float(fli[:-2]) * 100))
        first_line = (
            "200" if first_line_chars == "200" else str(int(float(fli[:-2]) * size_pt * 20))
        )
    else:
        first_line_chars = "0"
        first_line = str(int(_length(fli).pt * 20))
    body_style_xml = (
        f'<w:style {nsdecls("w")} w:type="paragraph" w:customStyle="1" '
        f'w:styleId="lunwenzhengwen">'
        f'<w:name w:val="论文正文"/>'
        f"<w:qFormat/>"
        f"<w:pPr>"
        f'<w:spacing w:line="{line}" w:lineRule="{line_rule}"/>'
        f'<w:ind w:firstLineChars="{first_line_chars}" w:firstLine="{first_line}"/>'
        f"</w:pPr>"
        f"<w:rPr>"
        f'<w:rFonts w:cs="宋体"/>'
        f'<w:kern w:val="2"/>'
        f'<w:sz w:val="{int(size_pt * 2)}"/>'
        f'<w:szCs w:val="{int(size_pt * 2)}"/>'
        f"</w:rPr>"
        f"</w:style>"
    )
    styles_el = document.styles.element
    for st in styles_el.findall(qn("w:style")):
        name_el = st.find(qn("w:name"))
        if name_el is not None and name_el.get(qn("w:val")) == "论文正文":
            styles_el.remove(st)
    styles_el.append(parse_xml(body_style_xml))
    body_style = document.styles["论文正文"]
    _mark_style_visible(body_style, 9)

    # ---- 大标题样式（Title，居中、无编号）----
    title_cfg = cfg.get("title", {})
    title_style = document.styles["Title"]
    _set_style_font(
        title_style,
        title_cfg.get("font", east_base),
        latin,
        _pt(title_cfg.get("size"), Pt(22)),
        bool(title_cfg.get("bold", True)),
        heading_color,
    )
    tpf = title_style.paragraph_format
    tpf.alignment = _ALIGN.get(title_cfg.get("align"), WD_ALIGN_PARAGRAPH.CENTER)
    if title_cfg.get("space_before"):
        tpf.space_before = _pt(title_cfg["space_before"])
    if title_cfg.get("space_after"):
        tpf.space_after = _pt(title_cfg["space_after"])
    tls = title_cfg.get("line_spacing")
    if tls:
        tpf.line_spacing = float(tls) if isinstance(tls, (int, float)) else _length(tls)
    _mark_style_visible(title_style, 10)

    # ---- 标题样式（一级~六级标题，编号标题一律左对齐）----
    for level in range(1, 7):
        lvl_cfg = heading_cfg.get(str(level), {})
        style = _get_style(document, HEADING_STYLE_NAMES[level])
        _set_style_font(
            style,
            lvl_cfg.get("font", east_base) or east_base,
            latin,
            _pt(lvl_cfg.get("size"), Pt(max(12, 16 - level + 1))),
            bool(lvl_cfg.get("bold", True)),
            heading_color,
        )
        pf = style.paragraph_format
        pf.alignment = _ALIGN.get(lvl_cfg.get("align"), WD_ALIGN_PARAGRAPH.LEFT)
        if lvl_cfg.get("space_before"):
            pf.space_before = _pt(lvl_cfg["space_before"])
        if lvl_cfg.get("space_after"):
            pf.space_after = _pt(lvl_cfg["space_after"])
        lls = lvl_cfg.get("line_spacing")
        if lls:
            pf.line_spacing = float(lls) if isinstance(lls, (int, float)) else _length(lls)
        pf.keep_with_next = True
        def make_ol():
            ol = OxmlElement("w:outlineLvl")
            ol.set(qn("w:val"), str(level - 1))
            return ol

        _replace_pPr_child(_style_pPr(style), "w:outlineLvl", make_ol)
        _mark_style_visible(style, 20 + level)

    # ---- 多级列表编号，挂到 Heading 1~4 ----
    numbering_root = _get_numbering_root(document)
    abstract_id, num_id = _next_ids(numbering_root)
    _build_numbering(numbering_root, heading_cfg, east_base, latin, abstract_id, num_id)
    for level in range(1, 5):
        style = document.styles[HEADING_STYLE_NAMES[level]]
        ppr = _style_pPr(style)

        def make_numpr():
            numpr = OxmlElement("w:numPr")
            ilvl = OxmlElement("w:ilvl")
            ilvl.set(qn("w:val"), str(level - 1))
            numid = OxmlElement("w:numId")
            numid.set(qn("w:val"), str(num_id))
            numpr.append(ilvl)
            numpr.append(numid)
            return numpr

        _replace_pPr_child(ppr, "w:numPr", make_numpr)

    # ---- 原生列表编号（无序/有序）----
    bullet_abstract_id, bullet_num_id = _next_ids(numbering_root)
    _build_list_numbering(numbering_root, "bullet", bullet_abstract_id, bullet_num_id)
    decimal_abstract_id, decimal_num_id = _next_ids(numbering_root)
    _build_list_numbering(numbering_root, "decimal", decimal_abstract_id, decimal_num_id)

    # List Paragraph 样式：清掉正文继承的首行缩进
    list_style = document.styles["List Paragraph"]
    lp_ppr = _style_pPr(list_style)
    lp_ind = lp_ppr.find(qn("w:ind"))
    if lp_ind is None:
        lp_ind = OxmlElement("w:ind")
        _insert_pPr_child(lp_ppr, lp_ind, _IND_SUCCESSORS)
    lp_ind.set(qn("w:firstLine"), "0")
    lp_ind.set(qn("w:firstLineChars"), "0")

    # ---- 图注样式（图片底注）----
    img_caption_cfg = cfg.get("image", {}).get("caption", {})
    fig_caption = _get_style(document, "图注")
    _set_style_font(
        fig_caption,
        img_caption_cfg.get("font", east),
        img_caption_cfg.get("latin", latin),
        _pt(img_caption_cfg.get("size"), Pt(9)),
        bool(img_caption_cfg.get("bold", False)),
        "000000",
    )
    fig_caption.paragraph_format.alignment = _ALIGN.get(
        img_caption_cfg.get("align"), WD_ALIGN_PARAGRAPH.CENTER
    )
    fig_caption.paragraph_format.space_before = Pt(3)
    fig_caption.paragraph_format.space_after = Pt(6)
    _mark_style_visible(fig_caption, 40)

    # ---- 表注样式（表格顶注）----
    tbl_caption_cfg = cfg.get("table", {}).get("caption", {})
    tbl_caption = _get_style(document, "表注")
    _set_style_font(
        tbl_caption,
        tbl_caption_cfg.get("font", "黑体"),
        tbl_caption_cfg.get("latin", latin),
        _pt(tbl_caption_cfg.get("size"), Pt(10.5)),
        bool(tbl_caption_cfg.get("bold", True)),
        "000000",
    )
    tbl_caption.paragraph_format.alignment = _ALIGN.get(
        tbl_caption_cfg.get("align"), WD_ALIGN_PARAGRAPH.CENTER
    )
    tbl_caption.paragraph_format.space_before = Pt(6)
    tbl_caption.paragraph_format.space_after = Pt(3)
    tbl_caption.paragraph_format.keep_with_next = True
    _mark_style_visible(tbl_caption, 41)

    # ---- 表内文字样式（表格字体）----
    tbl_font_cfg = cfg.get("table", {}).get("font", {})
    cell_style = _get_style(document, "表内文字")
    _set_style_font(
        cell_style,
        tbl_font_cfg.get("east_asia", east),
        tbl_font_cfg.get("latin", latin),
        _pt(tbl_font_cfg.get("size", "五号"), Pt(10.5)),
        None,
        "000000",
    )
    cell_style.paragraph_format.alignment = _ALIGN.get(
        cfg.get("table", {}).get("cell_align", "center"), WD_ALIGN_PARAGRAPH.CENTER
    )
    cell_style.paragraph_format.space_before = Pt(0)
    cell_style.paragraph_format.space_after = Pt(0)
    cell_style.paragraph_format.line_spacing = 1.0
    _mark_style_visible(cell_style, 42)

    # ---- 图/表题注自动编号（图%1、表%1），挂到图注/表注样式 ----
    fig_prefix = str(img_caption_cfg.get("prefix", "图")).strip()
    tab_prefix = str(tbl_caption_cfg.get("prefix", "表")).strip()
    fig_abs_id, fig_num_id = _next_ids(numbering_root)
    _build_caption_numbering(numbering_root, fig_prefix, fig_abs_id, fig_num_id)
    tab_abs_id, tab_num_id = _next_ids(numbering_root)
    _build_caption_numbering(numbering_root, tab_prefix, tab_abs_id, tab_num_id)

    def make_caption_numpr(num_id):
        def make():
            numpr = OxmlElement("w:numPr")
            ilvl = OxmlElement("w:ilvl")
            ilvl.set(qn("w:val"), "0")
            numid = OxmlElement("w:numId")
            numid.set(qn("w:val"), str(num_id))
            numpr.append(ilvl)
            numpr.append(numid)
            return numpr

        return make

    _replace_pPr_child(_style_pPr(fig_caption), "w:numPr", make_caption_numpr(fig_num_id))
    _replace_pPr_child(_style_pPr(tbl_caption), "w:numPr", make_caption_numpr(tab_num_id))

    # ---- 三线表表格样式 ----
    _build_table_style(document, cfg)

    # ---- 代码块样式 ----
    code_cfg = cfg.get("code", {})
    code = _get_style(document, "Code Block")
    _set_style_font(
        code,
        code_cfg.get("east_asia", east),
        code_cfg.get("font", "Consolas"),
        _pt(code_cfg.get("size"), Pt(10.5)),
        None,
        "000000",
    )
    code.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    code.paragraph_format.space_before = Pt(3)
    code.paragraph_format.space_after = Pt(3)
    _mark_style_visible(code, 43)

    return {
        "bullet": bullet_num_id,
        "decimal": decimal_num_id,
        "figure": fig_num_id,
        "table": tab_num_id,
    }


def _find_image(path, images_dir, md_dir):
    # Markdown may be untrusted. Resolve symlinks before checking containment so
    # a seemingly local image cannot point outside either resource directory.
    if os.path.isabs(path) or ntpath.isabs(path) or ntpath.splitdrive(path)[0]:
        return None

    candidates = []
    roots = []
    for root in (images_dir, md_dir):
        if not root:
            continue
        real_root = os.path.realpath(root)
        roots.append(real_root)
        candidates.append(os.path.join(root, path))
        # Keep the legacy basename lookup for ordinary subfolder references,
        # but never let it turn an escaping ../ path into a different local file.
        path_parts = path.replace("\\", "/").split("/")
        if root == images_dir and ".." not in path_parts:
            candidates.append(os.path.join(root, os.path.basename(path)))

    for candidate in candidates:
        real_candidate = os.path.realpath(candidate)
        if not os.path.isfile(real_candidate):
            continue
        for root in roots:
            try:
                if os.path.commonpath((root, real_candidate)) == root:
                    return real_candidate
            except ValueError:
                # Different Windows drives cannot be contained by one another.
                continue
    return None


def _write_content(document, blocks, cfg, images_dir, md_dir, list_num_ids, title=None):
    if title:
        document.add_paragraph(title, style="Title")

    image_cfg = cfg.get("image", {})
    max_width = _length(image_cfg.get("max_width"), Cm(14.5))
    caption_cfg = image_cfg.get("caption", {})
    caption_enabled = caption_cfg.get("enabled", True)
    tbl_cfg = cfg.get("table", {})
    tbl_caption_cfg = tbl_cfg.get("caption", {})
    tbl_caption_enabled = tbl_caption_cfg.get("enabled", True)
    tbl_style_name = tbl_cfg.get("style_name", "标准表格")
    cell_style = document.styles["表内文字"]

    for block in blocks:
        if isinstance(block, Heading):
            p = document.add_paragraph(style=HEADING_STYLE_NAMES[min(block.level, 6)])
            p.add_run(block.text)
        elif isinstance(block, Paragraph):
            document.add_paragraph(block.text, style="论文正文")
        elif isinstance(block, ListItem):
            num_id = list_num_ids["decimal"] if block.ordered else list_num_ids["bullet"]
            p = document.add_paragraph(style="List Paragraph")
            p.add_run(block.text)
            _apply_paragraph_numpr(p, num_id, block.level)
        elif isinstance(block, ImageBlock):
            img_path = _find_image(block.src, images_dir, md_dir)
            if img_path is None:
                print(f"[警告] 图片不存在: {block.src}")
                continue
            p = document.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            try:
                native_w = DocxImage.from_file(img_path).width
                width = min(native_w, max_width)
                p.add_run().add_picture(img_path, width=width)
            except Exception as exc:
                print(f"[警告] 图片插入失败 {img_path}: {exc}")
                continue
            if caption_enabled:
                document.add_paragraph(block.alt or "", style="图注")
        elif isinstance(block, TableBlock):
            if block.caption and tbl_caption_enabled:
                document.add_paragraph(block.caption, style="表注")
            ncols = max([len(block.header)] + [len(r) for r in block.rows] + [1])
            table = document.add_table(rows=1 + len(block.rows), cols=ncols)
            table.style = tbl_style_name
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = True

            def fill_row(row_idx, values):
                row = table.rows[row_idx]
                for c in range(ncols):
                    text = values[c] if c < len(values) else ""
                    cell = row.cells[c]
                    p = cell.paragraphs[0]
                    p.style = cell_style
                    if text:
                        p.add_run(text)

            fill_row(0, block.header)
            for r_idx, row in enumerate(block.rows, start=1):
                fill_row(r_idx, row)
        elif isinstance(block, CodeBlock):
            for line in block.text.splitlines() or [""]:
                document.add_paragraph(line, style="Code Block")


def build_docx(blocks, cfg, output_path, images_dir=None, md_dir=None, title=None):
    """blocks + 样式表配置 → docx 文件。"""
    document = Document()
    _setup_page(document, cfg.get("page", {}))
    list_num_ids = _setup_styles(document, cfg)
    _write_content(
        document,
        blocks,
        cfg,
        images_dir or "",
        md_dir or "",
        list_num_ids,
        title,
    )
    document.save(output_path)
