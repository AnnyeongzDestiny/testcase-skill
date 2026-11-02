# scripts 说明

本目录提供需求转换、Markdown 用例校验和按需 Excel 导出。当前版本不生成 HTML。

## 环境

```bash
pip install -r requirements.txt
```

主要依赖：`openpyxl`、`python-docx`、`pdfplumber`；`.doc` 转换仅支持安装 Microsoft Office 与 `pywin32` 的 Windows 环境。

## 输入转换

`.md` 直接读取，不运行转换脚本。`.docx`、`.doc`、`.pdf`、`.txt` 可执行：

```bash
python -B convert_to_md.py <输入文件> --output-dir <目录>
```

无法转换 `.doc` 时，先在 Word/WPS 中另存为 `.docx`，或使用 LibreOffice 转换。

## Markdown 校验

```bash
python -B validate.py <md目录> --schema auto
python -B validate.py <md目录> --schema full --br-source <prd-analysis.md>
```

`--schema` 取值：

- `auto`：识别完整 13 列、目标十列或带 BR 的追踪轻量结构；其他表头按历史结构兼容校验。
- `full`：要求精确的完整 13 列。
- `light`：要求精确的目标十列（支持标准字段别名）。
- `light-br`：要求目标十列加 `关联BR`、`备注`。
- `legacy`：显式按历史动态列校验。

`--strict` 仅为旧命令兼容参数，等同 `--schema full`，会输出弃用提示，不能与显式 `--schema` 同用。

`--br-source` 从 Markdown BR 目录检查未知引用、未覆盖规则，以及来源明确标记为核心/P0 的 BR 是否被 P0 用例覆盖。它不能与无追溯列的 `light` 模式同用。

validator 默认跳过 `00.` 大纲文件；编号、优先级、逐行必填字段、测试数据、用例类型、结果状态、BR、步骤编号、具体预期和 P0 比例均会校验。

## Excel 导出

只在用户明确要求 Excel 时执行：

```bash
python -B save_testcases.py <md目录> --output-dir <导出目录>
python -B save_testcases.py <md目录> --output-dir <导出目录> --template <模板.xlsx> --all-tables
```

参数：

- `--name`：输出文件名，不含 `.xlsx`。
- `--template`：加载模板并保留原有 sheet 和内容，将新用例 sheet 追加到末尾。
- `--all-tables`：导出每个 Markdown 文件内的全部用例表；默认只导出第一张用例表。

导出默认跳过 `00.` 大纲和不含用例编号/标题的非用例表。一份 Markdown 文件通常对应一个 sheet；非法 sheet 名字符会替换为 `_`，重名会自动增加序号。统计只包含新生成的用例 sheet。

## 文件索引

| 文件 | 作用 |
|---|---|
| `schema.py` | schema、字段别名、枚举、Markdown 解析和文件筛选的共享实现 |
| `validate.py` | Markdown 用例与 BR 覆盖校验 |
| `convert_to_md.py` | 非 Markdown 需求文件转换 |
| `excel_generator.py` | Excel 工作簿生成核心 |
| `save_testcases.py` | Excel-only 命令入口 |
