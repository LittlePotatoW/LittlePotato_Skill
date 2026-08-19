from pathlib import Path
from typing import Any, Dict

import pandas as pd

from .figures.plotter import Plotter
from .utility.loader import ExcelLoader


class Pipeline:

    @staticmethod
    def load_data() -> pd.DataFrame:
        # 读取演示数据 不存在时生成示例 CSV（实际使用请替换为真实数据源）
        path = Path("data.csv")
        if not path.exists():
            pd.DataFrame({"x1": [1, 2, 3, 4, 5],
                          "x2": [2.0, 1.5, 3.0, 2.5, 4.0],
                          "y": [3.1, 4.8, 7.2, 8.9, 11.0]}).to_csv(path,
                                                                  index=False)
        return ExcelLoader.load_csv("data.csv")

    @staticmethod
    def run_all(output_dir: str | Path = "output") -> Dict[str, Any]:
        # 端到端流程：读取 → 建模 → 出图 → 报告
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        Plotter.setup()
        df = Pipeline.load_data()
        results: Dict[str, Any] = {"df": df, "n_rows": len(df)}
        report = out_dir / "report.md"
        report.write_text(f"# Report\n\n样本量: {len(df)}\n", encoding="utf-8")
        results["report"] = report
        return results


class OperModel:

    @staticmethod
    def save(model: object, path: str | Path) -> None:
        # sklearn 模型持久化 自定义统计模型改用 np.savez_compressed
        from joblib import dump
        dump(model, path)

    @staticmethod
    def load(path: str | Path) -> object:
        from joblib import load
        return load(path)
