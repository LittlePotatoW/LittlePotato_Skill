from {{package}}.process import Pipeline


def main() -> None:
    # 一键运行 输出结果到 output/
    results = Pipeline.run_all()
    print("完成:", results["report"])


if __name__ == "__main__":
    main()
