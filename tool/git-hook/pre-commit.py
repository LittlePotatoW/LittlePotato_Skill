#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LittlePotato 仓库 pre-commit 钩子逻辑（规则可在 pre-commit-config.json 调整）。

检查项：
1. 一次提交中图片数量超过 max_images 张；
2. 任一文件大小超过 max_file_size_mb MB；
3. 文件后缀 / 文件名命中排除表（blocked_extensions / blocked_filenames）；
4. 检测为二进制内容（图片除外，图片走第 1 条规则）；
5. .ipynb 未清空输出（outputs 非空或 execution_count 未清空）。

绕过方式（不推荐）：环境变量 LP_GIT_HOOK_SKIP=1，或 git commit --no-verify。
"""

import json
import os
import subprocess
import sys

CONFIG_NAME = "pre-commit-config.json"

DEFAULT_CONFIG = {
    "max_images": 1,
    "max_file_size_mb": 1.0,
    "image_extensions": [
        "png", "jpg", "jpeg", "gif", "bmp", "webp", "svg", "tif", "tiff",
        "ico", "avif", "heic", "heif", "psd", "raw", "cr2", "nef", "arw",
    ],
    "blocked_extensions": [
        "exe", "msi", "dll", "so", "dylib", "bin", "o", "obj", "lib", "a",
        "class", "jar", "war", "pyc", "pyo", "pyd", "whl", "egg",
        "zip", "tar", "gz", "tgz", "bz2", "xz", "7z", "rar", "iso", "dmg",
        "pdb", "db", "sqlite", "sqlite3", "log", "tmp", "temp", "bak", "old",
        "swp", "swo", "orig", "rej", "dmp", "minidump", "pcap", "cap",
    ],
    "blocked_filenames": [
        "Thumbs.db", ".DS_Store", "desktop.ini", ".env",
    ],
    "check_binary": True,
    "check_notebook_outputs": True,
}


def run_git(args, cwd=None):
    return subprocess.run(["git", *args], check=True, capture_output=True, cwd=cwd).stdout


def repo_root():
    env_root = os.environ.get("LP_HOOK_REPO_ROOT")
    if env_root:
        return env_root
    return run_git(["rev-parse", "--show-toplevel"]).decode("utf-8", "surrogateescape").strip()


def load_config():
    config = dict(DEFAULT_CONFIG)
    path = os.path.join(repo_root(), "tool", "git-hook", CONFIG_NAME)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                user = json.load(fh)
            for key, value in user.items():
                config[key] = value
        except Exception as exc:
            print(f"pre-commit: 配置文件 {path} 解析失败，使用默认配置（{exc}）", file=sys.stderr)
    return config


def parse_raw(raw_text):
    """解析 git diff --cached --raw -z 输出，返回 [(path, blob_sha)]。

    每条记录格式：":<oldmode> <newmode> <oldsha> <newsha> <status>" + NUL + path + NUL
    重命名/复制（R/C）会额外多一个"旧路径"字段：... + NUL + old_path + NUL + new_path + NUL
    """
    entries = []
    parts = raw_text.split("\0")
    i = 0
    n = len(parts)
    while i < n:
        header = parts[i]
        i += 1
        if not header or not header.startswith(":"):
            continue
        fields = header.split()
        if len(fields) < 5:
            continue
        sha = fields[3]
        if sha and sha.count("0") != len(sha):
            status = fields[4]
            if status.startswith("R") or status.startswith("C"):
                if i + 1 < n:
                    path = parts[i + 1]  # 重命名时第二个字段才是新路径
                    i += 2
                else:
                    continue
            else:
                path = parts[i]
                i += 1
            if path:
                entries.append((path, sha))
        else:
            # 零哈希（删除等），也要跳过对应的路径字段
            status = fields[4] if len(fields) >= 5 else ""
            if status.startswith("R") or status.startswith("C"):
                i += 2
            else:
                i += 1
    return entries


def staged_entries():
    raw = run_git(
        ["diff", "--cached", "--raw", "-z", "--diff-filter=ACMRT"],
        cwd=repo_root(),
    )
    return parse_raw(raw.decode("utf-8", "surrogateescape"))


def blob_size(sha):
    return int(run_git(["cat-file", "-s", sha], cwd=repo_root()).strip())


def blob_prefix(sha, n):
    proc = subprocess.Popen(
        ["git", "-C", repo_root(), "cat-file", "blob", sha],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        return proc.stdout.read(n)
    finally:
        proc.kill()
        proc.wait()


def check_notebook(content, path):
    issues = []
    try:
        nb = json.loads(content.decode("utf-8"))
    except Exception as exc:
        return [f"Jupyter Notebook 无法解析: {exc}"]
    cells = nb.get("cells", []) if isinstance(nb, dict) else []
    for idx, cell in enumerate(cells):
        outputs = cell.get("outputs")
        if outputs not in (None, []):
            issues.append(f"cell {idx + 1} 存在未清空的输出（{len(outputs)} 个）")
        if cell.get("execution_count") is not None:
            issues.append(f"cell {idx + 1} execution_count 未清空")
    if issues:
        issues.append("请在 Jupyter 中执行 Kernel → Restart & Clear All Outputs 后重新保存")
    return issues


def inspect(path, content, content_len, config):
    """返回 (is_image, issues)。content 可能为完整内容或二进制前缀。"""
    issues = []
    basename = os.path.basename(path)
    ext = os.path.splitext(path)[1].lower().lstrip(".")

    if ext in config["blocked_extensions"]:
        issues.append(f"后缀命中排除表: .{ext}")
    if basename in config["blocked_filenames"]:
        issues.append(f"文件名命中排除表: {basename}")

    max_mb = float(config["max_file_size_mb"])
    size_mb = content_len / (1024 * 1024)
    if size_mb > max_mb:
        issues.append(f"大小 {size_mb:.3f} MB 超过限制 {max_mb} MB")

    is_image = ext in config["image_extensions"]
    if (
        not is_image
        and ext not in config["blocked_extensions"]
        and config.get("check_binary", True)
        and content is not None
        and b"\x00" in content[:8192]
    ):
        issues.append("检测为二进制文件")

    if (
        ext == "ipynb"
        and config.get("check_notebook_outputs", True)
        and content is not None
    ):
        issues.extend(check_notebook(content, path))

    return is_image, issues


def main():
    if os.environ.get("LP_GIT_HOOK_SKIP"):
        print("pre-commit: LP_GIT_HOOK_SKIP=1，跳过检查", file=sys.stderr)
        return 0

    config = load_config()
    entries = staged_entries()
    if not entries:
        return 0

    image_exts = config["image_extensions"]
    image_files = [
        path for path, _ in entries
        if os.path.splitext(path)[1].lower().lstrip(".") in image_exts
    ]

    problems = []
    for path, sha in entries:
        ext = os.path.splitext(path)[1].lower().lstrip(".")
        content = None
        content_len = blob_size(sha)
        need_binary = (
            config.get("check_binary", True)
            and ext not in image_exts
            and ext not in config["blocked_extensions"]
        )
        if ext == "ipynb" and config.get("check_notebook_outputs", True):
            content = run_git(["cat-file", "blob", sha], cwd=repo_root())
        elif need_binary:
            content = blob_prefix(sha, 8192)

        _, issues = inspect(path, content, content_len, config)
        if issues:
            problems.append((path, issues))

    max_images = int(config["max_images"])
    if len(image_files) > max_images:
        problems.append((None, [
            f"本次提交包含 {len(image_files)} 张图片，超过允许的 {max_images} 张: "
            + ", ".join(image_files)
        ]))

    if not problems:
        return 0

    print("pre-commit 检查未通过：", file=sys.stderr)
    for path, issues in problems:
        print(f"  - {path or '<全局>'}", file=sys.stderr)
        for issue in issues:
            print(f"      * {issue}", file=sys.stderr)
    print("", file=sys.stderr)
    print("如确需提交，请调整文件后重试；或使用 git commit --no-verify 跳过本次检查。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
