"""
功能测试用例生成器
根据功能需求生成全面的功能测试用例
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class FunctionalTestGenerator:
    """功能测试用例生成器"""

    # 特殊字符测试数据
    SPECIAL_CHARS = [
        ("英文双引号", '"'),
        ("英文单引号", "'"),
        ("左尖括号", "<"),
        ("右尖括号", ">"),
        ("反斜杠", "\\"),
        ("正斜杠", "/"),
        ("&符号", "&"),
        ("等于号", "="),
        ("分号", ";"),
        ("换行符", "\n"),
        ("制表符", "\t"),
        ("NULL字符", "\x00"),
        ("表情符号", "🎉"),
        ("中文标点", "，。？！"),
        ("空格", " "),
        ("多个空格", "   "),
    ]

    # 边界值数据
    BOUNDARY_VALUES = {
        'int': [-2147483649, -2147483648, -1, 0, 1, 2147483647, 2147483648],
        'str': ['', 'a' * 255, 'a' * 256, 'a' * 1000, 'a' * 10000],
        'float': [-1.7976931348623157e+308, -1.0, 0, 1.0, 1.7976931348623157e+308],
    }

    def __init__(self, module_name: str = "Module"):
        self.module_name = module_name
        self.testcase_id = 1
        self.testcases = []

    def generate(self, feature: Dict[str, Any]) -> List[Dict]:
        """
        根据功能描述生成测试用例

        Args:
            feature: 功能描述字典，包含 name, description, fields 等

        Returns:
            测试用例列表
        """
        self.testcases = []
        feature_name = feature.get('name', self.module_name)
        fields = feature.get('fields', [])

        # 生成正向测试用例
        self._generate_positive_tests(feature_name, fields)

        # 生成反向测试用例
        self._generate_negative_tests(feature_name, fields)

        # 生成边界值测试用例
        self._generate_boundary_tests(feature_name, fields)

        # 生成安全测试用例
        self._generate_security_tests(feature_name, fields)

        # 生成兼容性测试用例
        self._generate_compatibility_tests(feature_name)

        return self.testcases

    def _generate_positive_tests(self, feature_name: str, fields: List[Dict]):
        """生成正向测试用例"""
        # P0: 主流程测试
        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}主流程正常执行",
            priority="P0",
            preconditions="无",
            test_data="标准有效数据",
            steps=f"1. 进入{feature_name}页面\n2. 填写所有必填字段\n3. 提交请求\n4. 验证结果",
            expected="功能正常执行，返回成功结果",
            category="正向"
        ))

        # P1: 必填字段测试
        if fields:
            all_fields = ", ".join([f.get('name', '') for f in fields if f.get('required', False)])
            self.testcases.append(self._create_testcase(
                title=f"验证{feature_name}所有必填字段",
                priority="P0",
                preconditions="无",
                test_data=f"必填字段: {all_fields}",
                steps=f"1. 进入{feature_name}页面\n2. 仅填写必填字段\n3. 提交请求\n4. 验证结果",
                expected="功能正常执行，成功保存数据",
                category="正向"
            ))

        # P1: 可选字段测试
        optional_fields = [f for f in fields if not f.get('required', False)]
        if optional_fields:
            field_names = ", ".join([f.get('name', '') for f in optional_fields[:3]])
            self.testcases.append(self._create_testcase(
                title=f"验证{feature_name}必填+可选字段组合",
                priority="P1",
                preconditions="无",
                test_data=f"必填+部分可选字段: {field_names}",
                steps=f"1. 进入{feature_name}页面\n2. 填写必填和部分可选字段\n3. 提交请求\n4. 验证结果",
                expected="功能正常执行，正确保存所有数据",
                category="正向"
            ))

        # P2: 全量数据测试
        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}填写全部字段",
            priority="P2",
            preconditions="无",
            test_data="所有字段填写真实有效数据",
            steps=f"1. 进入{feature_name}页面\n2. 填写所有字段\n3. 提交请求\n4. 验证结果",
            expected="功能正常执行，所有数据正确保存",
            category="正向"
        ))

    def _generate_negative_tests(self, feature_name: str, fields: List[Dict]):
        """生成反向测试用例"""
        # P0: 缺少必填字段
        if fields:
            required_fields = [f for f in fields if f.get('required', False)]
            for field in required_fields[:2]:  # 限制数量
                self.testcases.append(self._create_testcase(
                    title=f"验证{feature_name}缺少必填字段【{field.get('name', '')}】",
                    priority="P0",
                    preconditions="无",
                    test_data=f"缺少字段: {field.get('name', '')}",
                    steps=f"1. 进入{feature_name}页面\n2. 不填写【{field.get('name', '')}】\n3. 提交请求",
                    expected=f"系统提示【{field.get('name', '该字段')}】不能为空",
                    category="反向"
                ))

        # P1: 空值测试
        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}所有字段为空",
            priority="P1",
            preconditions="无",
            test_data="所有字段留空",
            steps=f"1. 进入{feature_name}页面\n2. 所有字段留空\n3. 提交请求",
            expected="系统提示必填字段不能为空",
            category="反向"
        ))

        # P1: 格式错误
        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}邮箱格式错误",
            priority="P1",
            preconditions="无",
            test_data="邮箱: invalid-email",
            steps=f"1. 进入{feature_name}页面\n2. 输入错误格式的邮箱\n3. 提交请求",
            expected="系统提示邮箱格式不正确",
            category="反向"
        ))

        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}手机号格式错误",
            priority="P1",
            preconditions="无",
            test_data="手机号: 12345",
            steps=f"1. 进入{feature_name}页面\n2. 输入错误格式的手机号\n3. 提交请求",
            expected="系统提示手机号格式不正确",
            category="反向"
        ))

        # P1: 数据长度超限
        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}输入超长字符",
            priority="P1",
            preconditions="无",
            test_data="输入超过限制的字符数（5000字符）",
            steps=f"1. 进入{feature_name}页面\n2. 输入超长文本\n3. 提交请求",
            expected="系统提示输入内容过长，或截断处理",
            category="反向"
        ))

        # P2: 重复提交
        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}重复提交",
            priority="P2",
            preconditions="首次提交成功",
            test_data="与首次相同的数据",
            steps=f"1. 完成{feature_name}并提交\n2. 立即再次提交相同数据",
            expected="系统正确处理重复提交（成功或提示已存在）",
            category="反向"
        ))

    def _generate_boundary_tests(self, feature_name: str, fields: List[Dict]):
        """生成边界值测试用例"""
        # P1: 数值边界
        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}数值下边界",
            priority="P1",
            preconditions="无",
            test_data="数值字段使用最小允许值",
            steps=f"1. 进入{feature_name}页面\n2. 填写最小数值\n3. 提交请求",
            expected="功能正常执行，数据正确保存",
            category="边界值"
        ))

        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}数植上边界",
            priority="P1",
            preconditions="无",
            test_data="数值字段使用最大允许值",
            steps=f"1. 进入{feature_name}页面\n2. 填写最大数值\n3. 提交请求",
            expected="功能正常执行，数据正确保存",
            category="边界值"
        ))

        # P2: 字符串长度边界
        self.testcases.append(self._create_testcase(
            title=f"验证{feature_name}字符串长度边界",
            priority="P2",
            preconditions="无",
            test_data="字符串字段使用边界长度（255字符）",
            steps=f"1. 进入{feature_name}页面\n2. 输入255字符\n3. 提交请求",
            expected="功能正常执行，数据正确保存",
            category="边界值"
        ))

    def _generate_security_tests(self, feature_name: str, fields: List[Dict]):
        """生成安全测试用例"""
        # P0: SQL 注入
        sql_injection_tests = [
            ("单引号", "'"),
            ("OR 1=1", "' OR '1'='1"),
            ("UNION查询", "' UNION SELECT * FROM users--"),
            ("注释符", "admin'--"),
            ("DROP语句", "'; DROP TABLE users--"),
        ]

        for name, value in sql_injection_tests[:2]:  # 限制数量
            self.testcases.append(self._create_testcase(
                title=f"验证{feature_name}SQL注入攻击【{name}】",
                priority="P0",
                preconditions="无",
                test_data=f"输入SQL注入内容: {value[:30]}...",
                steps=f"1. 进入{feature_name}页面\n2. 输入SQL注入字符串\n3. 提交请求",
                expected="系统正确转义或拒绝，数据不被执行",
                category="安全",
                remark="安全测试用例"
            ))

        # P1: XSS 攻击
        xss_tests = [
            ("script标签", "<script>alert('xss')</script>"),
            ("img标签", "<img src=x onerror=alert('xss')>"),
            ("svg标签", "<svg onload=alert('xss')>"),
            ("JavaScript协议", "javascript:alert('xss')"),
        ]

        for name, value in xss_tests[:2]:
            self.testcases.append(self._create_testcase(
                title=f"验证{feature_name}XSS攻击【{name}】",
                priority="P1",
                preconditions="无",
                test_data=f"输入XSS内容: {value[:30]}...",
                steps=f"1. 进入{feature_name}页面\n2. 输入XSS字符串\n3. 提交请求",
                expected="系统正确转义，脚本不被执行",
                category="安全",
                remark="安全测试用例"
            ))

    def _generate_compatibility_tests(self, feature_name: str):
        """生成兼容性测试用例"""
        # 浏览器兼容
        browsers = [
            ("Chrome", "Chrome 最新版本"),
            ("Firefox", "Firefox 最新版本"),
            ("Safari", "Safari 最新版本"),
            ("Edge", "Edge 最新版本"),
        ]

        for browser, desc in browsers:
            self.testcases.append(self._create_testcase(
                title=f"验证{feature_name}在{browser}浏览器",
                priority="P1",
                preconditions=f"安装{browser}浏览器",
                test_data="标准有效数据",
                steps=f"1. 打开{browser}浏览器\n2. 进入{feature_name}\n3. 执行标准操作",
                expected=f"{desc}下功能正常",
                category="兼容性",
                remark=f"浏览器兼容性测试 - {browser}"
            ))

        # 移动端兼容
        devices = [
            ("iOS Safari", "iPhone/iPad Safari"),
            ("Android Chrome", "Android 手机 Chrome"),
        ]

        for device, desc in devices:
            self.testcases.append(self._create_testcase(
                title=f"验证{feature_name}在{device}端",
                priority="P1",
                preconditions=f"使用{device}设备",
                test_data="标准有效数据",
                steps=f"1. 打开{device}\n2. 进入{feature_name}\n3. 执行标准操作",
                expected=f"{desc}下功能正常",
                category="兼容性",
                remark=f"移动端兼容性测试 - {device}"
            ))

    def _create_testcase(self, title: str, priority: str, preconditions: str,
                         test_data: str, steps: str, expected: str,
                         category: str = "功能", remark: str = "") -> Dict:
        """创建单个测试用例"""
        tc = {
            "功能ID": f"FUNC_{self.module_name.upper()}_{self.testcase_id:03d}",
            "用例标题": title,
            "功能模块": self.module_name,
            "优先级": priority,
            "预置条件": preconditions,
            "测试数据": test_data,
            "执行步骤": steps,
            "预期结果": expected,
            "测试结果": "待执行",
            "测试版本号": "v1.0.0",
            "测试人员": "",
            "备注": remark,
            "测试类型": category
        }
        self.testcase_id += 1
        return tc


# 便捷函数
def generate_functional_testcases(module_name: str, features: List[Dict]) -> List[Dict]:
    """生成功能测试用例"""
    generator = FunctionalTestGenerator(module_name)
    all_cases = []
    for feature in features:
        all_cases.extend(generator.generate(feature))
    return all_cases
