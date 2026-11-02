"""
Postman Collection 输出格式化器
生成 Postman 格式的测试集合
"""

import json
from datetime import datetime
from typing import Dict, List, Any


class PostmanFormatter:
    """Postman 格式化器"""

    def __init__(self, module_name: str = "TestModule", base_url: str = ""):
        self.module_name = module_name
        self.base_url = base_url
        self.timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def format(self, testcases: List[Dict]) -> Dict:
        """
        格式化测试用例为 Postman Collection

        Args:
            testcases: 测试用例列表

        Returns:
            Postman Collection 格式的字典
        """
        collection = {
            "info": {
                "_postman_id": self._generate_id(),
                "name": f"{self.module_name} Test Cases",
                "description": f"Auto-generated test cases for {self.module_name}",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [],
            "variable": [
                {
                    "key": "baseUrl",
                    "value": self.base_url,
                    "type": "string"
                }
            ]
        }

        # 按接口分组
        grouped = {}
        for tc in testcases:
            if tc.get('用例编号', '').startswith('API_'):
                interface = tc.get('接口名称', 'Unknown')
                if interface not in grouped:
                    grouped[interface] = []
                grouped[interface].append(tc)

        # 创建测试文件夹和请求
        for interface, cases in grouped.items():
            folder = self._create_folder(interface, cases)
            collection["item"].append(folder)

        return collection

    def _create_folder(self, folder_name: str, cases: List[Dict]) -> Dict:
        """创建测试文件夹"""
        folder = {
            "name": folder_name,
            "item": []
        }

        for tc in cases:
            request = self._create_request(tc)
            folder["item"].append(request)

        return folder

    def _create_request(self, tc: Dict) -> Dict:
        """创建单个请求"""
        url = tc.get('请求URL', '')
        method = tc.get('请求类型', 'GET')
        headers = tc.get('请求头', '')
        body_data = tc.get('请求数据', '')

        # 构建请求对象
        request = {
            "name": tc.get('用例标题', 'Unnamed Test'),
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "exec": self._generate_test_script(tc),
                        "type": "text/javascript"
                    }
                }
            ],
            "request": {
                "method": method,
                "header": self._parse_headers(headers),
                "body": self._parse_body(method, body_data),
                "url": {
                    "raw": url if url.startswith('http') else f"{self.base_url}/{url}",
                    "host": ["{{baseUrl}}"],
                    "path": url.strip('/').split('/') if url and not url.startswith('http') else []
                }
            },
            "response": []
        }

        # 如果 URL 包含变量，修复 path
        if url and '{{' in url:
            request["request"]["url"]["raw"] = url

        return request

    def _parse_headers(self, header_str: str) -> List[Dict]:
        """解析请求头"""
        headers = []
        for line in header_str.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                headers.append({
                    "key": k.strip(),
                    "value": v.strip(),
                    "type": "text"
                })
        return headers

    def _parse_body(self, method: str, body_str: str) -> Dict:
        """解析请求体"""
        if method in ['GET', 'HEAD']:
            return {"mode": "raw", "raw": "", "options": {"raw": {"language": "json"}}}

        if not body_str or body_str == '{}':
            return {"mode": "raw", "raw": "", "options": {"raw": {"language": "json"}}}

        try:
            body_obj = json.loads(body_str)
            return {
                "mode": "raw",
                "raw": json.dumps(body_obj, ensure_ascii=False, indent=2),
                "options": {"raw": {"language": "json"}}
            }
        except json.JSONDecodeError:
            return {
                "mode": "raw",
                "raw": body_str,
                "options": {"raw": {"language": "json"}}
            }

    def _generate_test_script(self, tc: Dict) -> List[str]:
        """生成 Postman 测试脚本"""
        expected_status = tc.get('预期响应状态', 200)
        expected_response = tc.get('预期响应信息', '{}')

        script = [
            f"// 用例: {tc.get('用例标题', '')}",
            f"// 预期状态码: {expected_status}",
            "",
            f"pm.test('状态码为 {expected_status}', function () {{",
            f"    pm.response.to.have.status({expected_status});",
            "});",
            "",
            "pm.test('响应是 JSON 格式', function () {",
            "    pm.response.to.be.json;",
            "});",
        ]

        # 尝试解析预期响应，添加字段验证
        try:
            expected_obj = json.loads(expected_response)
            if isinstance(expected_obj, dict):
                for key in list(expected_obj.keys())[:3]:  # 最多验证3个字段
                    script.extend([
                        "",
                        f"pm.test('响应包含字段 {key}', function () {{",
                        "    var jsonData = pm.response.json();",
                        f"    pm.expect(jsonData).to.have.property('{key}');",
                        "});"
                    ])
        except:
            pass

        return script

    def _generate_id(self) -> str:
        """生成随机 ID"""
        import uuid
        return str(uuid.uuid4())

    def save(self, collection: Dict, filepath: str):
        """保存 Postman Collection 文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(collection, f, ensure_ascii=False, indent=2)
        return filepath


# 便捷函数
def format_postman(testcases: List[Dict], module_name: str, base_url: str = "") -> Dict:
    """格式化测试用例为 Postman Collection"""
    return PostmanFormatter(module_name, base_url).format(testcases)
