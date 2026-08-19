import numpy as np
import pandas as pd
from typing import Tuple


def df_to_arrayf(df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    # 提取指定列并转为 float64 数组
    return df[cols].to_numpy(dtype=np.float64)


def standardize(x: np.ndarray, mean: np.ndarray | None = None,
                sigma: np.ndarray | None = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # 标准化 返回 (标准化值, 均值, 标准差)
    x = np.asarray(x, dtype=np.float64)
    if mean is None: mean = np.mean(x, axis=0)
    if sigma is None: sigma = np.std(x, axis=0)
    safe_sigma = np.where(sigma < 1e-12, 1.0, sigma)            # 除零保护
    return (x - mean) / safe_sigma, mean, sigma


def split_train_test(X: np.ndarray, Y: np.ndarray, test_frac: float = 0.2,
                     seed: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    # 按固定随机种子划分训练/测试集
    rng = np.random.default_rng(seed)
    idx = rng.permutation(X.shape[0])
    n_test = int(round(X.shape[0] * test_frac))
    test_idx, train_idx = idx[:n_test], idx[n_test:]
    return X[train_idx], Y[train_idx], X[test_idx], Y[test_idx]
