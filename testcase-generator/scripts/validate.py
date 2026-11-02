#!/usr/bin/env python3
"""Validate Markdown game test cases."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import (  # noqa: E402
    BR_PATTERN,
    CASE_ID_PATTERN,
    VALID_CASE_TYPES,
    VALID_PRIORITIES,
    VALID_RESULT_STATUS,
    iter_case_md_files,
    canonicalize_header,
    is_case_table,
    parse_br_refs,
    parse_md_tables,
    resolve_schema,
)

REQUIRED_COLUMNS = {
    "用例编号",
    "用例标题",
    "优先级",
    "前置条件",
    "操作步骤",
    "预期结果",
}
VAGUE_RESULT_PATTERN = re.compile(
    r"^(?:步骤\s*\d+[：:]\s*)?"
    r"(?:功能|界面|显示|操作|流程|结果|状态|运行)?"
    r"(?:正常|正确|成功|失败|无异常)[。.!！]?$",
    re.I,
)
STEP_NUMBER_PATTERN = re.compile(r"(?:^|<br>\s*|\n\s*)\d+[a-zA-Z]?[\.、\)]")
CORE_MARKER_PATTERN = re.compile(r"^(?:P0|核心|关键|是)$", re.I)
CORE_HEADER_PATTERN = re.compile(r"^(?:优先级|等级|级别|重要性|是否核心|核心规则)$", re.I)


@dataclass(frozen=True)
class ValidationResult:
    p0_count: int
    case_count: int
    errors: list[str]
    referenced_brs: set[str]
    p0_brs: set[str]


def _canonical_header(name: str) -> str:
    return canonicalize_header(name)


def _cell(row: list[str], indices: dict[str, int], name: str) -> str:
    index = indices.get(name)
    return row[index].strip() if index is not None and index < len(row) else ""


def _check_non_empty(
    row: list[str],
    indices: dict[str, int],
    name: str,
    case_id: str,
    errors: list[str],
) -> None:
    if name in indices and not _cell(row, indices, name):
        errors.append(f"{case_id}: {name} 为空")


def parse_br_source(path: str) -> tuple[dict[str, int], set[str]]:
    """Return BR definitions and explicitly marked core BRs from Markdown tables."""
    definitions: dict[str, int] = {}
    core: set[str] = set()

    for table in parse_md_tables(path):
        headers = [_canonical_header(name) for name in table.header]
        br_index = next(
            (i for i, name in enumerate(headers) if name in {"BR编号", "BR ID", "BR"}),
            None,
        )
        if br_index is None:
            continue
        core_indices = [
            i for i, name in enumerate(headers) if CORE_HEADER_PATTERN.fullmatch(name)
        ]
        for parsed in table.rows:
            if br_index >= len(parsed.cells):
                continue
            br = parsed.cells[br_index].strip()
            if not BR_PATTERN.fullmatch(br):
                continue
            if br in definitions:
                raise ValueError(f"BR 定义重复: {br}")
            definitions[br] = parsed.source_line
            if any(
                i < len(parsed.cells)
                and CORE_MARKER_PATTERN.fullmatch(parsed.cells[i].strip())
                for i in core_indices
            ):
                core.add(br)

    if not definitions:
        raise ValueError("BR 来源中未找到可识别的 BR 目录")
    return definitions, core


def validate_file(
    filepath: str,
    schema_mode: str,
    seen_ids: dict[str, str],
    _table=None,
) -> ValidationResult:
    if _table is None:
        tables = parse_md_tables(filepath)
        if not tables:
            return ValidationResult(
                0, 0, [f"{filepath}: 未解析到表格"], set(), set()
            )
        case_tables = [table for table in tables if is_case_table(table.header)]
        selected = case_tables or [tables[0]]
        results = [
            validate_file(filepath, schema_mode, seen_ids, table)
            for table in selected
        ]
        return ValidationResult(
            sum(result.p0_count for result in results),
            sum(result.case_count for result in results),
            [error for result in results for error in result.errors],
            set().union(*(result.referenced_brs for result in results)),
            set().union(*(result.p0_brs for result in results)),
        )

    table = _table
    header = table.header
    rows = table.rows
    resolution = resolve_schema(header, schema_mode)
    indices = resolution.indices
    errors: list[str] = []

    for first, second in resolution.duplicate_aliases:
        errors.append(f"{filepath}: 表头 '{first}' 与 '{second}' 表示同一字段，不能同时存在")

    if schema_mode != "legacy" and resolution.schema_name is None:
        if schema_mode == "auto":
            # auto 对无法识别的旧表头回退到 legacy 校验。
            missing = REQUIRED_COLUMNS - set(indices)
        else:
            errors.append(f"{filepath}:{table.header_line}: 表头不符合 schema {schema_mode}")
            missing = set(resolution.missing)
    elif schema_mode == "legacy":
        missing = REQUIRED_COLUMNS - set(indices)
    else:
        missing = set(resolution.missing)

    if missing:
        errors.append(
            f"{filepath}:{table.header_line}: 缺少必填列: {', '.join(sorted(missing))}"
        )
    if not rows:
        errors.append(f"{filepath}: 表格无数据行")
        return ValidationResult(0, 0, errors, set(), set())

    p0_count = 0
    referenced_brs: set[str] = set()
    p0_brs: set[str] = set()

    for parsed in rows:
        row = parsed.cells
        line_number = parsed.source_line
        if len(row) != len(header):
            errors.append(
                f"{filepath}:{line_number}: 行列数不匹配"
                f"（表头 {len(header)} 列，数据 {len(row)} 列）"
            )
            continue

        case_id = _cell(row, indices, "用例编号")
        if not case_id:
            errors.append(f"{filepath}:{line_number}: 存在用例编号为空的数据行")
            continue
        if not CASE_ID_PATTERN.fullmatch(case_id):
            errors.append(f"{case_id}: 编号格式不符合 {{模块缩写}}-{{三位数字}}")
        if case_id in seen_ids:
            errors.append(f"{case_id}: 编号重复（首次出现于 {seen_ids[case_id]}）")
        else:
            seen_ids[case_id] = f"{filepath}:{line_number}"

        priority = _cell(row, indices, "优先级")
        if not priority:
            errors.append(f"{case_id}: 优先级为空")
        elif priority not in VALID_PRIORITIES:
            errors.append(f"{case_id}: 优先级 '{priority}' 不合法（应为 P0/P1/P2）")
        elif priority == "P0":
            p0_count += 1

        for name in ("用例标题", "所属模块", "前置条件", "操作步骤", "预期结果"):
            _check_non_empty(row, indices, name, case_id, errors)

        case_type = _cell(row, indices, "用例类型")
        if "用例类型" in indices and case_type not in VALID_CASE_TYPES:
            values = "/".join(sorted(VALID_CASE_TYPES))
            errors.append(f"{case_id}: 用例类型 '{case_type}' 不合法（应为 {values} 之一）")

        if "测试数据" in indices and not _cell(row, indices, "测试数据"):
            errors.append(f"{case_id}: 测试数据为空（无独立输入数据应填 '-'）")

        result = _cell(row, indices, "结果")
        if "结果" in indices:
            if not result:
                errors.append(f"{case_id}: 结果为空（生成时应填 '未执行'）")
            elif result not in VALID_RESULT_STATUS:
                values = "/".join(sorted(VALID_RESULT_STATUS))
                errors.append(f"{case_id}: 结果 '{result}' 不合法（应为 {values} 之一）")

        br_value = _cell(row, indices, "关联BR")
        case_brs: set[str] = set()
        if "关联BR" in indices:
            if not br_value:
                errors.append(f"{case_id}: 关联BR为空（无追溯要求时应填 '-'）")
            for br in parse_br_refs(br_value):
                if not BR_PATTERN.fullmatch(br):
                    errors.append(
                        f"{case_id}: 关联BR '{br}' 格式不合法"
                        "（应为 BR-XXX，三位数字）"
                    )
                else:
                    case_brs.add(br)
            if (
                br_value == "-"
                and "备注" in indices
                and not _cell(row, indices, "备注")
            ):
                errors.append(f"{case_id}: 关联BR为 '-' 时，备注需说明跳过追溯的原因")
        referenced_brs.update(case_brs)
        if priority == "P0":
            p0_brs.update(case_brs)

        expected = _cell(row, indices, "预期结果")
        segments = [
            segment.strip()
            for segment in re.split(r"<br\s*/?>|\r?\n", expected, flags=re.I)
            if segment.strip()
        ]
        vague = [
            segment for segment in segments if VAGUE_RESULT_PATTERN.fullmatch(segment)
        ]
        if vague:
            errors.append(f"{case_id}: 预期结果存在空泛表述: {', '.join(vague)}")

        steps = _cell(row, indices, "操作步骤")
        if steps and not STEP_NUMBER_PATTERN.search(steps):
            errors.append(f"{case_id}: 操作步骤应采用数字编号（如 1. / 2.）")

    return ValidationResult(
        p0_count,
        len(rows),
        errors,
        referenced_brs,
        p0_brs,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown game test cases")
    parser.add_argument("src_dir")
    parser.add_argument("--p0-ratio", type=float, default=0.30)
    parser.add_argument(
        "--schema",
        choices=("auto", "full", "light", "light-br", "legacy"),
        default="auto",
    )
    parser.add_argument("--strict", action="store_true", help="Deprecated compatibility alias")
    parser.add_argument("--br-source")
    args = parser.parse_args(argv)

    if args.strict and args.schema != "auto":
        parser.error("--strict 不能与显式 --schema 同时使用")
    if args.strict:
        print("Warning: --strict 已弃用，请使用 --schema full。", file=sys.stderr)
    if not os.path.isdir(args.src_dir):
        print(f"Error: directory not found: {args.src_dir}")
        return 1
    if not 0 <= args.p0_ratio <= 1:
        print("Error: --p0-ratio must be between 0 and 1")
        return 1
    if args.br_source and args.schema == "light":
        print("Error: --br-source 不能与未追踪的 light schema 同时使用")
        return 1

    md_files = iter_case_md_files(args.src_dir)
    if not md_files:
        print(f"Error: no .md files found in {args.src_dir}")
        return 1

    source_definitions: dict[str, int] | None = None
    source_core: set[str] = set()
    if args.br_source:
        try:
            source_definitions, source_core = parse_br_source(args.br_source)
        except (OSError, ValueError) as exc:
            print(f"Error: {exc}")
            return 1

    mode = "full" if args.strict else args.schema
    all_errors: list[str] = []
    seen_ids: dict[str, str] = {}
    referenced_brs: set[str] = set()
    p0_brs: set[str] = set()
    total_cases = 0
    total_p0 = 0
    stats: list[tuple[str, int, int]] = []

    for name in md_files:
        result = validate_file(os.path.join(args.src_dir, name), mode, seen_ids)
        total_cases += result.case_count
        total_p0 += result.p0_count
        referenced_brs.update(result.referenced_brs)
        p0_brs.update(result.p0_brs)
        stats.append((name, result.case_count, result.p0_count))
        all_errors.extend(result.errors)
        if result.case_count and result.p0_count == 0:
            all_errors.append(f"{name}: 模块至少应包含 1 条 P0 用例")

    if source_definitions is not None:
        defined_brs = set(source_definitions)
        for br in sorted(referenced_brs - defined_brs):
            all_errors.append(f"关联BR '{br}' 未在来源目录中定义")
        for br in sorted(defined_brs - referenced_brs):
            all_errors.append(f"BR '{br}' 未被任何用例覆盖")
        for br in sorted(source_core - p0_brs):
            all_errors.append(f"关键 BR '{br}' 未被 P0 用例覆盖")

    if total_cases and total_p0 / total_cases < args.p0_ratio:
        all_errors.append(
            f"P0 用例占比 {total_p0 / total_cases:.1%} 低于阈值 "
            f"{args.p0_ratio:.0%} ({total_p0}/{total_cases})"
        )

    print(f"Validated {len(md_files)} file(s), {total_cases} case(s).\n")
    for name, count, p0_count in stats:
        if count:
            print(f"  {name}: {count} cases, P0={p0_count} ({p0_count / count:.0%})")
        else:
            print(f"  {name}: no data")
    print()

    if all_errors:
        print(f"Found {len(all_errors)} issue(s):")
        for error in all_errors:
            print(f"  - {error}")
        return 1

    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
