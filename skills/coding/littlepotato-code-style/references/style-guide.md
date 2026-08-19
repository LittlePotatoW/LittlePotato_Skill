# 风格细则（Style Guide）

> 详细规则与示例。核心规范见 SKILL.md，本文件在编写或重构模块前阅读。

## 1. 目录结构

目标结构（以包名 `my_pkg` 为例）：

```
my_pkg/
├── __init__.py          # 统一导出
├── process.py           # Pipeline / OperModel 门面类
├── utility/             # 读写与转换
│   ├── __init__.py
│   ├── loader.py        # ExcelLoader 等
│   └── transform.py     # df_to_arrayf 等普通函数
├── algorithm/           # 算法
│   ├── __init__.py
│   ├── base.py          # BaseMath 通用数学
│   ├── surrogate.py     # 代理模型
│   ├── optimize.py      # 优化
│   ├── robust.py        # 鲁棒设计
│   └── sensitivity.py   # 敏感性
├── figures/
│   ├── __init__.py
│   └── plotter.py       # Plotter 统一出图
└── main.py              # 包根一键入口
```

## 2. __init__.py 导出模式

子模块导出：

```python
from .loader import ExcelLoader as ExcelLoader

__all__ = ["ExcelLoader"]
```

包根汇总：

```python
from .utility import *
from .algorithm import *
from .figures import *
from .process import Pipeline, OperModel

__all__ = ["Pipeline", "OperModel"]
__all__.extend(utility.__all__)
__all__.extend(algorithm.__all__)
__all__.extend(figures.__all__)
```

## 3. 类即命名空间

相关函数放进 class，全部 `@staticmethod`：

```python
class BaseMath:
    @staticmethod
    def r2(y: np.ndarray, yhat: np.ndarray) -> float:
        # 决定系数 R²
        ...
```

模块级只留 import 与常量；纯转换函数（如 `PIL2gray`、`df_to_arrayf`）可作普通函数。

## 4. 门面类（process.py）

```python
class Pipeline:
    @staticmethod
    def load_data() -> pd.DataFrame: ...

    @staticmethod
    def run_all(output_dir: str | Path = "output") -> Dict[str, Any]:
        # 端到端执行：读取 → 建模 → 出图 → 报告
        ...


class OperModel:
    @staticmethod
    def get_new_model(K: int | None = None) -> NormalModel: ...

    @staticmethod
    def save_model(model: NormalModel, path: str | Path) -> None: ...

    @staticmethod
    def load_model(path: str | Path) -> NormalModel: ...

    @staticmethod
    def train(folder: str | Path, model=None, save_path=None) -> NormalModel: ...
```

## 5. 类型标注与常量

```python
from pathlib import Path
from typing import Callable, Set

IMG_SUFFIX: Set = {".png", ".jpg", ".jpeg"}

def load(path: str | Path) -> "NormalModel": ...

def cv_scores(model_fn: Callable[[np.ndarray, np.ndarray], object],
              X: np.ndarray, Y: np.ndarray, k: int = 5) -> dict: ...
```

## 6. 防御式数值处理

```python
safe_sigma = np.where(sigma < 1e-6, 1.0, sigma)      # 除零保护
if rng < 1e-12: return np.zeros_like(y)              # 全等值保护

with np.errstate(divide="ignore", invalid="ignore"):
    mu = block_sum / block_cnt

assert len(masks) == len(images), \
    f"masks 数量 {len(masks)} 与 images 数量 {len(images)} 不一致"
```

## 7. 模型持久化

自定义统计模型：

```python
def save(self, path: str | Path) -> None:
    arrays = {"K": np.asarray(self.K), "sum": self.sum, "sigma": self.sigma}
    np.savez_compressed(path, allow_pickle=False, **arrays)

@classmethod
def load(cls, path: str | Path) -> "NormalModel":
    data = np.load(path)
    model = cls.__new__(cls)
    model.K = int(data["K"])
    ...
```

sklearn 模型：

```python
from joblib import dump, load
dump(model, path)
model = load(path)
```

## 8. 中文注释风格

- 行内注释：`# 归一化`、`# 成本型指标正向化`、`# 延迟导入 避免循环依赖`；
- 方法级一句话说明返回值：`# 返回 (z, mean, sigma)`；
- 注释写"为什么"，不写"是什么"；少用 docstring。

## 9. 常见坑

- **循环依赖**：`process.py` 引用 `algorithm` 时用函数内延迟导入（`from ..algorithm.xxx import Yyy` 放方法体内）。
- **Windows GBK 控制台**：`print` 避免 `²`、`±` 等非 GBK 字符（用 `R2`、`+/-`），或把结果写入 UTF-8 文件。
- **numpy dtype**：数组统一 `float64`/`float32`，避免 int 运算截断。
- **pandas 中文列名**：读入后立即改为 snake_case 英文列名（如 `R_star`）。
- **交叉验证泄漏**：标准化参数只用训练集计算，再作用于测试集。

## 10. 完成检查清单

- 包结构完整，`__init__.py` 导出一致；
- 所有方法有类型标注；
- 关键步骤有中文注释；
- 除零/空值/形状校验齐全；
- 模型可 save/load；
- `main.py` 可一键运行并输出报告与图表。
