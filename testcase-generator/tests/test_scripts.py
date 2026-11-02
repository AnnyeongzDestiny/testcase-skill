from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import schema  # noqa: E402
import validate  # noqa: E402
from excel_generator import build_excel  # noqa: E402


FULL_HEADER = list(schema.FULL_COLUMNS)
LIGHT_HEADER = [
    "编号",
    "功能模块",
    "用例标题",
    "优先级",
    "前置条件",
    "测试数据",
    "测试步骤",
    "预期结果",
    "实际结果",
    "测试结果",
]
LIGHT_BR_HEADER = LIGHT_HEADER + ["关联BR", "备注"]


def markdown_table(header: list[str], rows: list[list[str]], prefix: str = "") -> str:
    body = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    body.extend("| " + " | ".join(row) + " |" for row in rows)
    return prefix + "\n".join(body) + "\n"


def full_row(case_id: str = "SHOP-001", br: str = "BR-001", priority: str = "P0") -> list[str]:
    return [
        case_id,
        "商店",
        "购买后更新余额和库存",
        "正向",
        priority,
        "已进入商店；金币余额为100",
        "商品价格=80",
        "1. 点击购买按钮",
        "金币余额显示为20，库存增加1",
        "",
        "未执行",
        br,
        "-" if br != "-" else "本项目未提供 BR 清单",
    ]


def light_row(case_id: str = "SET-001") -> list[str]:
    return [
        case_id,
        "设置",
        "关闭音效后不再播放操作音效",
        "P0",
        "已进入设置页；音效开关为开启",
        "-",
        "1. 关闭音效开关",
        "音效开关显示为关闭",
        "",
        "未执行",
    ]


class SchemaTests(unittest.TestCase):
    def test_detects_all_supported_schemas_and_aliases(self):
        self.assertEqual(schema.detect_schema(FULL_HEADER), "full")
        self.assertEqual(schema.detect_schema(LIGHT_HEADER), "light")
        self.assertEqual(schema.detect_schema(LIGHT_BR_HEADER), "light-br")
        index, _, _ = schema.build_column_index(LIGHT_HEADER)
        self.assertEqual(index["用例编号"], 0)
        self.assertEqual(index["结果"], 9)

    def test_explicit_mode_rejects_different_exact_schema(self):
        resolution = schema.resolve_schema(FULL_HEADER, "light")
        self.assertIsNone(resolution.schema_name)
        self.assertIn("用例类型", resolution.extra)

    def test_parser_records_real_source_lines(self):
        lines = [
            "# 标题\n",
            "\n",
            "说明\n",
            "\n",
            "| 编号 | 用例标题 |\n",
            "|---|---|\n",
            "| A-001 | 标题 |\n",
        ]
        table = schema.extract_md_tables(lines)[0]
        self.assertEqual(table.header_line, 5)
        self.assertEqual(table.rows[0].source_line, 7)

    def test_parser_keeps_empty_tables(self):
        table = schema.extract_md_tables(
            ["| 编号 | 用例标题 |\n", "|---|---|\n"]
        )[0]
        self.assertEqual(table.header_line, 1)
        self.assertEqual(table.rows, [])


class ValidatorTests(unittest.TestCase):
    def run_validator(self, src: Path, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = validate.main([str(src), *args])
            except SystemExit as exc:
                code = int(exc.code)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_full_light_and_light_br_modes(self):
        cases = [
            (FULL_HEADER, full_row(), "full"),
            (LIGHT_HEADER, light_row(), "light"),
            (LIGHT_BR_HEADER, light_row() + ["BR-001", "-"], "light-br"),
        ]
        for header, row, mode in cases:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                src = Path(temp)
                (src / "01.模块.md").write_text(
                    markdown_table(header, [row]), encoding="utf-8"
                )
                self.assertEqual(self.run_validator(src, "--schema", "auto")[0], 0)
                self.assertEqual(self.run_validator(src, "--schema", mode)[0], 0)

    def test_explicit_schema_rejects_other_exact_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp)
            (src / "01.模块.md").write_text(
                markdown_table(FULL_HEADER, [full_row()]), encoding="utf-8"
            )
            code, output, _ = self.run_validator(src, "--schema", "light")
            self.assertEqual(code, 1)
            self.assertIn("表头不符合 schema light", output)

    def test_auto_and_legacy_accept_historical_dynamic_table(self):
        header = ["用例编号", "用例标题", "优先级", "前置条件", "操作步骤", "预期结果"]
        row = ["OLD-001", "旧格式用例", "P0", "已进入页面", "1. 点击按钮", "页面显示提示文案"]
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp)
            (src / "01.旧格式.md").write_text(markdown_table(header, [row]), encoding="utf-8")
            self.assertEqual(self.run_validator(src, "--schema", "auto")[0], 0)
            self.assertEqual(self.run_validator(src, "--schema", "legacy")[0], 0)
            self.assertEqual(self.run_validator(src, "--schema", "full")[0], 1)

    def test_reports_empty_table(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp)
            (src / "01.空表.md").write_text(
                markdown_table(FULL_HEADER, []), encoding="utf-8"
            )
            code, output, _ = self.run_validator(src, "--schema", "full")
            self.assertEqual(code, 1)
            self.assertIn("表格无数据行", output)

    def test_reports_real_line_and_duplicate_id(self):
        prefix = "# 模块\n\n说明文字\n\n"
        row = full_row()
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp)
            content = markdown_table(FULL_HEADER, [row, row], prefix=prefix)
            (src / "01.模块.md").write_text(content, encoding="utf-8")
            code, output, _ = self.run_validator(src, "--schema", "full")
            self.assertEqual(code, 1)
            self.assertIn(":7）", output)

    def test_br_source_checks_unknown_uncovered_and_core_p0(self):
        source = markdown_table(
            ["BR编号", "规则", "优先级"],
            [
                ["BR-001", "已知规则", "P0"],
                ["BR-002", "未覆盖规则", "P1"],
            ],
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src = root / "cases"
            src.mkdir()
            (root / "br.md").write_text(source, encoding="utf-8")
            (src / "01.模块.md").write_text(
                markdown_table(FULL_HEADER, [full_row(br="BR-999")]), encoding="utf-8"
            )
            code, output, _ = self.run_validator(
                src, "--schema", "full", "--br-source", str(root / "br.md")
            )
            self.assertEqual(code, 1)
            self.assertIn("BR-999' 未在来源目录中定义", output)
            self.assertIn("BR 'BR-002' 未被任何用例覆盖", output)
            self.assertIn("关键 BR 'BR-001' 未被 P0 用例覆盖", output)

    def test_br_source_without_priority_does_not_infer_core(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src = root / "cases"
            src.mkdir()
            (root / "br.md").write_text(
                markdown_table(["BR编号", "规则"], [["BR-001", "关键功能说明"]]),
                encoding="utf-8",
            )
            (src / "01.模块.md").write_text(
                markdown_table(
                    FULL_HEADER,
                    [
                        full_row(br="BR-001", priority="P1"),
                        full_row(case_id="SHOP-002", br="-", priority="P0"),
                    ],
                ),
                encoding="utf-8",
            )
            code, output, _ = self.run_validator(
                src,
                "--schema",
                "full",
                "--br-source",
                str(root / "br.md"),
                "--p0-ratio",
                "0",
            )
            self.assertEqual(code, 0, output)
            self.assertNotIn("关键 BR", output)


class ExcelTests(unittest.TestCase):
    def test_skips_outline_and_non_case_tables(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src = root / "cases"
            src.mkdir()
            (src / "00.测试用例大纲.md").write_text(
                markdown_table(LIGHT_HEADER, [light_row("OUT-001")]), encoding="utf-8"
            )
            content = markdown_table(["字段", "说明"], [["x", "y"]])
            content += "\n" + markdown_table(LIGHT_HEADER, [light_row()])
            (src / "01.设置.md").write_text(content, encoding="utf-8")
            out = root / "output.xlsx"
            result = build_excel(src, out)
            self.assertEqual(result["sheets"], 1)
            workbook = load_workbook(out)
            self.assertEqual(workbook.sheetnames, ["01_设置"])
            self.assertEqual(workbook.active["A2"].value, "SET-001")

    def test_outline_only_directory_still_writes_valid_workbook(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src = root / "cases"
            src.mkdir()
            (src / "00.测试用例大纲.md").write_text("# 大纲\n", encoding="utf-8")
            out = root / "output.xlsx"
            result = build_excel(src, out)
            self.assertEqual(result["sheets"], 0)
            self.assertEqual(load_workbook(out).sheetnames, ["Sheet"])

    def test_missing_template_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src = root / "cases"
            src.mkdir()
            (src / "01.设置.md").write_text(
                markdown_table(LIGHT_HEADER, [light_row()]), encoding="utf-8"
            )
            with self.assertRaises(FileNotFoundError):
                build_excel(src, root / "output.xlsx", root / "missing.xlsx")

    def test_all_tables_and_template_preservation_case_insensitive_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src = root / "cases"
            src.mkdir()
            content = markdown_table(LIGHT_HEADER, [light_row("SET-001")])
            content += "\n" + markdown_table(LIGHT_HEADER, [light_row("SET-002")])
            (src / "Cases.md").write_text(content, encoding="utf-8")

            template = root / "template.xlsx"
            workbook = Workbook()
            workbook.active.title = "cases"
            workbook.active["A1"] = "keep"
            workbook.save(template)

            out = root / "output.xlsx"
            result = build_excel(src, out, template, all_tables=True)
            workbook = load_workbook(out)
            self.assertEqual(workbook["cases"]["A1"].value, "keep")
            self.assertEqual(result["sheets"], 2)
            self.assertEqual(len(workbook.sheetnames), 3)
            self.assertEqual(len({name.casefold() for name in workbook.sheetnames}), 3)


if __name__ == "__main__":
    unittest.main()
