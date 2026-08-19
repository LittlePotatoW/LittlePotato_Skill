import numpy as np


class BaseMath:
    # 通用数学工具：回归评估指标、归一化、熵权、交叉验证划分

    @staticmethod
    def r2(y: np.ndarray, yhat: np.ndarray) -> float:
        # 决定系数 R²
        y = np.asarray(y, dtype=np.float64)
        yhat = np.asarray(yhat, dtype=np.float64)
        ss_res = np.sum((y - yhat) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return float(1.0 - ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

    @staticmethod
    def rmse(y: np.ndarray, yhat: np.ndarray) -> float:
        # 均方根误差
        return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(yhat)) ** 2)))

    @staticmethod
    def mae(y: np.ndarray, yhat: np.ndarray) -> float:
        # 平均绝对误差
        return float(np.mean(np.abs(np.asarray(y) - np.asarray(yhat))))

    @staticmethod
    def minmax_normalize(y: np.ndarray, ymin: float | None = None,
                         ymax: float | None = None) -> np.ndarray:
        # 成本型指标 min-max 归一化 结果越小越优 取值 [0,1]
        y = np.asarray(y, dtype=np.float64)
        if ymin is None: ymin = np.min(y)
        if ymax is None: ymax = np.max(y)
        rng = float(ymax) - float(ymin)
        if rng < 1e-12: return np.zeros_like(y)                # 除零保护
        return (y - ymin) / rng

    @staticmethod
    def entropy_weights(G: np.ndarray) -> np.ndarray:
        # 熵权法 G 为成本型 min-max 归一化矩阵（n×m）
        # 成本型指标先正向化 (1-g) 再计算信息熵 权重体现信息离散度
        G = np.asarray(G, dtype=np.float64)
        n, m = G.shape
        P = 1.0 - G
        P = P / np.where(P.sum(axis=0) < 1e-12, 1.0, P.sum(axis=0))
        P = np.where(P < 1e-12, 1e-12, P)                      # 零值平滑
        e = -np.sum(P * np.log(P), axis=0) / np.log(n)
        d = 1.0 - e
        w = d / np.sum(d)
        return w

    @staticmethod
    def fold_indices(n: int, k: int = 5, seed: int = 42) -> list[np.ndarray]:
        # 返回 k 折交叉验证的测试集下标（列表）
        rng = np.random.default_rng(seed)
        idx = rng.permutation(n)
        return list(np.array_split(idx, k))
