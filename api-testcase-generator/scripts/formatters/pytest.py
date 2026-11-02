"""
Pytest 输出格式化器
生成 pytest 格式的自动化测试代码
"""

import json
from datetime import datetime
from typing import Dict, List, Any


class PytestFormatter:
    """Pytest 格式化器"""

    def __init__(self, module_name: str = "TestModule", base_url: str = ""):
        self.module_name = module_name
        self.base_url = base_url
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def format(self, testcases: List[Dict]) -> str:
        """
        格式化测试用例为 pytest 代码

        Args:
            testcases: 测试用例列表

        Returns:
            pytest 代码字符串
        """
        # 筛选 API 测试用例
        api_cases = [tc for tc in testcases if tc.get('用例编号', '').startswith('API_')]

        code = self._header()

        # 按接口分组
        grouped = {}
        for tc in api_cases:
            interface = tc.get('接口名称', 'Unknown')
            if interface not in grouped:
                grouped[interface] = []
            grouped[interface].append(tc)

        for interface, cases in grouped.items():
            code += self._format_interface_test(interface, cases)

        code += self._footer()

        return code

    def _header(self) -> str:
        """生成文件头部"""
        return f'''"""{self.module_name} 测试用例
自动化生成的 pytest 测试代码

生成时间: {self.timestamp}
Base URL: {self.base_url}
"""

import pytest
import requests
import json
from typing import Dict, Any


# 测试配置
BASE_URL = "{self.base_url}"


class TestSetup:
    """测试配置类"""

    @pytest.fixture(scope="session")
    def base_url(self):
        return BASE_URL

    @pytest.fixture(scope="session")
    def headers(self):
        return {{
            "Content-Type": "application/json",
            "Accept": "application/json"
        }}

    @pytest.fixture
    def auth_token(self):
        """获取认证 Token"""
        # TODO: 实现登录逻辑
        return None


class TestValidation:
    """响应验证工具类"""

    @staticmethod
    def validate_response(response, expected_status: int = 200):
        assert response.status_code == expected_status, \\
            f"期望状态码 {{expected_status}}, 实际 {{response.status_code}}"

    @staticmethod
    def validate_json(response):
        assert response.headers.get("Content-Type", "").startswith("application/json"), \\
            "响应不是 JSON 格式"

    @staticmethod
    def validate_field(response, field_name: str):
        data = response.json()
        assert field_name in data, f"响应缺少字段: {{field_name}}"


'''

    def _format_interface_test(self, interface: str, cases: List[Dict]) -> str:
        """生成单个接口的测试类"""
        class_name = self._to_class_name(interface)
        code = f'\nclass Test{class_name}:\n'
        code += f'    """{interface} 测试类"""\n\n'

        for idx, tc in enumerate(cases):
            test_name = self._to_method_name(tc.get('用例标题', f'test_{idx}'))
            priority = tc.get('模块/优先级', 'P1').split('/')[-1]

            # 获取测试数据
            url = tc.get('请求URL', '')
            method = tc.get('请求类型', 'GET')
            headers = self._parse_headers(tc.get('请求头', ''))
            data = tc.get('请求数据', '')

            # 根据优先级决定是否标记为 skip
            skip_condition = '@pytest.mark.skip(reason="P2低优先级")' if priority == 'P2' else ''

            # 构建请求代码
            code += f'''    {skip_condition}
    def {test_name}(self, base_url, headers):
        """{tc.get('用例标题', '')}"""
'''

            # 处理 URL
            if url.startswith('/'):
                code += f'''        url = f"{{base_url}}{url}"
'''
            else:
                code += f'''        url = "{{base_url}}/" + "{url.lstrip('/')}"
'''

            # 处理请求头
            if headers:
                code += f'        test_headers = headers.copy()\n'
                for k, v in headers.items():
                    code += f'        test_headers["{k}"] = "{v}"\n'
                code += '\n'

            # 处理请求数据和请求方法
            data_json = repr(data) if data else 'None'
            if method in ['GET', 'HEAD', 'DELETE']:
                code += f'''        response = requests.{method.lower()}(url, headers=test_headers)
'''
            else:
                code += f'''        response = requests.{method.lower()}(url, headers=test_headers, json={data_json})
'''

            expected_status = tc.get('预期响应状态', 200)
            code += f'''
        # 验证响应状态
        assert response.status_code == {expected_status}, f"期望{{expected_status}}, 实际{{response.status_code}}"

        # 验证响应格式
        TestValidation.validate_json(response)

        # 验证响应数据
        data = response.json()
        # TODO: 根据预期响应调整验证逻辑
        # expected = {tc.get('预期响应信息', '{}')}
        # assert data.get("code") == expected.get("code")
'''

        return code

    def _footer(self) -> str:
        """生成文件尾部"""
        return '''

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''

    def _to_class_name(self, name: str) -> str:
        """转换为类名"""
        # 移除特殊字符，转驼峰
        words = []
        current = ''
        for char in name:
            if char.isalnum():
                current += char
            else:
                if current:
                    words.append(current)
                    current = ''
        if current:
            words.append(current)

        return ''.join(word.capitalize() for word in words if word)

    def _to_method_name(self, name: str) -> str:
        """转换为方法名"""
        # 转小写下划线
        name = name.lower()
        name = name.replace(' ', '_')
        name = name.replace('-', '_')
        name = name.replace('(', '')
        name = name.replace(')', '')
        # 移除特殊字符
        import re
        name = re.sub(r'[^a-z0-9_]', '', name)
        # 限制长度
        if len(name) > 50:
            name = name[:50]
        return f"test_{name}" if name else "test_default"

    def _parse_headers(self, header_str: str) -> Dict:
        """解析请求头字符串"""
        headers = {}
        for line in header_str.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                headers[k.strip()] = v.strip()
        return headers

    def save(self, code: str, filepath: str):
        """保存 pytest 文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        return filepath


# 便捷函数
def format_pytest(testcases: List[Dict], module_name: str, base_url: str = "") -> str:
    """格式化测试用例为 pytest 代码"""
    return PytestFormatter(module_name, base_url).format(testcases)
