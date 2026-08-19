from pathlib import Path

import pandas as pd


class ExcelLoader:

    @staticmethod
    def load_csv(path: str | Path) -> pd.DataFrame:
        # 读取 CSV 并返回数据框（首行为表头）
        return pd.read_csv(path)

    @staticmethod
    def load_xlsx(path: str | Path, skiprows: int = 0,
                  columns: list[str] | None = None) -> pd.DataFrame:
        # 读取 Excel 数据 可按列名规范化为 snake_case
        df = pd.read_excel(path, header=None, skiprows=skiprows)
        df = df.dropna(how="all").reset_index(drop=True)
        if columns is not None:
            df.columns = columns
        return df
