"""Excel 导出核心逻辑。

Markdown 表格的识别和解析统一复用 :mod:`schema`，这里只负责把测试用例表
写入 Excel。模板工作表会原样保留，生成的工作表追加在模板工作表之后。
"""

from __future__ import annotations

import os
import re

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from schema import (
    ParsedTable,
    iter_case_md_files,
    is_case_table,
    parse_md_tables,
)


# ── 样式常量 ──────────────────────────────────────────
STYLES = {
    "header_font": Font(name="Microsoft YaHei", bold=True, size=11, color="FFFFFF"),
    "header_fill": PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid"),
    "header_align": Alignment(horizontal="center", vertical="center", wrap_text=True),
    "cell_font": Font(name="Microsoft YaHei", size=10),
    "cell_align": Alignment(vertical="top", wrap_text=True),
    "border": Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    ),
}

DEFAULT_COL_WIDTHS = [12, 14, 40, 8, 35, 45, 55]
MIN_COL_WIDTH = 8
MAX_COL_WIDTH = 60
_INVALID_SHEET_CHARS = re.compile(r"[\\/\?\*\[\]\:\.]")
_SHEET_NAME_MAX = 31


def _sanitize_sheet_name(name: str, used: set[str]) -> str:
    """清洗 sheet 名：剔除非法字符、限制长度、避免大小写不敏感冲突。"""
    sanitized = _INVALID_SHEET_CHARS.sub("_", name)[:_SHEET_NAME_MAX] or "Sheet"
    base = sanitized
    counter = 2
    used_folded = {item.casefold() for item in used}
    while sanitized.casefold() in used_folded:
        suffix = f"_{counter}"
        sanitized = base[: _SHEET_NAME_MAX - len(suffix)] + suffix
        counter += 1
    used.add(sanitized)
    return sanitized


def _apply_header_style(cell):
    cell.font = STYLES["header_font"]
    cell.fill = STYLES["header_fill"]
    cell.alignment = STYLES["header_align"]
    cell.border = STYLES["border"]


def _apply_cell_style(cell):
    cell.font = STYLES["cell_font"]
    cell.alignment = STYLES["cell_align"]
    cell.border = STYLES["border"]


def _set_col_widths(ws, col_count: int):
    for col_idx in range(1, col_count + 1):
        width = DEFAULT_COL_WIDTHS[col_idx - 1] if col_idx <= len(DEFAULT_COL_WIDTHS) else 20
        ws.column_dimensions[get_column_letter(col_idx)].width = max(
            MIN_COL_WIDTH, min(MAX_COL_WIDTH, width)
        )


def _write_table(ws, table: ParsedTable) -> None:
    """把已识别的测试用例表写入工作表。"""
    for col_idx, header in enumerate(table.header, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        _apply_header_style(cell)

    for row_idx, parsed_row in enumerate(table.rows, 2):
        for col_idx, value in enumerate(parsed_row.cells, 1):
            cell = ws.cell(
                row=row_idx,
                column=col_idx,
                value=re.sub(r"<br\s*/?>", "\n", value, flags=re.I),
            )
            _apply_cell_style(cell)

    _set_col_widths(ws, len(table.header))
    ws.freeze_panes = "A2"


def parse_md_table(filepath):
    """兼容旧调用方：返回文件中的第一个测试用例表。"""
    tables = [table for table in parse_md_tables(filepath) if is_case_table(table.header)]
    if not tables:
        return [], []
    table = tables[0]
    return table.header, [row.cells for row in table.rows]


def parse_md_all_tables(filepath):
    """兼容旧调用方：返回文件中的全部测试用例表。"""
    return [
        (table.header, [row.cells for row in table.rows])
        for table in parse_md_tables(filepath)
        if is_case_table(table.header)
    ]


def build_excel(src_dir, out_path, template_path=None, all_tables: bool = False):
    """将目录中的测试用例 Markdown 导出为一个 Excel 工作簿。

    ``00.`` 开头的 Markdown 文件和不符合测试用例 schema 的表格会被忽略。
    如果提供模板，模板中的所有工作表都会保留，生成的工作表追加在其后。
    """
    output_dir = os.path.dirname(os.path.abspath(os.fspath(out_path)))
    os.makedirs(output_dir, exist_ok=True)

    if template_path:
        if not os.path.isfile(template_path):
            raise FileNotFoundError(f"template not found: {template_path}")
        wb = load_workbook(template_path)
    else:
        wb = Workbook()
        wb.remove(wb.active)

    used_sheet_names = set(wb.sheetnames)
    details = []
    md_files = iter_case_md_files(src_dir)

    for md_file in md_files:
        filepath = os.path.join(src_dir, md_file)
        case_tables = [
            table for table in parse_md_tables(filepath) if is_case_table(table.header)
        ]
        if not all_tables:
            case_tables = case_tables[:1]

        stem = md_file[:-3]
        for table_idx, table in enumerate(case_tables):
            base_name = stem if table_idx == 0 else f"{stem}_{table_idx + 1}"
            sheet_name = _sanitize_sheet_name(base_name, used_sheet_names)
            ws = wb.create_sheet(title=sheet_name)
            _write_table(ws, table)
            details.append((sheet_name, len(table.rows)))

    if not details and not wb.sheetnames:
        wb.create_sheet(title="Sheet")

    wb.save(out_path)
    return {
        "sheets": len(details),
        "total_cases": sum(count for _, count in details),
        "details": details,
    }
