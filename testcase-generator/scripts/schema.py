"""Shared schemas and Markdown helpers for game test-case tools."""
from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Sequence

FULL_COLUMNS = (
    "用例编号", "所属模块", "用例标题", "用例类型", "优先级", "前置条件",
    "测试数据", "操作步骤", "预期结果", "实际结果", "结果", "关联BR", "备注",
)
LIGHT_COLUMNS = (
    "用例编号", "所属模块", "用例标题", "优先级", "前置条件",
    "测试数据", "操作步骤", "预期结果", "实际结果", "结果",
)
LIGHT_BR_COLUMNS = LIGHT_COLUMNS + ("关联BR", "备注")
HEADER_ALIASES = {"编号": "用例编号", "功能模块": "所属模块", "测试步骤": "操作步骤", "测试结果": "结果"}
VALID_PRIORITIES = frozenset({"P0", "P1", "P2"})
VALID_CASE_TYPES = frozenset({"正向", "异常", "边界", "等价类", "组合", "状态恢复", "联动"})
VALID_RESULT_STATUS = frozenset({"未执行", "通过", "失败", "阻塞", "跳过"})
CASE_ID_PATTERN = re.compile(r"^[A-Za-z0-9一-龥]+-\d{3}$")
BR_PATTERN = re.compile(r"^BR-\d{3}$")

@dataclass(frozen=True)
class SchemaDefinition:
    name: str
    columns: tuple[str, ...]
    required: frozenset[str]
    allow_extra: bool = False

SCHEMAS = {
    "full": SchemaDefinition("full", FULL_COLUMNS, frozenset(FULL_COLUMNS)),
    "light": SchemaDefinition("light", LIGHT_COLUMNS, frozenset(LIGHT_COLUMNS)),
    "light-br": SchemaDefinition("light-br", LIGHT_BR_COLUMNS, frozenset(LIGHT_BR_COLUMNS)),
}

@dataclass(frozen=True)
class ParsedRow:
    cells: list[str]
    source_line: int

@dataclass(frozen=True)
class ParsedTable:
    header: list[str]
    header_line: int
    separator_line: int | None
    rows: list[ParsedRow]
    table_index: int

@dataclass(frozen=True)
class SchemaResolution:
    schema_name: str | None
    indices: dict[str, int]
    original_names: dict[str, str]
    missing: tuple[str, ...]
    extra: tuple[str, ...]
    duplicate_aliases: tuple[tuple[str, str], ...] = ()

def canonicalize_header(name: str) -> str:
    name = name.strip()
    return HEADER_ALIASES.get(name, name)

def build_column_index(header: Sequence[str]) -> tuple[dict[str, int], dict[str, str], tuple[tuple[str, str], ...]]:
    indices: dict[str, int] = {}
    originals: dict[str, str] = {}
    duplicates: list[tuple[str, str]] = []
    for index, raw in enumerate(header):
        original = raw.strip()
        if not original:
            continue
        canonical = canonicalize_header(original)
        if canonical in indices:
            duplicates.append((originals[canonical], original))
        else:
            indices[canonical] = index
            originals[canonical] = original
    return indices, originals, tuple(duplicates)

def detect_schema(header: Sequence[str]) -> str | None:
    canonical = tuple(canonicalize_header(x) for x in header)
    if canonical == FULL_COLUMNS:
        return "full"
    if canonical == LIGHT_COLUMNS:
        return "light"
    if canonical == LIGHT_BR_COLUMNS:
        return "light-br"
    return None

def resolve_schema(header: Sequence[str], mode: str = "auto") -> SchemaResolution:
    indices, originals, duplicates = build_column_index(header)
    detected = detect_schema(header)
    if mode == "auto":
        requested = detected
        schema_name = detected
    elif mode == "legacy":
        requested = None
        schema_name = None
    elif mode in SCHEMAS:
        requested = mode
        schema_name = mode if detected == mode else None
    else:
        raise ValueError(f"unknown schema mode: {mode}")
    definition = SCHEMAS.get(requested)
    expected = set(definition.columns) if definition else set()
    missing = tuple(c for c in (definition.columns if definition else ()) if c not in indices)
    extra = tuple(
        canonicalize_header(x)
        for x in header
        if canonicalize_header(x) and canonicalize_header(x) not in expected
    )
    return SchemaResolution(schema_name, indices, originals, missing, extra, duplicates)

def is_case_table(header: Sequence[str]) -> bool:
    indices, _, _ = build_column_index(header)
    return "用例编号" in indices and "用例标题" in indices

def split_md_row(line: str) -> list[str]:
    placeholder = "\x00PIPE\x00"
    cells = line.rstrip("\r\n").replace(r"\|", placeholder).split("|")
    if cells and not cells[0].strip(): cells = cells[1:]
    if cells and not cells[-1].strip(): cells = cells[:-1]
    return [c.strip().replace(placeholder, "|") for c in cells]

def extract_md_tables(lines: Sequence[str]) -> list[ParsedTable]:
    tables: list[ParsedTable] = []
    header = None
    header_line = 0
    separator_line = None
    rows: list[ParsedRow] = []
    table_index = 0
    def finish() -> None:
        nonlocal header, header_line, separator_line, rows, table_index
        if header is not None and separator_line is not None:
            tables.append(ParsedTable(header, header_line, separator_line, rows, table_index))
            table_index += 1
        header = None; header_line = 0; separator_line = None; rows = []
    for line_number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line.startswith("|"):
            finish(); continue
        if re.match(r"^\|?[\s\-:|]+\|?$", line) and "-" in line:
            if header is not None:
                separator_line = line_number
            continue
        cells = split_md_row(raw)
        if header is None or separator_line is None:
            if header is not None:
                finish()
            header, header_line = cells, line_number
        else:
            rows.append(ParsedRow(cells, line_number))
    finish()
    return tables

def parse_md_tables(filepath: str) -> list[ParsedTable]:
    with open(filepath, "r", encoding="utf-8") as handle:
        return extract_md_tables(handle.readlines())

def parse_br_refs(value: str) -> list[str]:
    if not value or value.strip() == "-": return []
    return [part.strip() for part in re.split(r"[,，]", value) if part.strip()]

def iter_case_md_files(src_dir: str, *, exclude_outline: bool = True) -> list[str]:
    return sorted(
        name for name in os.listdir(src_dir)
        if name.casefold().endswith(".md") and (not exclude_outline or not name.startswith("00."))
    )

# Compatibility aliases used by existing callers.
_split_md_row = split_md_row
_extract_md_tables = extract_md_tables
