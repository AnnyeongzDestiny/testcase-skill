#!/usr/bin/env python3
"""
测试用例生成器主程序
统一入口，支持手工用例文档和可导入 JSON 等输出模式
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers import PostmanParser, SwaggerParser, JsonSchemaParser, MarkdownParser, HarParser
from generators import APITestGenerator
from formatters import MarkdownFormatter, ExcelFormatter, PytestFormatter, PostmanFormatter, JMeterFormatter, ApifoxFormatter
from utils import validate_testcase


class TestCaseGenerator:
    """测试用例生成器主类"""

    SUPPORTED_INPUT_FORMATS = {
        'postman': ['.json'],
        'swagger': ['.json', '.yaml', '.yml'],
        'openapi': ['.json', '.yaml', '.yml'],
        'markdown': ['.md', '.txt'],
        'json': ['.json'],
        'har': ['.har'],
        'json_schema': ['.json']
    }

    MANUAL_OUTPUT_FORMATS = {
        'markdown': 'md',
        'excel': 'xlsx'
    }

    IMPORT_OUTPUT_FORMATS = {
        'apifox': 'json',
        'postman': 'json'
    }

    AUTOMATION_OUTPUT_FORMATS = {
        'pytest': 'py',
        'jmeter': 'jmx',
        'json': 'json'
    }

    SUPPORTED_OUTPUT_FORMATS = {
        **MANUAL_OUTPUT_FORMATS,
        **IMPORT_OUTPUT_FORMATS,
        **AUTOMATION_OUTPUT_FORMATS
    }

    def __init__(self):
        self.testcases = []

    def detect_format(self, filepath: str) -> str:
        """检测文件格式"""
        ext = Path(filepath).suffix.lower()

        if ext == '.docx':
            return 'unknown'

        if ext in ['.json']:
            # 尝试读取并检测类型
            with open(filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)

            if 'info' in content and 'item' in content:
                return 'postman'
            if 'openapi' in content or 'swagger' in content:
                return 'openapi'
            if 'paths' in content:
                return 'json'
            if 'log' in content and 'entries' in content:
                return 'har'

        if ext in ['.yaml', '.yml']:
            return 'openapi'

        if ext in ['.md', '.txt']:
            return 'markdown'

        return 'unknown'

    def parse_document(self, filepath: str) -> List[Dict]:
        """解析文档"""
        format_type = self.detect_format(filepath)

        parsers = {
            'postman': PostmanParser,
            'openapi': SwaggerParser,
            'swagger': SwaggerParser,
            'json': JsonSchemaParser,
            'json_schema': JsonSchemaParser,
            'markdown': MarkdownParser,
            'har': HarParser
        }

        parser_class = parsers.get(format_type)
        if not parser_class:
            raise ValueError(f"不支持的文件格式: {format_type}")

        # 文本类 parser 期望内容字符串；JSON/YAML/HAR/Postman 等可接受路径
        if format_type in ('markdown',):
            content = Path(filepath).read_text(encoding='utf-8')
            parser = parser_class(content)
        else:
            parser = parser_class(filepath)
        return parser.parse()

    def generate_testcases(self, apis: List[Dict], module_name: str, base_url: str = "") -> List[Dict]:
        """生成测试用例"""
        all_cases = []

        # 生成 API 测试用例
        generator = APITestGenerator(base_url, module_name)
        for api in apis:
            cases = generator.generate(api)
            all_cases.extend(cases)

        return all_cases

    def resolve_output_mode(self, args) -> tuple[str, str]:
        """根据参数解析输出模式和格式。"""
        if args.manual and args.import_json:
            raise ValueError("参数冲突: --manual 不能和 --import-json 同时使用")

        output_mode = args.mode
        output_format = args.output

        if args.manual:
            output_mode = 'manual'
            output_format = 'markdown'

        if args.import_json:
            if output_mode and output_mode != 'import':
                raise ValueError("参数冲突: --import-json 只能与 --mode import 搭配使用")
            output_mode = 'import'
            output_format = args.import_json

        if not output_mode:
            if output_format in self.IMPORT_OUTPUT_FORMATS:
                output_mode = 'import'
            elif output_format in self.AUTOMATION_OUTPUT_FORMATS:
                output_mode = 'automation'
            else:
                output_mode = 'manual'

        self._validate_mode_format(output_mode, output_format)
        return output_mode, output_format

    def _validate_mode_format(self, output_mode: str, output_format: str):
        """校验模式和输出格式是否匹配。"""
        mode_formats = {
            'manual': self.MANUAL_OUTPUT_FORMATS,
            'import': self.IMPORT_OUTPUT_FORMATS,
            'automation': self.AUTOMATION_OUTPUT_FORMATS,
            'export': self.SUPPORTED_OUTPUT_FORMATS,
        }
        allowed = mode_formats.get(output_mode)
        if not allowed:
            raise ValueError(f"不支持的输出模式: {output_mode}")
        if output_format == 'all' and output_mode == 'export':
            return
        if output_format not in allowed:
            allowed_names = ', '.join(allowed.keys())
            raise ValueError(f"输出模式 {output_mode} 不支持格式 {output_format}，可用格式: {allowed_names}")

    def _build_filename(self, output_dir: str, module_name: str, output_mode: str,
                        output_format: str, ext: str, timestamp: str) -> str:
        """按用途生成更清晰的文件名。"""
        name_map = {
            ('manual', 'markdown'): 'manual_interface_testcases',
            ('manual', 'excel'): 'manual_interface_testcases',
            ('import', 'apifox'): 'apifox_import',
            ('import', 'postman'): 'postman_import',
            ('automation', 'pytest'): 'pytest_scaffold',
            ('automation', 'jmeter'): 'jmeter_plan',
            ('automation', 'json'): 'raw_testcases',
        }
        suffix = name_map.get((output_mode, output_format), f"testcases_{output_format}")
        return f"{output_dir}/{module_name}_{suffix}_{timestamp}.{ext}"

    def format_output(self, testcases: List[Dict], module_name: str, base_url: str,
                      output_format: str, output_mode: str = 'manual', output_dir: str = ".") -> List[str]:
        """
        格式化并输出测试用例
        """
        output_files = []
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 过滤有效用例
        valid_cases = []
        for tc in testcases:
            is_valid, _ = validate_testcase(tc)
            if is_valid:
                valid_cases.append(tc)

        if output_format == 'all':
            formats = list(self.SUPPORTED_OUTPUT_FORMATS.keys())
            output_mode_for_format = {
                **{fmt: 'manual' for fmt in self.MANUAL_OUTPUT_FORMATS},
                **{fmt: 'import' for fmt in self.IMPORT_OUTPUT_FORMATS},
                **{fmt: 'automation' for fmt in self.AUTOMATION_OUTPUT_FORMATS},
            }
        else:
            self._validate_mode_format(output_mode, output_format)
            formats = [output_format]
            output_mode_for_format = {output_format: output_mode}

        for fmt in formats:
            ext = self.SUPPORTED_OUTPUT_FORMATS[fmt]
            fmt_mode = output_mode_for_format.get(fmt, output_mode)
            filename = self._build_filename(output_dir, module_name, fmt_mode, fmt, ext, timestamp)

            if fmt == 'markdown':
                content = MarkdownFormatter(module_name, base_url, profile='manual').format(valid_cases)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                output_files.append(filename)

            elif fmt == 'excel':
                filepath = ExcelFormatter(module_name).format(valid_cases, filename)
                output_files.append(filepath)

            elif fmt == 'pytest':
                code = PytestFormatter(module_name, base_url).format(valid_cases)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(code)
                output_files.append(filename)

            elif fmt == 'postman':
                collection = PostmanFormatter(module_name, base_url).format(valid_cases)
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(collection, f, ensure_ascii=False, indent=2)
                output_files.append(filename)

            elif fmt == 'apifox':
                collection = ApifoxFormatter(module_name, base_url).format(valid_cases)
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(collection, f, ensure_ascii=False, indent=2)
                output_files.append(filename)

            elif fmt == 'jmeter':
                xml = JMeterFormatter(module_name, base_url).format(valid_cases)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(xml)
                output_files.append(filename)

            elif fmt == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(valid_cases, f, ensure_ascii=False, indent=2)
                output_files.append(filename)

        return output_files

    def print_summary(self, testcases: List[Dict]):
        """打印用例统计"""
        print("\n" + "="*60)
        print("测试用例生成完成!")
        print("="*60)

        # 统计
        api_count = len([tc for tc in testcases if tc.get('用例编号', '').startswith('API_')])
        func_count = len([tc for tc in testcases if tc.get('功能ID', '').startswith('FUNC_')])

        # 优先级统计
        priority_stats = {}
        for tc in testcases:
            priority = tc.get('模块/优先级', tc.get('优先级', '未知'))
            priority_stats[priority] = priority_stats.get(priority, 0) + 1

        print(f"\n用例总数: {len(testcases)}")
        print(f"  - 接口测试用例: {api_count}")
        print(f"  - 功能测试用例: {func_count}")

        print("\n优先级分布:")
        for priority, count in sorted(priority_stats.items()):
            print(f"  - {priority}: {count}个")

        # 类型统计
        type_stats = {}
        for tc in testcases:
            tc_type = tc.get('测试类型', '未知')
            type_stats[tc_type] = type_stats.get(tc_type, 0) + 1

        print("\n测试类型分布:")
        for tc_type, count in type_stats.items():
            print(f"  - {tc_type}: {count}个")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="接口测试用例生成器 - 默认生成手工 Markdown 用例表，也可显式导出 Apifox/Postman JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认：生成接口手工测试用例 Markdown 表
  python main.py -i api.json -m UserAPI

  # 显式生成手工用例 Markdown 表
  python main.py -i swagger.yaml --manual -m AuthAPI -b https://api.example.com

  # 生成 Apifox 可导入 JSON
  python main.py -i postman.json --import-json apifox -m PaymentAPI --base-url https://api.example.com

  # 兼容旧用法：直接指定 apifox 输出
  python main.py -i postman.json -o apifox -m PaymentAPI --base-url https://api.example.com
        """
    )

    parser.add_argument('-i', '--input', required=True, help='输入文件路径')
    parser.add_argument('--mode', choices=['manual', 'import', 'automation', 'export'],
                        help='输出模式：manual=手工用例表(默认), import=Apifox/Postman 可导入 JSON, automation=自动化脚手架')
    parser.add_argument('--manual', action='store_true', help='生成手工接口测试用例 Markdown 表')
    parser.add_argument('--import-json', choices=['apifox', 'postman'], help='生成可导入 JSON：apifox 或 postman')
    parser.add_argument('-o', '--output', default='markdown', choices=['markdown', 'excel', 'pytest', 'postman', 'apifox', 'jmeter', 'json', 'all'],
                        help='输出格式 (默认: markdown，手工接口测试用例表)')
    parser.add_argument('-m', '--module', default='TestModule', help='模块名称')
    parser.add_argument('-b', '--base-url', default='', help='基础 URL')
    parser.add_argument('-d', '--output-dir', default='.', help='输出目录')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    generator = TestCaseGenerator()

    try:
        output_mode, output_format = generator.resolve_output_mode(args)

        # 解析文档
        if args.verbose:
            print(f"解析文件: {args.input}")
            print(f"输出模式: {output_mode}, 输出格式: {output_format}")
        apis = generator.parse_document(args.input)

        if args.verbose:
            print(f"解析到 {len(apis)} 个接口")

        # 生成测试用例
        testcases = generator.generate_testcases(apis, args.module, args.base_url)

        if args.verbose:
            print(f"生成 {len(testcases)} 个测试用例")

        # 输出
        files = generator.format_output(testcases, args.module, args.base_url, output_format, output_mode, args.output_dir)

        if args.verbose:
            for f in files:
                print(f"生成文件: {f}")

        # 打印统计
        generator.print_summary(testcases)

        print(f"\n输出文件: {', '.join(files)}")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
