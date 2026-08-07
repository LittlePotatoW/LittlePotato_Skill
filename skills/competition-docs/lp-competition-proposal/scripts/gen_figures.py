#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计划书示意图生成模板。

用法：
    python gen_figures.py

说明：
    - 每个块需要架构图/流程图/数据图时，在本文件加一个函数（如 fig_overview()）
    - 函数输出 PNG 到 ../images/，命名按 image-checklist.md（如 fig-09-01-product-overview.png）
    - 生成后记得登记 images/image-map.md
    - 中文使用系统字体（Windows 微软雅黑 / 黑体），macOS/Linux 请改 FONT 路径
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

IMAGES_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "images"))
FONT = r"C:\Windows\Fonts\msyh.ttc"  # Windows 微软雅黑；无则换 simhei.ttf 或系统字体


def setup_font():
    from matplotlib import font_manager
    if os.path.exists(FONT):
        font_manager.fontManager.addfont(FONT)
        prop = font_manager.FontProperties(fname=FONT)
        plt.rcParams["font.family"] = prop.get_name()
    plt.rcParams["axes.unicode_minus"] = False


def draw_box(ax, x, y, w, h, title, lines, fc, ec, title_fs=14, body_fs=10):
    """画一个带标题与若干行文本的圆角框。参数顺序：坐标、宽高、标题、行列表、填充色、边框色。"""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.02",
                         linewidth=1.8, edgecolor=ec, facecolor=fc, zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.05, title, ha="center", va="top",
            fontsize=title_fs, fontweight="bold", color=ec, zorder=3)
    for i, line in enumerate(lines):
        ax.text(x + 0.03, y + h - 0.15 - i * 0.13, line, ha="left", va="top",
                fontsize=body_fs, color="#222", zorder=3)


def fig_example():
    """示例：模块分层图。复制本函数改内容即可。"""
    fig, ax = plt.subplots(figsize=(14, 8), dpi=110)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    ax.text(7, 7.6, "示例示意图标题", ha="center", va="top",
            fontsize=20, fontweight="bold", color="#0b3d6e")
    draw_box(ax, 1, 4.8, 5.5, 2.0, "模块 A", ["功能 1", "功能 2"], "#eaf3fb", "#1f6fb2")
    draw_box(ax, 7.5, 4.8, 5.5, 2.0, "模块 B", ["功能 3", "功能 4"], "#eef8ee", "#2e8b57")
    ax.annotate("", xy=(7.4, 5.8), xytext=(6.6, 5.8),
                arrowprops=dict(arrowstyle="->", color="#555", lw=2))
    fig.tight_layout()
    os.makedirs(IMAGES_DIR, exist_ok=True)
    out = os.path.join(IMAGES_DIR, "fig-example.png")
    fig.savefig(out, dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved:", out)


if __name__ == "__main__":
    setup_font()
    fig_example()
