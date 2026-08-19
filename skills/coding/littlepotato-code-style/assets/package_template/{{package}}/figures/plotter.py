from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class Plotter:
    # 统一出图：中文显示 所有图保存到 output/figures

    FONT = "Microsoft YaHei"

    @staticmethod
    def setup() -> Path:
        # 初始化中文字体与输出目录
        plt.rcParams["font.sans-serif"] = [Plotter.FONT, "SimHei"]
        plt.rcParams["axes.unicode_minus"] = False
        out = Path("output/figures")
        out.mkdir(parents=True, exist_ok=True)
        return out

    @staticmethod
    def save(fig, out_dir: Path, name: str) -> Path:
        # 保存图片并关闭画布
        path = out_dir / f"{name}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path
