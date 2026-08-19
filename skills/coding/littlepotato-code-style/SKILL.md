---
name: littlepotato-code-style
description: 小土豆团队的 Python 代码风格规范与脚手架。Use when writing, refactoring, or scaffolding Python packages, algorithm modules, or math-modeling projects in this team style, especially when the user says "按这个项目的代码风格"、"按参考项目的风格"、"按小土豆代码风格" or points to an existing project as the style reference. Covers the package layout (utility/algorithm/figures + process.py facade), class-as-namespace static methods, __init__.py re-exports with __all__, full type hints (str | Path, np.ndarray | None, list[np.ndarray]), Chinese inline comments, UPPER_SNAKE constants, Pipeline/OperModel facade classes, defensive numeric guards, and model save/load via npz/joblib.
---

# 小土豆代码风格（LittlePotato Code Style）

## Overview

本技能规定小土豆团队的 Python 工程代码风格，用于新建、改写或重构 Python 包、算法模块与数学建模项目。核心理念：**包即产品、类即命名空间、门面类串联流程、中文注释说明意图、防御式数值处理**。参照项目：`RailwayDetection` 与 `thermal_model`。

## 核心规范（必须遵守）

1. **包结构**：`utility/`（读写与转换）、`algorithm/`（算法）、`figures/`（出图）、`process.py`（门面类）、`__init__.py`（统一导出）；包根放 `main.py` 作为一键入口。
2. **类即命名空间**：用 `class` + `@staticmethod` 组织相关函数（如 `BaseMath`、`ExcelLoader`、`ScoreCal`），模块内不散落同域函数；纯转换工具（如 `utility/transform.py`）可用普通函数。
3. **统一导出**：每个 `__init__.py` 写 `from .module import ClassName as ClassName` 并维护 `__all__`；包根 `__init__.py` 汇总子包 `__all__`。
4. **类型标注**：所有函数/方法写完整类型标注，允许 `str | Path`、`np.ndarray | None`、`list[np.ndarray]`；模块常量全大写并标注类型（`IMG_SUFFIX: Set = {...}`）。
5. **中文注释**：关键步骤写中文行内注释说明"做什么/为什么"（如 `# 标准化 返回 (z, mean, sigma)`）；不写大段 docstring。
6. **门面类**：`process.py` 提供 `Pipeline`（静态方法串联流程，`run_all` 一键执行）与 `OperModel`（模型创建/加载/保存/训练）。
7. **防御式数值处理**：除零保护（`np.where(sigma < 1e-6, 1.0, sigma)`）、空值/边界保护、`np.errstate`；形状校验用 `assert` 并抛中文 `ValueError`。
8. **模型持久化**：自定义统计模型用 `np.savez_compressed` + `classmethod load`；sklearn 模型用 `joblib.dump/load`。
9. **数据约定**：数值统一 `float64`；DataFrame 列名 snake_case（如 `alpha`、`n_rows`、`R_star`）；输出目录 `output/`，图存 `output/figures/`。
10. **可运行性**：写完即跑通，关键数字用真实数据验算不写死；Windows 控制台避免非 GBK 字符（用 `R2` 代替 `R²`）。

## 新建包的标准流程

1. 运行脚手架生成骨架：
   `python scripts/scaffold_package.py <package-name> --path <目标目录>`
2. 按顺序实现 `utility/` → `algorithm/` → `figures/` → `process.py` → `main.py`。
3. 每模块完成后运行 `main.py` 验证；结果写入 `output/report.md` 与 `output/figures/`。

## 详细规范

编写新模块前阅读 [references/style-guide.md](references/style-guide.md)，内含目录结构、`__init__` 导出、类命名空间、门面类、持久化模式与常见坑。

## Resources

- `scripts/scaffold_package.py`：一键生成符合本风格的包骨架（复制模板并替换 `{{package}}` 占位符）
- `assets/package_template/`：包骨架静态模板（占位符 `{{package}}`）
- `references/style-guide.md`：风格细则、模式与示例代码
