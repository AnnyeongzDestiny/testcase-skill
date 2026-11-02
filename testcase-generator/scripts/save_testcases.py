"""将 Markdown 测试用例目录导出为 Excel。"""

from __future__ import annotations

import argparse
import os
import sys

# 将 scripts 目录加入 path，以便直接运行本文件时导入同目录模块。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from excel_generator import build_excel


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Markdown test cases to an Excel workbook")
    parser.add_argument("src_dir", help="Directory containing test case .md files")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory (default: current working directory)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Output filename without .xlsx (default: derived from src_dir)",
    )
    parser.add_argument("--template", default=None, help="Path to an Excel template file")
    parser.add_argument(
        "--all-tables",
        action="store_true",
        help="Export every test-case table per file as a separate sheet",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.src_dir):
        parser.error(f"directory not found: {args.src_dir}")

    if args.template and not os.path.isfile(args.template):
        parser.error(f"template not found: {args.template}")

    filename = args.name or (os.path.basename(os.path.normpath(args.src_dir)) + "_TestCases")
    if filename in {"", ".", ".."} or os.path.basename(filename) != filename:
        parser.error("--name must be a filename without directory components")
    os.makedirs(args.output_dir, exist_ok=True)
    excel_path = os.path.join(args.output_dir, f"{filename}.xlsx")

    print(f"Source: {args.src_dir}")
    print(f"Excel:  {excel_path}")
    print(f"Mode: {'all tables' if args.all_tables else 'first table per file'}")
    print()

    result = build_excel(args.src_dir, excel_path, args.template, args.all_tables)
    if not result["sheets"]:
        parser.error("no test-case tables found after excluding outline files")
    print(f"Done: {excel_path}")
    print(f"Sheets: {result['sheets']}")
    for name, count in result["details"]:
        print(f"  - {name} ({count} cases)")
    print(f"Total: {result['total_cases']} cases")


if __name__ == "__main__":
    main()
