#!/usr/bin/env python3
"""
需求文档格式转换脚本
支持将 .docx / .doc / .pdf / .txt 转换为 .md 格式

用法:
    python convert_to_md.py <输入文件路径> [--output-dir DIR]

示例:
    python convert_to_md.py "D:/docs/需求文档.docx"
    python convert_to_md.py "D:/docs/需求.pdf" --output-dir "D:/output"

输出:
    默认输出到输入文件同目录，文件名保持一致仅后缀改为 .md

依赖说明:
    - .docx 需要 python-docx（必装）
    - .pdf  需要 pdfplumber（必装）
    - .doc  需要 pywin32 + Windows + Microsoft Office
            其他平台会提示用户先用 Word/WPS 另存为 .docx
            或安装 LibreOffice 后自行转换
"""

import sys
import os
import argparse
from pathlib import Path


def convert_docx_to_md(input_path: str) -> str:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P

    doc = Document(input_path)
    lines = []
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            para = Paragraph(child, doc)
            text = para.text.strip()
            if not text:
                lines.append("")
                continue
            style_name = para.style.name.lower() if para.style else ""
            if "heading 1" in style_name:
                lines.append(f"# {text}")
            elif "heading 2" in style_name:
                lines.append(f"## {text}")
            elif "heading 3" in style_name:
                lines.append(f"### {text}")
            elif "heading 4" in style_name:
                lines.append(f"#### {text}")
            elif "list" in style_name:
                lines.append(f"- {text}")
            else:
                lines.append(text)
        elif isinstance(child, CT_Tbl):
            table = Table(child, doc)
            lines.append("")
            for i, row in enumerate(table.rows):
                cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
                lines.append("| " + " | ".join(cells) + " |")
                if i == 0:
                    lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
            lines.append("")
    return "\n".join(lines)


def convert_doc_to_md(input_path: str) -> str:
    """仅 Windows + Microsoft Office 环境可用。其他平台会给出明确降级指引。"""
    if sys.platform != "win32":
        print(
            "错误：.doc 格式转换当前仅支持 Windows + Microsoft Office 环境。\n"
            f"当前平台：{sys.platform}\n"
            "降级方案：\n"
            "  1) 在 Word/WPS 中将文件另存为 .docx 后重跑本脚本；\n"
            "  2) 或安装 LibreOffice 后用 `soffice --headless --convert-to docx <file>` 预处理。"
        )
        sys.exit(2)

    try:
        import win32com.client  # noqa: F401
    except ImportError:
        print(
            "错误：缺少 pywin32 依赖，无法调用 Word COM 组件。\n"
            "请执行：pip install pywin32\n"
            "或改用 .docx 输入文件。"
        )
        sys.exit(2)

    import win32com.client  # noqa: F401
    import tempfile
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    fd, temp_docx = tempfile.mkstemp(suffix=".docx")
    os.close(fd)
    doc = None
    try:
        doc = word.Documents.Open(os.path.abspath(input_path))
        doc.SaveAs2(temp_docx, FileFormat=16)
        doc.Close()
        doc = None
        return convert_docx_to_md(temp_docx)
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()
        if os.path.exists(temp_docx):
            os.unlink(temp_docx)


def convert_pdf_to_md(input_path: str) -> str:
    import pdfplumber
    lines = []
    with pdfplumber.open(input_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.append(text)
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                lines.append("")
                for i, row in enumerate(table):
                    cells = [str(cell or "").replace("\n", " ").strip() for cell in row]
                    lines.append("| " + " | ".join(cells) + " |")
                    if i == 0:
                        lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
                lines.append("")
    return "\n".join(lines)


def convert_txt_to_md(input_path: str) -> str:
    with open(input_path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(description="将需求文档转换为 Markdown 格式")
    parser.add_argument("input", help="输入文件路径（支持 .docx / .doc / .pdf / .txt）")
    parser.add_argument("--output-dir", help="输出目录（默认与输入文件同目录）")
    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"错误：文件不存在 - {input_path}")
        sys.exit(1)

    ext = input_path.suffix.lower()
    converters = {
        ".docx": convert_docx_to_md,
        ".doc": convert_doc_to_md,
        ".pdf": convert_pdf_to_md,
        ".txt": convert_txt_to_md,
    }

    if ext not in converters:
        print(f"错误：不支持的格式 '{ext}'，支持的格式：{', '.join(converters.keys())}")
        sys.exit(1)

    print(f"正在转换: {input_path.name} ({ext})")
    try:
        md_content = converters[ext](str(input_path))
    except SystemExit:
        raise
    except Exception as e:
        print(f"转换失败: {e}")
        sys.exit(1)

    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = input_path.parent

    output_path = output_dir / (input_path.stem + ".md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"转换完成: {output_path}")
    print(f"文件大小: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()